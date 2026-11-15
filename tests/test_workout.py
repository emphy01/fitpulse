"""
Unit and Integration Tests for Home Workout Backend.
Verifies all Usability features, UX principles, and state engine operations.
"""

import unittest
import shutil
import tempfile
from pathlib import Path

from homeworkout.models import (
    MuscleGroup, DifficultyLevel, SessionState, StepType, UserProfile
)
from homeworkout.service import WorkoutAppService
from homeworkout.engine import WorkoutEngine


class TestHomeWorkoutBackend(unittest.TestCase):

    def setUp(self):
        # Create isolated temporary directory for test storage
        self.test_dir = tempfile.mkdtemp()
        self.service = WorkoutAppService(storage_dir=self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_default_catalog_initialization(self):
        """Findable / Useful: Verify catalog and default routines load automatically."""
        exercises = self.service.list_exercises()
        routines = self.service.list_routines()

        self.assertGreaterEqual(len(exercises), 5)
        self.assertGreaterEqual(len(routines), 3)

        # Check 7-minute workout structure
        found_7min = [r for r in routines if "7-Minute" in r.title]
        self.assertTrue(len(found_7min) > 0)
        routine_7min = found_7min[0]
        self.assertGreater(routine_7min.total_duration_seconds, 0)
        self.assertGreater(routine_7min.exercise_count, 0)

    def test_search_and_filter_exercises(self):
        """Findable: Test keyword, target muscle, and difficulty filters."""
        # 1. Search by muscle group
        legs = self.service.search_exercises(target_muscle=MuscleGroup.LEGS)
        for ex in legs:
            self.assertEqual(ex.target_muscle, MuscleGroup.LEGS)
        self.assertTrue(len(legs) > 0)

        # 2. Search by keyword
        pushups = self.service.search_exercises(keyword="push")
        self.assertTrue(any("Push" in ex.name for ex in pushups))

        # 3. Search non-existent
        empty = self.service.search_exercises(keyword="nonexistent123xyz")
        self.assertEqual(len(empty), 0)

    def test_search_routines(self):
        """Findable: Test searching routines with multiple criteria."""
        core_routines = self.service.search_routines(target_muscle=MuscleGroup.ABS_CORE)
        self.assertTrue(any("Core" in r.title for r in core_routines))

        quick_routines = self.service.search_routines(max_duration_seconds=360)
        for r in quick_routines:
            self.assertLessEqual(r.total_duration_seconds, 360)

    def test_profile_update_and_validation(self):
        """Errors (Usability): Proper bounds checking and input validation."""
        # Valid update
        prof = self.service.update_profile(name="Budi", weight_kg=72.5, default_rest_seconds=20)
        self.assertEqual(prof.name, "Budi")
        self.assertEqual(prof.weight_kg, 72.5)
        self.assertEqual(prof.default_rest_seconds, 20)

        # Invalid weight (< 20 kg)
        with self.assertRaises(ValueError):
            self.service.update_profile(weight_kg=10)

        # Invalid empty name
        with self.assertRaises(ValueError):
            self.service.update_profile(name="   ")

    def test_workout_engine_lifecycle(self):
        """Usability & UX: Full execution cycle from start to completion."""
        routine = self.service.list_routines()[1]  # Core routine
        profile = self.service.get_profile()
        engine = WorkoutEngine(routine, profile)

        self.assertEqual(engine.state, SessionState.IDLE)
        engine.start()
        self.assertIn(engine.state, [SessionState.RUNNING, SessionState.RESTING])

        initial_exercise = engine.current_step.exercise.name

        # Test ticking
        snapshot_1 = engine.tick(delta_seconds=5)
        self.assertEqual(engine.total_elapsed_seconds, 5)
        self.assertGreater(engine.calories_burned, 0.0)

        # Test pause & resume
        self.assertTrue(engine.pause())
        self.assertEqual(engine.state, SessionState.PAUSED)

        # Ticking while paused should not advance time
        engine.tick(delta_seconds=5)
        self.assertEqual(engine.total_elapsed_seconds, 5)

        self.assertTrue(engine.resume())
        self.assertIn(engine.state, [SessionState.RUNNING, SessionState.RESTING])

        # Test skip step
        self.assertTrue(engine.skip_step())
        # Next step should be different
        self.assertEqual(engine.current_step_index, 1)

        # Test previous step
        self.assertTrue(engine.previous_step())
        self.assertEqual(engine.current_step_index, 0)
        self.assertEqual(engine.current_step.exercise.name, initial_exercise)

    def test_abort_requires_confirmation(self):
        """Errors (Usability): Accidental cancellation protection."""
        engine = self.service.quick_start()
        engine.tick(10)

        # Abort without confirmation must raise ValueError
        with self.assertRaises(ValueError):
            engine.abort(confirmed=False)

        # Abort with explicit confirmation succeeds
        log = engine.abort(confirmed=True)
        self.assertEqual(engine.state, SessionState.ABORTED)
        self.assertEqual(log.status, "ABORTED")

    def test_custom_routine_builder(self):
        """Valuable & Desirable: Creating a custom workout."""
        custom = self.service.create_custom_routine(
            title="My Evening Stretch & Burn",
            description="Short custom workout for evening routine",
            target_muscle=MuscleGroup.FULL_BODY,
            difficulty=DifficultyLevel.BEGINNER,
            exercise_ids_and_durations=[
                ("ex_jumping_jacks", 20),
                ("ex_plank", 30)
            ],
            rest_seconds=10
        )

        self.assertEqual(custom.title, "My Evening Stretch & Burn")
        self.assertEqual(custom.exercise_count, 2)
        # 2 exercises + 1 rest interval = 3 steps
        self.assertEqual(len(custom.steps), 3)
        self.assertEqual(custom.total_duration_seconds, 20 + 10 + 30)

        # Make sure it appears in searchable routines
        found = self.service.search_routines(keyword="Evening Stretch")
        self.assertEqual(len(found), 1)

    def test_workout_history_and_streak_calculation(self):
        """Credible & Valuable: Metrics and streak recording."""
        # Complete a workout
        engine = self.service.quick_start()

        # Simulate completion
        while engine.state not in (SessionState.COMPLETED, SessionState.ABORTED):
            engine.tick(delta_seconds=10)

        self.assertEqual(engine.state, SessionState.COMPLETED)

        # Check logs saved in storage
        logs = self.service.get_history()
        self.assertGreaterEqual(len(logs), 1)
        self.assertEqual(logs[-1].status, "COMPLETED")
        self.assertGreater(logs[-1].calories_burned, 0)

        # Check stats dashboard
        stats = self.service.get_user_dashboard_stats()
        self.assertGreaterEqual(stats["total_workouts"], 1)
        self.assertGreaterEqual(stats["current_streak_days"], 1)
        self.assertGreater(stats["total_calories"], 0)

    def test_difficulty_impact_on_templates(self):
        """Useful / Credible: Verifies difficulty impacts duration, rest, and quantity."""
        routines = self.service.list_routines()

        # Find beginner, intermediate, and advanced routines
        beg_routines = [r for r in routines if r.difficulty == DifficultyLevel.BEGINNER]
        int_routines = [r for r in routines if r.difficulty == DifficultyLevel.INTERMEDIATE]
        adv_routines = [r for r in routines if r.difficulty == DifficultyLevel.ADVANCED]

        self.assertGreaterEqual(len(beg_routines), 3)
        self.assertGreaterEqual(len(int_routines), 3)
        self.assertGreaterEqual(len(adv_routines), 3)

        # Check Beginner step work duration = 20s
        beg_work_steps = [s for s in beg_routines[0].steps if s.step_type == StepType.EXERCISE]
        self.assertEqual(beg_work_steps[0].duration_seconds, 20)

        # Check Intermediate step work duration = 30s
        int_work_steps = [s for s in int_routines[0].steps if s.step_type == StepType.EXERCISE]
        self.assertEqual(int_work_steps[0].duration_seconds, 30)

        # Check Advanced step work duration = 45s
        adv_work_steps = [s for s in adv_routines[0].steps if s.step_type == StepType.EXERCISE]
        self.assertEqual(adv_work_steps[0].duration_seconds, 45)

    def test_weekly_schedule_operations(self):
        """Valuable / Habit: Tests weekly schedule loading and modifications."""
        schedule = self.service.get_weekly_schedule()
        self.assertIn("Senin", schedule.days)
        self.assertIn("Minggu", schedule.days)

        # Update schedule for Rabu
        routines = self.service.list_routines()
        first_routine = routines[0]
        updated = self.service.update_daily_schedule(
            day="Rabu",
            is_rest_day=False,
            routine_id=first_routine.id,
            scheduled_time="06:45",
            reminder_enabled=True
        )

        rabu_sched = updated.days["Rabu"]
        self.assertFalse(rabu_sched.is_rest_day)
        self.assertEqual(rabu_sched.routine_id, first_routine.id)
        self.assertEqual(rabu_sched.scheduled_time, "06:45")

        # Today's schedule lookup
        today = self.service.get_today_schedule()
        self.assertIsNotNone(today.day)

        # Update schedule for Rabu as REST DAY (tests both day and day_name kwargs)
        updated_rest = self.service.update_daily_schedule(
            day_name="Rabu",
            is_rest_day=True
        )
        self.assertTrue(updated_rest.days["Rabu"].is_rest_day)
        self.assertIsNone(updated_rest.days["Rabu"].routine_id)

        # Confirm persistence on fresh service instance
        fresh_service = WorkoutAppService(storage_dir=self.test_dir)
        fresh_sched = fresh_service.get_weekly_schedule()
        self.assertTrue(fresh_sched.days["Rabu"].is_rest_day)

        # Verify weekly target consistency calculation adjusts dynamically
        consistency = fresh_service.storage.compute_weekly_consistency()
        expected_workout_days = len([d for d in fresh_sched.days.values() if not d.is_rest_day and d.routine_id])
        self.assertEqual(consistency["total_scheduled_week"], expected_workout_days)

        # Test bulk update
        all_days = {}
        for d in ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]:
            all_days[d] = {"is_rest_day": True, "routine_id": None}
        fresh_service.update_all_daily_schedules(all_days)
        all_rest_consistency = fresh_service.storage.compute_weekly_consistency()
        self.assertEqual(all_rest_consistency["total_scheduled_week"], 0)

    def test_template_cloning_and_editing(self):
        """Valuable / Flexibility: Verifies editing an existing template."""
        routines = self.service.list_routines()
        target_routine = routines[0]

        # Edit routine in place
        updated = self.service.create_custom_routine(
            title="Modified Template Title",
            description="Updated description",
            target_muscle=target_routine.target_muscle,
            difficulty=target_routine.difficulty,
            exercise_ids_and_durations=[
                ("ex_jumping_jacks", 40),
                ("ex_pushups", 35)
            ],
            rest_seconds=25,
            routine_id=target_routine.id
        )

        self.assertEqual(updated.id, target_routine.id)
        self.assertEqual(updated.title, "Modified Template Title")
        self.assertEqual(updated.exercise_count, 2)

        # Confirm persisted in storage
        fetched = self.service.get_routine_by_id(target_routine.id)
        self.assertEqual(fetched.title, "Modified Template Title")

    def test_session_feedback_and_adaptive_advice(self):
        """HCI Feedback: Verifies physical state feedback and adaptive advice."""
        # Complete a workout
        engine = self.service.quick_start()
        while engine.state not in (SessionState.COMPLETED, SessionState.ABORTED):
            engine.tick(delta_seconds=10)

        # Record TOO_HEAVY feedback
        rec = self.service.record_session_feedback("TOO_HEAVY")
        self.assertIn("Turunkan durasi", rec["advice"])

        # Check log updated
        logs = self.service.get_history()
        self.assertGreaterEqual(len(logs), 1)
        latest = logs[-1]
        self.assertIn("Terlalu Berat", latest.user_feedback)
        self.assertIsNotNone(latest.recommendation_given)

    def test_delete_routine(self):
        """Usability: Verify routine deletion."""
        routines_before = self.service.list_routines()
        self.assertGreaterEqual(len(routines_before), 2)
        target = routines_before[-1]

        success = self.service.delete_routine(target.id)
        self.assertTrue(success)

        routines_after = self.service.list_routines()
        self.assertEqual(len(routines_after), len(routines_before) - 1)
        self.assertIsNone(self.service.get_routine_by_id(target.id))

    def test_personal_best_streak_resets_and_computes(self):
        """Stats: Verify personal best streak calculation and reset."""
        # When no logs, streak and PB must be 0
        stats = self.service.get_user_dashboard_stats()
        self.assertEqual(stats["current_streak_days"], 0)
        self.assertEqual(stats["personal_best_streak"], 0)

        # After reset, must remain 0
        self.service.storage.reset_all_user_data()
        stats_after_reset = self.service.get_user_dashboard_stats()
        self.assertEqual(stats_after_reset["personal_best_streak"], 0)
        self.assertEqual(stats_after_reset["current_streak_days"], 0)


if __name__ == '__main__':
    unittest.main()
