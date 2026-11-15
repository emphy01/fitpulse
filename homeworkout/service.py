"""
Application Service Facade.
Orchestrates storage, active workout sessions, search/filter, and custom routine creation.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from .models import (
    WorkoutRoutine, WorkoutStep, Exercise, UserProfile,
    WorkoutLog, MuscleGroup, DifficultyLevel, StepType, SessionState,
    WeeklySchedule, DailySchedule, DayOfWeek
)
from .storage import StorageManager
from .engine import WorkoutEngine


class WorkoutAppService:
    """
    Central API/Service facade for the Home Workout backend.
    Enforces all 5 Usability and 7 UX principles:
    - Learnability & Memorability: Consistent API, persistent settings
    - Efficiency: Quick-start methods, fast lookups
    - Findability: Filter by muscle, difficulty, duration, and keyword search
    - Error Tolerance: Input validation with human-readable error messages
    - Credibility & Value: Metrics calculation, history logs, profile personalization
    """

    def __init__(self, storage_dir: Optional[str] = None):
        self.storage = StorageManager(storage_dir)
        self.current_engine: Optional[WorkoutEngine] = None

    # ---- Profile & Settings ----
    def get_profile(self, user_id: str = "default_user") -> UserProfile:
        return self.storage.load_profile(user_id=user_id)

    def update_profile(self, user_id: str = "default_user", **kwargs) -> UserProfile:
        profile = self.get_profile(user_id=user_id)

        # Validation (Error Prevention)
        if "weight_kg" in kwargs:
            val = float(kwargs["weight_kg"])
            if val <= 20 or val > 300:
                raise ValueError("Berat badan harus berada di antara 20 kg dan 300 kg.")
            profile.weight_kg = val

        if "height_cm" in kwargs:
            val = float(kwargs["height_cm"])
            if val <= 50 or val > 260:
                raise ValueError("Tinggi badan harus berada di antara 50 cm dan 260 cm.")
            profile.height_cm = val

        if "name" in kwargs:
            name = str(kwargs["name"]).strip()
            if not name:
                raise ValueError("Nama tidak boleh kosong.")
            profile.name = name

        if "fitness_level" in kwargs:
            profile.fitness_level = DifficultyLevel(kwargs["fitness_level"])

        if "default_rest_seconds" in kwargs:
            rest = int(kwargs["default_rest_seconds"])
            if rest < 5 or rest > 180:
                raise ValueError("Durasi istirahat harus antara 5 sampai 180 detik.")
            profile.default_rest_seconds = rest

        if "sound_enabled" in kwargs:
            profile.sound_enabled = bool(kwargs["sound_enabled"])

        if "high_contrast_mode" in kwargs:
            profile.high_contrast_mode = bool(kwargs["high_contrast_mode"])

        if "voice_cues_enabled" in kwargs:
            profile.voice_cues_enabled = bool(kwargs["voice_cues_enabled"])

        if "show_onboarding_guide" in kwargs:
            profile.show_onboarding_guide = bool(kwargs["show_onboarding_guide"])

        if "age" in kwargs:
            val = int(kwargs["age"])
            if val < 5 or val > 120:
                raise ValueError("Usia harus berada di antara 5 sampai 120 tahun.")
            profile.age = val

        if "gender" in kwargs:
            profile.gender = str(kwargs["gender"]).strip().lower()

        if "target_focus" in kwargs:
            profile.target_focus = str(kwargs["target_focus"]).strip()

        if "is_profile_completed" in kwargs:
            profile.is_profile_completed = bool(kwargs["is_profile_completed"])

        self.storage.save_profile(profile, user_id=user_id)
        return profile

    # ---- Exercises Library & Search (Findable) ----
    def list_exercises(self) -> List[Exercise]:
        return self.storage.load_exercises()

    def get_exercise_by_id(self, exercise_id: str) -> Optional[Exercise]:
        for ex in self.list_exercises():
            if ex.id == exercise_id:
                return ex
        return None

    def update_exercise_image(self, exercise_id: str, image_path: str) -> Optional[Exercise]:
        exercises = self.list_exercises()
        target = None
        for ex in exercises:
            if ex.id == exercise_id:
                ex.image_path = image_path
                target = ex
                break
        if target:
            self.storage.save_exercises(exercises)
            # Also sync any routine steps referencing this exercise
            routines = self.list_routines()
            modified = False
            for r in routines:
                for step in r.steps:
                    if step.exercise and step.exercise.id == exercise_id:
                        step.exercise.image_path = image_path
                        modified = True
            if modified:
                self.storage.save_routines(routines)
        return target

    def search_exercises(
        self,
        keyword: str = "",
        target_muscle: Optional[MuscleGroup] = None,
        difficulty: Optional[DifficultyLevel] = None
    ) -> List[Exercise]:
        exercises = self.list_exercises()
        results = []
        kw = keyword.lower().strip()

        for ex in exercises:
            if kw and (kw not in ex.name.lower() and kw not in ex.accessible_description.lower()):
                continue
            if target_muscle and ex.target_muscle != target_muscle:
                continue
            if difficulty and ex.difficulty != difficulty:
                continue
            results.append(ex)

        return results

    # ---- Routines Library & Search (Findable, Useful) ----
    def list_routines(self, user_id: str = "default_user") -> List[WorkoutRoutine]:
        return self.storage.load_routines(user_id=user_id)

    def get_routine_by_id(self, routine_id: str, user_id: str = "default_user") -> Optional[WorkoutRoutine]:
        for r in self.list_routines(user_id=user_id):
            if r.id == routine_id:
                return r
        return None

    def search_routines(
        self,
        keyword: str = "",
        target_muscle: Optional[MuscleGroup] = None,
        difficulty: Optional[DifficultyLevel] = None,
        max_duration_seconds: Optional[int] = None,
        user_id: str = "default_user"
    ) -> List[WorkoutRoutine]:
        routines = self.list_routines(user_id=user_id)
        results = []
        kw = keyword.lower().strip()

        for r in routines:
            if kw and (kw not in r.title.lower() and kw not in r.description.lower() and not any(kw in tag.lower() for tag in r.tags)):
                continue
            if target_muscle and r.target_muscle != target_muscle:
                continue
            if difficulty and r.difficulty != difficulty:
                continue
            if max_duration_seconds and r.total_duration_seconds > max_duration_seconds:
                continue
            results.append(r)

        return results

    # ---- Custom Routine Builder & Editor (Valuable, Desirable) ----
    def create_custom_routine(
        self,
        title: str,
        description: str,
        target_muscle: MuscleGroup,
        difficulty: DifficultyLevel,
        exercise_ids_and_durations: List[tuple[str, int]],
        rest_seconds: Optional[int] = None,
        routine_id: Optional[str] = None,
        user_id: str = "default_user"
    ) -> WorkoutRoutine:
        """
        Builds, saves, or updates a routine.
        If routine_id is supplied, it edits the existing routine; otherwise it creates a new one.
        """
        title = title.strip()
        if not title:
            raise ValueError("Judul workout tidak boleh kosong.")
        if not exercise_ids_and_durations:
            raise ValueError("Workout harus memiliki minimal 1 gerakan latihan.")

        ex_map = {ex.id: ex for ex in self.list_exercises()}
        profile = self.get_profile(user_id=user_id)
        rest_dur = rest_seconds if rest_seconds is not None else profile.default_rest_seconds

        steps: List[WorkoutStep] = []
        import uuid
        r_id = routine_id if routine_id else f"custom_{uuid.uuid4().hex[:6]}"

        for idx, (ex_id, work_sec) in enumerate(exercise_ids_and_durations):
            if ex_id not in ex_map:
                raise ValueError(f"Exercise ID '{ex_id}' tidak ditemukan dalam katalog.")
            if work_sec < 5 or work_sec > 300:
                raise ValueError(f"Durasi gerakan harus antara 5 hingga 300 detik. (Diberikan: {work_sec}s)")

            # Add Exercise Step
            steps.append(WorkoutStep(
                step_id=f"step_{idx+1}",
                step_type=StepType.EXERCISE,
                duration_seconds=work_sec,
                exercise=ex_map[ex_id]
            ))

            # Add Rest Step if not the final exercise
            if idx < len(exercise_ids_and_durations) - 1 and rest_dur > 0:
                steps.append(WorkoutStep(
                    step_id=f"step_{idx+1}_rest",
                    step_type=StepType.REST,
                    duration_seconds=rest_dur
                ))

        tags = ["Custom", target_muscle.value]
        # Preserve original tags if editing existing
        existing = self.get_routine_by_id(r_id, user_id=user_id)
        if existing and existing.tags:
            tags = list(set(existing.tags + tags))

        routine = WorkoutRoutine(
            id=r_id,
            title=title,
            description=description,
            target_muscle=target_muscle,
            difficulty=difficulty,
            tags=tags,
            steps=steps
        )

        self.storage.add_routine(routine, user_id=user_id)
        return routine

    def save_or_update_routine(self, routine: WorkoutRoutine, user_id: str = "default_user") -> WorkoutRoutine:
        self.storage.add_routine(routine, user_id=user_id)
        return routine

    def delete_routine(self, routine_id: str, user_id: str = "default_user") -> bool:
        """Deletes a routine from storage."""
        return self.storage.delete_routine(routine_id, user_id=user_id)

    def record_session_feedback(self, feedback_choice: str) -> Dict[str, str]:
        """
        Records user physical state feedback after workout and generates HCI adaptive advice.
        HCI: Feedback, Credibility, and Error Tolerance (helps users calibrate difficulty).
        """
        advice_map = {
            "TOO_HEAVY": {
                "title": "Terlalu Berat / Sangat Lelah",
                "advice": "💡 Saran Pelatih: Turunkan durasi setiap gerakan 5–10 detik atau tingkatkan durasi istirahat antar gerakan. Jangan memaksakan diri, konsistensi jangka panjang jauh lebih penting!",
                "suggestion_tag": "Turunkan durasi / tambah istirahat"
            },
            "SLIGHTLY_HEAVY": {
                "title": "Agak Berat tapi Mampu",
                "advice": "💡 Saran Pelatih: Ini adalah zona latihan yang ideal untuk memicu adaptasi dan pembentukan otot baru. Pertahankan ritme ini dalam 1–2 minggu ke depan!",
                "suggestion_tag": "Zona optimal tercapai"
            },
            "BALANCED": {
                "title": "Pas & Nyaman",
                "advice": "💡 Saran Pelatih: Kerja luar biasa! Kondisi fisik Anda seimbang dan bugar dengan beban ini. Pertahankan konsistensi latihan mingguan Anda.",
                "suggestion_tag": "Pertahankan konsistensi"
            },
            "TOO_LIGHT": {
                "title": "Terlalu Ringan / Kurang Berasa",
                "advice": "💡 Saran Pelatih: Tubuh Anda siap menerima stimulasi lebih tinggi! Coba tambah durasi gerakan (+10s), kurangi waktu istirahat, atau beralih ke template tingkat lanjutan.",
                "suggestion_tag": "Tingkatkan intensitas / coba level lanjutan"
            }
        }

        entry = advice_map.get(feedback_choice, {
            "title": feedback_choice,
            "advice": "💡 Tetap jaga konsistensi dan pantau terus kondisi fisik Anda setelah latihan.",
            "suggestion_tag": "Netral"
        })

        self.storage.update_latest_log_feedback(entry["title"], entry["advice"])
        return entry

    # ---- Workout Session Controller ----
    def quick_start(self) -> WorkoutEngine:
        """
        Efficiency feature: Immediately starts the most popular/default routine
        (Scientific 7-Minute Workout) without needing navigation steps.
        """
        routines = self.list_routines()
        if not routines:
            raise RuntimeError("Tidak ada routine workout yang tersedia.")
        return self.start_workout(routines[0].id)

    def start_workout(self, routine_id: str) -> WorkoutEngine:
        routine = self.get_routine_by_id(routine_id)
        if not routine:
            raise ValueError(f"Routine dengan ID '{routine_id}' tidak ditemukan.")

        profile = self.get_profile()
        self.current_engine = WorkoutEngine(routine, profile)

        # Hook session completion to save into storage automatically
        def on_workout_finished(log: WorkoutLog):
            self.storage.append_log(log)

        self.current_engine.on_complete_callbacks.append(on_workout_finished)
        self.current_engine.start()
        return self.current_engine

    def get_active_session(self) -> Optional[WorkoutEngine]:
        if self.current_engine and self.current_engine.state not in (SessionState.COMPLETED, SessionState.ABORTED):
            return self.current_engine
        return None

    # ---- Statistics & History (Credible, Valuable) ----
    def get_history(self, user_id: str = "default_user") -> List[WorkoutLog]:
        return self.storage.load_logs(user_id=user_id)

    def get_user_dashboard_stats(self, user_id: str = "default_user") -> Dict[str, Any]:
        stats = self.storage.compute_user_stats(user_id=user_id)
        profile = self.get_profile(user_id=user_id)
        stats["user_name"] = profile.name
        stats["weight_kg"] = profile.weight_kg
        stats["fitness_level"] = profile.fitness_level.value
        today_sched = self.get_today_schedule(user_id=user_id)
        stats["today_schedule"] = today_sched.to_dict()
        return stats

    # ---- Weekly Routine Schedule (Valuable, Habit Building) ----
    @staticmethod
    def get_today_day_name() -> str:
        """Returns today's day name in Indonesian (Senin .. Minggu)."""
        mapping = {
            0: DayOfWeek.SENIN.value,
            1: DayOfWeek.SELASA.value,
            2: DayOfWeek.RABU.value,
            3: DayOfWeek.KAMIS.value,
            4: DayOfWeek.JUMAT.value,
            5: DayOfWeek.SABTU.value,
            6: DayOfWeek.MINGGU.value
        }
        return mapping.get(datetime.now().weekday(), DayOfWeek.SENIN.value)

    def get_weekly_schedule(self, user_id: str = "default_user") -> WeeklySchedule:
        return self.storage.load_weekly_schedule(user_id=user_id)

    def get_today_schedule(self, user_id: str = "default_user") -> DailySchedule:
        schedule = self.get_weekly_schedule(user_id=user_id)
        today_name = self.get_today_day_name()
        if today_name in schedule.days:
            return schedule.days[today_name]
        return DailySchedule(day=today_name, is_rest_day=True)

    def update_daily_schedule(
        self,
        day: Optional[str] = None,
        is_rest_day: bool = False,
        routine_id: Optional[str] = None,
        scheduled_time: str = "07:00",
        reminder_enabled: bool = True,
        routine_title: Optional[str] = None,
        day_name: Optional[str] = None,
        user_id: str = "default_user",
        **kwargs
    ) -> WeeklySchedule:
        """
        Updates schedule for a specific day of the week.
        User can assign any existing preset or custom workout, or mark as rest day.
        Accepts either 'day' or 'day_name' for robustness.
        """
        target_day = day or day_name or kwargs.get("day_name") or kwargs.get("day")
        if not target_day:
            raise ValueError("Nama hari (day) wajib ditentukan.")

        schedule = self.get_weekly_schedule(user_id=user_id)

        title = routine_title
        if not is_rest_day and routine_id:
            routine = self.get_routine_by_id(routine_id, user_id=user_id)
            if not routine:
                raise ValueError(f"Workout routine dengan ID '{routine_id}' tidak ditemukan.")
            title = routine.title
        elif is_rest_day:
            routine_id = None
            title = "Hari Istirahat"

        # Validate time format "HH:MM"
        time_parts = (scheduled_time or "07:00").strip().split(":")
        if len(time_parts) != 2 or not all(p.isdigit() for p in time_parts):
            scheduled_time = "07:00"
        else:
            h, m = int(time_parts[0]), int(time_parts[1])
            if not (0 <= h <= 23 and 0 <= m <= 59):
                scheduled_time = "07:00"

        schedule.days[target_day] = DailySchedule(
            day=target_day,
            is_rest_day=is_rest_day,
            routine_id=routine_id if not is_rest_day else None,
            routine_title=title if not is_rest_day else None,
            scheduled_time=scheduled_time,
            reminder_enabled=reminder_enabled
        )

        self.storage.save_weekly_schedule(schedule, user_id=user_id)
        return schedule

    def update_all_daily_schedules(self, days_data: Dict[str, Dict[str, Any]], user_id: str = "default_user") -> WeeklySchedule:
        """Updates multiple or all days of the week atomically."""
        schedule = self.get_weekly_schedule(user_id=user_id)
        for d_name, d_cfg in days_data.items():
            is_rest = bool(d_cfg.get("is_rest_day", False))
            r_id = d_cfg.get("routine_id")
            title = None
            if not is_rest and r_id:
                routine = self.get_routine_by_id(r_id, user_id=user_id)
                if routine:
                    title = routine.title
            else:
                is_rest = True
                r_id = None

            sched_time = d_cfg.get("scheduled_time", "07:00")
            remind = d_cfg.get("reminder_enabled", True)

            schedule.days[d_name] = DailySchedule(
                day=d_name,
                is_rest_day=is_rest,
                routine_id=r_id,
                routine_title=title,
                scheduled_time=sched_time,
                reminder_enabled=remind
            )
        self.storage.save_weekly_schedule(schedule, user_id=user_id)
        return schedule

    # ---- Pending Workouts & Data Reset ----
    def get_pending_workouts(self, user_id: str = "default_user") -> List[Dict[str, Any]]:
        return self.storage.load_pending_workouts(user_id=user_id)

    def save_pending_workout(self, item: Dict[str, Any], user_id: str = "default_user") -> Dict[str, Any]:
        return self.storage.save_pending_workout(item, user_id=user_id)

    def remove_pending_workout(self, pending_id: str, user_id: str = "default_user") -> bool:
        return self.storage.remove_pending_workout(pending_id, user_id=user_id)

    def reset_user_data(self, user_id: str = "default_user") -> bool:
        return self.storage.reset_all_user_data(user_id=user_id)
