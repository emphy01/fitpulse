"""
Persistence Storage layer for FitPulse Home Workout application.
Supports:
1. TiDB Cloud Serverless / MySQL / PostgreSQL (via SQLAlchemy database models)
2. SQLite local database
3. Safe JSON fallback and initial data auto-migration
"""

import json
import os
import uuid
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from .models import (
    UserProfile, Exercise, WorkoutRoutine, WorkoutLog,
    DailySchedule, WeeklySchedule, DayOfWeek, DifficultyLevel
)
from .data import (
    DEFAULT_EXERCISES, build_default_routines, build_default_weekly_schedule
)
from .database import (
    init_db, SessionFactory, User, DBUserProfile, DBWorkoutLog,
    DBWeeklySchedule, DBPendingWorkout, DBCustomRoutine, DBWeightLog
)
from .auth import ensure_guest_or_default_user


class StorageManager:
    """
    Manages loading and saving application state.
    Integrates with TiDB Cloud / SQLite with multi-user isolation
    and automatic JSON backup/migration.
    """

    def __init__(self, storage_dir: Optional[str] = None):
        is_custom_dir = (storage_dir is not None)
        if storage_dir is None:
            self.storage_dir = Path(__file__).resolve().parent.parent / "workout_data"
        else:
            self.storage_dir = Path(storage_dir)

        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.profile_file = self.storage_dir / "user_profile.json"
        self.exercises_file = self.storage_dir / "exercises.json"
        self.routines_file = self.storage_dir / "routines.json"
        self.logs_file = self.storage_dir / "workout_logs.json"
        self.schedule_file = self.storage_dir / "weekly_schedule.json"
        self.pending_file = self.storage_dir / "pending_workouts.json"

        # If a custom test directory was provided, create an isolated database engine
        if is_custom_dir:
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            from .database import Base
            test_db_url = f"sqlite:///{(self.storage_dir / 'fitpulse.db').as_posix()}"
            self.engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
            Base.metadata.create_all(bind=self.engine)
            self.session_factory = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)
        else:
            from .database import engine, SessionFactory, init_db
            self.engine = engine
            self.session_factory = SessionFactory
            try:
                init_db()
                session = self.session_factory()
                ensure_guest_or_default_user(session)
                session.close()
                self._migrate_json_to_db_if_needed()
            except Exception as e:
                print(f"⚠️ Database initialization warning: {e}. Using JSON storage fallback.")

        # Initialize JSON defaults as safety fallback
        self._initialize_json_defaults()

    def _get_session(self):
        """Returns a new database session."""
        return self.session_factory()

    # ---- JSON Fallback Helpers ----
    def _safe_read_json(self, file_path: Path, fallback_data: Any) -> Any:
        if not file_path.exists():
            return fallback_data
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return fallback_data

    def _safe_write_json(self, file_path: Path, data: Any) -> bool:
        try:
            temp_path = file_path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            if file_path.exists():
                file_path.unlink()
            temp_path.rename(file_path)
            return True
        except IOError:
            return False

    def _initialize_json_defaults(self):
        # 1. Profile
        if not self.profile_file.exists():
            self._safe_write_json(self.profile_file, UserProfile().to_dict())

        # 2. Exercises
        existing_exercises = self.load_exercises()
        existing_ids = {e.id for e in existing_exercises}
        needs_exercise_update = False
        for default_e in DEFAULT_EXERCISES:
            if default_e.id not in existing_ids:
                existing_exercises.append(default_e)
                needs_exercise_update = True
        if needs_exercise_update or not self.exercises_file.exists():
            self.save_exercises(existing_exercises)

        # 3. Routines
        existing_routines = self.load_routines()
        existing_r_ids = {r.id for r in existing_routines}
        default_routines = build_default_routines(self.load_exercises())
        needs_routine_update = False
        for default_r in default_routines:
            if default_r.id not in existing_r_ids:
                existing_routines.append(default_r)
                needs_routine_update = True
        if needs_routine_update or not self.routines_file.exists():
            self.save_routines(existing_routines)

        # 4. Logs
        if not self.logs_file.exists():
            self._safe_write_json(self.logs_file, [])

        # 5. Weekly Schedule
        if not self.schedule_file.exists():
            default_schedule = build_default_weekly_schedule(self.load_routines())
            self._safe_write_json(self.schedule_file, default_schedule.to_dict())

    def _migrate_json_to_db_if_needed(self):
        """Migrates local JSON file data to default_user in database if DB is newly initialized."""
        session = self._get_session()
        try:
            # Check if default_user has logs
            db_log_count = session.query(DBWorkoutLog).filter(DBWorkoutLog.user_id == "default_user").count()
            if db_log_count == 0 and self.logs_file.exists():
                json_logs = self._safe_read_json(self.logs_file, [])
                for item in json_logs:
                    log = DBWorkoutLog(
                        log_id=item.get("log_id") or str(uuid.uuid4())[:8],
                        user_id="default_user",
                        routine_id=item.get("routine_id", ""),
                        routine_title=item.get("routine_title", ""),
                        timestamp=item.get("timestamp", datetime.now().isoformat()),
                        duration_spent_seconds=item.get("duration_spent_seconds", 0),
                        total_routine_duration_seconds=item.get("total_routine_duration_seconds", 0),
                        calories_burned=item.get("calories_burned", 0.0),
                        completed_steps_count=item.get("completed_steps_count", 0),
                        total_steps_count=item.get("total_steps_count", 0),
                        status=item.get("status", "COMPLETED"),
                        user_feedback=item.get("user_feedback"),
                        recommendation_given=item.get("recommendation_given")
                    )
                    session.add(log)
                session.commit()

            # Check profile sync
            if self.profile_file.exists():
                prof_data = self._safe_read_json(self.profile_file, {})
                if prof_data:
                    db_prof = session.query(DBUserProfile).filter(DBUserProfile.user_id == "default_user").first()
                    if db_prof:
                        db_prof.name = prof_data.get("name", db_prof.name)
                        db_prof.weight_kg = float(prof_data.get("weight_kg", db_prof.weight_kg))
                        db_prof.height_cm = float(prof_data.get("height_cm", db_prof.height_cm))
                        db_prof.fitness_level = prof_data.get("fitness_level", db_prof.fitness_level)
                        db_prof.default_rest_seconds = int(prof_data.get("default_rest_seconds", db_prof.default_rest_seconds))
                        db_prof.sound_enabled = bool(prof_data.get("sound_enabled", db_prof.sound_enabled))
                        db_prof.voice_cues_enabled = bool(prof_data.get("voice_cues_enabled", db_prof.voice_cues_enabled))
                        db_prof.high_contrast_mode = bool(prof_data.get("high_contrast_mode", db_prof.high_contrast_mode))
                        db_prof.show_onboarding_guide = bool(prof_data.get("show_onboarding_guide", db_prof.show_onboarding_guide))
                        session.commit()
        except Exception as e:
            session.rollback()
            print(f"Note on initial migration: {e}")
        finally:
            session.close()

    # =========================================================================
    # USER PROFILE
    # =========================================================================
    def load_profile(self, user_id: str = "default_user") -> UserProfile:
        session = self._get_session()
        try:
            db_p = session.query(DBUserProfile).filter(DBUserProfile.user_id == user_id).first()
            if db_p:
                return UserProfile(
                    user_id=db_p.user_id,
                    name=db_p.name,
                    weight_kg=db_p.weight_kg,
                    height_cm=db_p.height_cm,
                    fitness_level=DifficultyLevel(db_p.fitness_level),
                    default_rest_seconds=db_p.default_rest_seconds,
                    sound_enabled=db_p.sound_enabled,
                    high_contrast_mode=db_p.high_contrast_mode,
                    voice_cues_enabled=db_p.voice_cues_enabled,
                    show_onboarding_guide=db_p.show_onboarding_guide
                )
        except Exception:
            pass
        finally:
            session.close()

        # Fallback to local JSON
        data = self._safe_read_json(self.profile_file, None)
        if data and isinstance(data, dict):
            return UserProfile.from_dict(data)
        return UserProfile()

    def save_profile(self, profile: UserProfile, user_id: str = "default_user") -> bool:
        # Save to DB
        session = self._get_session()
        db_success = False
        try:
            db_p = session.query(DBUserProfile).filter(DBUserProfile.user_id == user_id).first()
            if not db_p:
                db_p = DBUserProfile(user_id=user_id)
                session.add(db_p)
            db_p.name = profile.name
            db_p.weight_kg = profile.weight_kg
            db_p.height_cm = profile.height_cm
            db_p.fitness_level = profile.fitness_level.value if hasattr(profile.fitness_level, 'value') else str(profile.fitness_level)
            db_p.default_rest_seconds = profile.default_rest_seconds
            db_p.sound_enabled = profile.sound_enabled
            db_p.voice_cues_enabled = profile.voice_cues_enabled
            db_p.high_contrast_mode = profile.high_contrast_mode
            db_p.show_onboarding_guide = profile.show_onboarding_guide
            session.commit()
            db_success = True
        except Exception as e:
            session.rollback()
        finally:
            session.close()

        # Always save JSON for default_user backup
        if user_id == "default_user":
            self._safe_write_json(self.profile_file, profile.to_dict())

        return db_success or True

    # =========================================================================
    # EXERCISES LIBRARY
    # =========================================================================
    def load_exercises(self) -> List[Exercise]:
        data = self._safe_read_json(self.exercises_file, [])
        if not data:
            return DEFAULT_EXERCISES
        try:
            return [Exercise.from_dict(item) for item in data]
        except Exception:
            return DEFAULT_EXERCISES

    def save_exercises(self, exercises: List[Exercise]) -> bool:
        data = [ex.to_dict() for ex in exercises]
        return self._safe_write_json(self.exercises_file, data)

    def add_exercise(self, exercise: Exercise) -> bool:
        exercises = self.load_exercises()
        exercises = [e for e in exercises if e.id != exercise.id]
        exercises.append(exercise)
        return self.save_exercises(exercises)

    # =========================================================================
    # ROUTINES & TEMPLATES (Catalog + User Custom Routines)
    # =========================================================================
    def load_routines(self, user_id: str = "default_user") -> List[WorkoutRoutine]:
        # 1. Base Catalog routines
        catalog_data = self._safe_read_json(self.routines_file, [])
        if not catalog_data:
            base_routines = build_default_routines(self.load_exercises())
        else:
            try:
                base_routines = [WorkoutRoutine.from_dict(item) for item in catalog_data]
            except Exception:
                base_routines = build_default_routines(self.load_exercises())

        # 2. Merge with user's custom routines from DB
        session = self._get_session()
        try:
            custom_items = session.query(DBCustomRoutine).filter(
                (DBCustomRoutine.user_id == user_id) | (DBCustomRoutine.user_id.is_(None))
            ).all()
            existing_ids = {r.id for r in base_routines}
            for ci in custom_items:
                if ci.id not in existing_ids:
                    steps_data = json.loads(ci.steps_json) if ci.steps_json else []
                    tags_data = json.loads(ci.tags_json) if ci.tags_json else []
                    routine = WorkoutRoutine(
                        id=ci.id,
                        title=ci.title,
                        description=ci.description or "",
                        target_muscle=ci.target_muscle or "Full Body",
                        difficulty=DifficultyLevel(ci.difficulty) if ci.difficulty in [d.value for d in DifficultyLevel] else DifficultyLevel.BEGINNER,
                        tags=tags_data,
                        cover_image=ci.cover_image or "workout_data/images/covers/cover_default_custom.png",
                        steps=[WorkoutStep.from_dict(s) for s in steps_data]
                    )
                    base_routines.append(routine)
        except Exception:
            pass
        finally:
            session.close()

        return base_routines

    def save_routines(self, routines: List[WorkoutRoutine], user_id: str = "default_user") -> bool:
        data = [r.to_dict() for r in routines]
        return self._safe_write_json(self.routines_file, data)

    def add_routine(self, routine: WorkoutRoutine, user_id: str = "default_user") -> bool:
        # Save to DB as custom routine
        session = self._get_session()
        try:
            existing = session.query(DBCustomRoutine).filter(DBCustomRoutine.id == routine.id).first()
            if not existing:
                existing = DBCustomRoutine(id=routine.id, user_id=user_id)
                session.add(existing)
            existing.title = routine.title
            existing.description = routine.description
            existing.target_muscle = routine.target_muscle
            existing.difficulty = routine.difficulty.value if hasattr(routine.difficulty, 'value') else str(routine.difficulty)
            existing.tags_json = json.dumps(routine.tags)
            existing.steps_json = json.dumps([s.to_dict() for s in routine.steps])
            existing.cover_image = routine.cover_image
            session.commit()
        except Exception as e:
            session.rollback()
        finally:
            session.close()

        # Also update JSON file
        routines = self.load_routines(user_id=user_id)
        routines = [r for r in routines if r.id != routine.id]
        routines.append(routine)
        return self.save_routines(routines, user_id=user_id)

    def delete_routine(self, routine_id: str, user_id: str = "default_user") -> bool:
        session = self._get_session()
        db_deleted = False
        try:
            cr = session.query(DBCustomRoutine).filter(
                DBCustomRoutine.id == routine_id,
                DBCustomRoutine.user_id == user_id
            ).first()
            if cr:
                session.delete(cr)
                session.commit()
                db_deleted = True
        except Exception:
            session.rollback()
        finally:
            session.close()

        # Also remove from JSON if present
        routines = self.load_routines(user_id=user_id)
        initial_len = len(routines)
        routines = [r for r in routines if r.id != routine_id]
        if len(routines) < initial_len:
            self.save_routines(routines, user_id=user_id)
            return True
        return db_deleted

    # =========================================================================
    # WEEKLY SCHEDULE
    # =========================================================================
    def load_weekly_schedule(self, user_id: str = "default_user") -> WeeklySchedule:
        session = self._get_session()
        try:
            db_scheds = session.query(DBWeeklySchedule).filter(DBWeeklySchedule.user_id == user_id).all()
            if db_scheds and len(db_scheds) >= 7:
                days_dict = {}
                for s in db_scheds:
                    days_dict[s.day_name] = DailySchedule(
                        day=DayOfWeek(s.day_name),
                        routine_id=s.routine_id,
                        is_rest_day=s.is_rest_day,
                        scheduled_time=s.scheduled_time or "07:00",
                        reminder_enabled=s.reminder_enabled
                    )
                return WeeklySchedule(days=days_dict)
        except Exception:
            pass
        finally:
            session.close()

        # Fallback to local JSON
        data = self._safe_read_json(self.schedule_file, None)
        if data and isinstance(data, dict):
            return WeeklySchedule.from_dict(data)
        return build_default_weekly_schedule(self.load_routines(user_id))

    def save_weekly_schedule(self, schedule: WeeklySchedule, user_id: str = "default_user") -> bool:
        session = self._get_session()
        try:
            for day_name, daily in schedule.days.items():
                s = session.query(DBWeeklySchedule).filter(
                    DBWeeklySchedule.user_id == user_id,
                    DBWeeklySchedule.day_name == day_name
                ).first()
                if not s:
                    s = DBWeeklySchedule(id=str(uuid.uuid4()), user_id=user_id, day_name=day_name)
                    session.add(s)
                s.routine_id = daily.routine_id
                s.is_rest_day = daily.is_rest_day
                s.scheduled_time = daily.scheduled_time
                s.reminder_enabled = daily.reminder_enabled
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()

        if user_id == "default_user":
            self._safe_write_json(self.schedule_file, schedule.to_dict())
        return True

    # =========================================================================
    # WORKOUT LOGS & STATS
    # =========================================================================
    def load_logs(self, user_id: str = "default_user") -> List[WorkoutLog]:
        session = self._get_session()
        try:
            db_logs = session.query(DBWorkoutLog).filter(
                DBWorkoutLog.user_id == user_id
            ).order_by(DBWorkoutLog.timestamp.asc()).all()
            if db_logs:
                return [WorkoutLog(
                    log_id=l.log_id,
                    routine_id=l.routine_id,
                    routine_title=l.routine_title,
                    timestamp=l.timestamp,
                    duration_spent_seconds=l.duration_spent_seconds,
                    total_routine_duration_seconds=l.total_routine_duration_seconds,
                    calories_burned=l.calories_burned,
                    completed_steps_count=l.completed_steps_count,
                    total_steps_count=l.total_steps_count,
                    status=l.status,
                    user_feedback=l.user_feedback,
                    recommendation_given=l.recommendation_given
                ) for l in db_logs]
        except Exception:
            pass
        finally:
            session.close()

        # Fallback to local JSON
        if user_id == "default_user":
            data = self._safe_read_json(self.logs_file, [])
            if isinstance(data, list):
                return [WorkoutLog.from_dict(item) for item in data]
        return []

    def append_log(self, log: WorkoutLog, user_id: str = "default_user") -> bool:
        session = self._get_session()
        try:
            db_log = DBWorkoutLog(
                log_id=log.log_id,
                user_id=user_id,
                routine_id=log.routine_id,
                routine_title=log.routine_title,
                timestamp=log.timestamp,
                duration_spent_seconds=log.duration_spent_seconds,
                total_routine_duration_seconds=log.total_routine_duration_seconds,
                calories_burned=log.calories_burned,
                completed_steps_count=log.completed_steps_count,
                total_steps_count=log.total_steps_count,
                status=log.status,
                user_feedback=log.user_feedback,
                recommendation_given=log.recommendation_given
            )
            session.add(db_log)
            session.commit()
        except Exception as e:
            session.rollback()
        finally:
            session.close()

        if user_id == "default_user":
            logs_data = self._safe_read_json(self.logs_file, [])
            logs_data.append(log.to_dict())
            self._safe_write_json(self.logs_file, logs_data)

        return True

    def save_logs(self, logs: List[WorkoutLog], user_id: str = "default_user") -> bool:
        session = self._get_session()
        try:
            session.query(DBWorkoutLog).filter(DBWorkoutLog.user_id == user_id).delete()
            for log in logs:
                db_log = DBWorkoutLog(
                    log_id=log.log_id,
                    user_id=user_id,
                    routine_id=log.routine_id,
                    routine_title=log.routine_title,
                    timestamp=log.timestamp,
                    duration_spent_seconds=log.duration_spent_seconds,
                    total_routine_duration_seconds=log.total_routine_duration_seconds,
                    calories_burned=log.calories_burned,
                    completed_steps_count=log.completed_steps_count,
                    total_steps_count=log.total_steps_count,
                    status=log.status,
                    user_feedback=log.user_feedback,
                    recommendation_given=log.recommendation_given
                )
                session.add(db_log)
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()

        if user_id == "default_user":
            data = [l.to_dict() for l in logs]
            self._safe_write_json(self.logs_file, data)
        return True

    def update_latest_log_feedback(self, feedback: str, recommendation: str, user_id: str = "default_user") -> bool:
        session = self._get_session()
        try:
            latest = session.query(DBWorkoutLog).filter(
                DBWorkoutLog.user_id == user_id
            ).order_by(DBWorkoutLog.timestamp.desc()).first()
            if latest:
                latest.user_feedback = feedback
                latest.recommendation_given = recommendation
                session.commit()
                return True
        except Exception:
            session.rollback()
        finally:
            session.close()

        if user_id == "default_user":
            logs_data = self._safe_read_json(self.logs_file, [])
            if logs_data and isinstance(logs_data, list):
                logs_data[-1]["user_feedback"] = feedback
                logs_data[-1]["recommendation_given"] = recommendation
                return self._safe_write_json(self.logs_file, logs_data)
        return False

    def compute_user_stats(self, user_id: str = "default_user") -> Dict[str, Any]:
        logs = self.load_logs(user_id=user_id)
        completed = [l for l in logs if l.status == "COMPLETED"]

        total_workouts = len(completed)
        total_seconds = sum(l.duration_spent_seconds for l in completed)
        total_calories = sum(l.calories_burned for l in completed)

        unique_dates = set()
        for l in completed:
            try:
                dt = datetime.fromisoformat(l.timestamp).date()
                unique_dates.add(dt)
            except Exception:
                continue

        streak = 0
        today = datetime.now().date()
        check_date = today

        if check_date not in unique_dates:
            check_date = today - timedelta(days=1)

        while check_date in unique_dates:
            streak += 1
            check_date -= timedelta(days=1)

        # Calculate all-time personal best consecutive streak
        personal_best = 0
        if unique_dates:
            sorted_dates = sorted(unique_dates)
            cur_run = 0
            prev_d = None
            for d in sorted_dates:
                if prev_d and (d - prev_d).days == 1:
                    cur_run += 1
                else:
                    cur_run = 1
                prev_d = d
                if cur_run > personal_best:
                    personal_best = cur_run

        personal_best = max(personal_best, streak)

        return {
            "total_workouts": total_workouts,
            "total_minutes": round(total_seconds / 60.0, 1),
            "total_calories": round(total_calories, 1),
            "current_streak_days": streak,
            "personal_best_streak": personal_best,
            "logs_count": len(logs)
        }

    # =========================================================================
    # PENDING WORKOUTS
    # =========================================================================
    def load_pending_workouts(self, user_id: str = "default_user") -> List[Dict[str, Any]]:
        session = self._get_session()
        try:
            db_pendings = session.query(DBPendingWorkout).filter(
                DBPendingWorkout.user_id == user_id
            ).order_by(DBPendingWorkout.timestamp.desc()).all()
            if db_pendings:
                return [p.to_dict() for p in db_pendings]
        except Exception:
            pass
        finally:
            session.close()

        if user_id == "default_user":
            data = self._safe_read_json(self.pending_file, [])
            return data if isinstance(data, list) else []
        return []

    def save_pending_workout(self, item: Dict[str, Any], user_id: str = "default_user") -> Dict[str, Any]:
        pending_id = item.get("pending_id") or str(uuid.uuid4())[:8]
        item["pending_id"] = pending_id
        if "timestamp" not in item:
            item["timestamp"] = datetime.now().isoformat()

        session = self._get_session()
        try:
            # Remove any pending workout with same pending_id or routine_id for this user
            session.query(DBPendingWorkout).filter(
                DBPendingWorkout.user_id == user_id,
                (DBPendingWorkout.pending_id == pending_id) | (DBPendingWorkout.routine_id == item.get("routine_id"))
            ).delete()
            db_p = DBPendingWorkout(
                pending_id=pending_id,
                user_id=user_id,
                routine_id=item.get("routine_id", ""),
                routine_title=item.get("routine_title", ""),
                current_step_index=item.get("current_step_index", 0),
                total_steps_count=item.get("total_steps_count", 0),
                duration_spent_seconds=item.get("duration_spent_seconds", 0),
                calories_burned=item.get("calories_burned", 0.0),
                timestamp=item["timestamp"]
            )
            session.add(db_p)
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()

        if user_id == "default_user":
            pendings = self._safe_read_json(self.pending_file, [])
            pendings = [p for p in pendings if p.get("pending_id") != pending_id and p.get("routine_id") != item.get("routine_id")]
            pendings.insert(0, item)
            self._safe_write_json(self.pending_file, pendings)

        return item

    def remove_pending_workout(self, pending_id: str, user_id: str = "default_user") -> bool:
        session = self._get_session()
        db_deleted = False
        try:
            res = session.query(DBPendingWorkout).filter(
                DBPendingWorkout.user_id == user_id,
                DBPendingWorkout.pending_id == pending_id
            ).delete()
            session.commit()
            db_deleted = (res > 0)
        except Exception:
            session.rollback()
        finally:
            session.close()

        if user_id == "default_user":
            pendings = self._safe_read_json(self.pending_file, [])
            initial_len = len(pendings)
            pendings = [p for p in pendings if p.get("pending_id") != pending_id]
            self._safe_write_json(self.pending_file, pendings)
            return (len(pendings) < initial_len) or db_deleted

        return db_deleted

    # =========================================================================
    # RESET ALL USER DATA
    # =========================================================================
    def reset_all_user_data(self, user_id: str = "default_user") -> bool:
        session = self._get_session()
        try:
            # Delete logs & pendings
            session.query(DBWorkoutLog).filter(DBWorkoutLog.user_id == user_id).delete()
            session.query(DBPendingWorkout).filter(DBPendingWorkout.user_id == user_id).delete()
            # Reset profile to defaults
            p = session.query(DBUserProfile).filter(DBUserProfile.user_id == user_id).first()
            if p:
                p.name = "Athlete"
                p.weight_kg = 65.0
                p.height_cm = 170.0
                p.fitness_level = "Beginner"
                p.default_rest_seconds = 15
                p.sound_enabled = True
                p.voice_cues_enabled = True
                p.high_contrast_mode = False
                p.show_onboarding_guide = True
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()

        if user_id == "default_user":
            default_profile = UserProfile()
            self._safe_write_json(self.profile_file, default_profile.to_dict())
            self._safe_write_json(self.logs_file, [])
            self._safe_write_json(self.pending_file, [])
            default_sched = build_default_weekly_schedule(self.load_routines(user_id))
            self.save_weekly_schedule(default_sched, user_id=user_id)

        return True

    # =========================================================================
    # WEEKLY SCHEDULE CONSISTENCY
    # =========================================================================
    def compute_weekly_consistency(self, user_id: str = "default_user") -> Dict[str, Any]:
        schedule = self.load_weekly_schedule(user_id=user_id)
        logs = self.load_logs(user_id=user_id)

        day_names = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
        now = datetime.now()
        today_idx = now.weekday()  # 0 is Senin, 6 is Minggu

        elapsed_days = day_names[:today_idx + 1]

        scheduled_up_to_today = [
            d for d in elapsed_days
            if d in schedule.days and not schedule.days[d].is_rest_day and schedule.days[d].routine_id
        ]

        total_scheduled_week = [
            d for d in day_names
            if d in schedule.days and not schedule.days[d].is_rest_day and schedule.days[d].routine_id
        ]

        monday_start = now - timedelta(days=today_idx, hours=now.hour, minutes=now.minute, seconds=now.second, microseconds=now.microsecond)

        completed_dates = set()
        completed_day_names = set()
        for lg in logs:
            if lg.status == "COMPLETED":
                try:
                    lg_dt = datetime.fromisoformat(lg.timestamp)
                    if lg_dt >= monday_start:
                        completed_dates.add(lg_dt.date())
                        completed_day_names.add(day_names[lg_dt.weekday()])
                except Exception:
                    continue

        sched_count = len(scheduled_up_to_today)
        completed_count = len(completed_dates)

        if sched_count == 0:
            consistency_pct = 100.0
            missed_count = 0
        else:
            effective_completed = min(completed_count, sched_count)
            consistency_pct = round((effective_completed / sched_count) * 100.0, 1)
            missed_count = max(0, sched_count - completed_count)

        return {
            "percentage": consistency_pct,
            "scheduled_up_to_today": sched_count,
            "completed_this_week": completed_count,
            "missed_count": missed_count,
            "total_scheduled_week": len(total_scheduled_week),
            "scheduled_days": total_scheduled_week,
            "rest_days": [d for d in day_names if d not in total_scheduled_week],
            "completed_day_names": list(completed_day_names)
        }
