"""
Workout Session Controller and State Machine.
Encapsulates real-time workout execution, step transitions, interval timing,
scientific calorie estimation (MET), audio cues, and error-tolerant controls.
"""

from typing import Optional, Callable, Dict, Any, List
from .models import WorkoutRoutine, WorkoutStep, SessionState, StepType, WorkoutLog, UserProfile


class WorkoutEngine:
    """
    State machine for executing a workout session.
    HCI Usability Highlights:
    - Usable & Predictable State Transitions
    - Error Prevention: confirmation token needed to abort active workout
    - Efficiency & Flexibility: Skip, Prev, and Dynamic Time Adjustment (+/- 10s)
    - Credible: ACSM Standard MET Calorie formula
    - Accessible: Audio cue callbacks for screen-readers or voice synthesis
    """

    def __init__(self, routine: WorkoutRoutine, user_profile: UserProfile):
        self.routine = routine
        self.user_profile = user_profile

        self.state: SessionState = SessionState.IDLE
        self.current_step_index: int = 0
        self.step_remaining_seconds: int = 0
        self.total_elapsed_seconds: int = 0
        self.calories_burned: float = 0.0
        self.completed_steps_count: int = 0

        # Event Callbacks (UI decouplers)
        self.on_tick_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self.on_step_change_callbacks: List[Callable[[WorkoutStep, int, int], None]] = []
        self.on_state_change_callbacks: List[Callable[[SessionState, SessionState], None]] = []
        self.on_audio_cue_callbacks: List[Callable[[str], None]] = []
        self.on_complete_callbacks: List[Callable[[WorkoutLog], None]] = []

        self._setup_initial_step()

    def _setup_initial_step(self):
        if self.routine.steps:
            self.step_remaining_seconds = self.routine.steps[0].duration_seconds
        else:
            self.step_remaining_seconds = 0

    @property
    def current_step(self) -> Optional[WorkoutStep]:
        if 0 <= self.current_step_index < len(self.routine.steps):
            return self.routine.steps[self.current_step_index]
        return None

    @property
    def next_step(self) -> Optional[WorkoutStep]:
        if 0 <= self.current_step_index + 1 < len(self.routine.steps):
            return self.routine.steps[self.current_step_index + 1]
        return None

    @property
    def progress_percentage(self) -> float:
        total = len(self.routine.steps)
        if total == 0:
            return 100.0
        return round((self.current_step_index / total) * 100, 1)

    def _set_state(self, new_state: SessionState):
        old_state = self.state
        if old_state != new_state:
            self.state = new_state
            for cb in self.on_state_change_callbacks:
                cb(old_state, new_state)

    # ---- Calorie Calculation (ACSM Scientific Formula) ----
    def _calculate_calories_for_duration(self, step: WorkoutStep, seconds: int) -> float:
        """
        Formula: Calories/min = (MET * 3.5 * weight_kg) / 200
        Calories = (Calories/min) * (seconds / 60)
        """
        if step.step_type == StepType.REST:
            met = 1.3  # Resting metabolic rate
        elif step.exercise:
            met = step.exercise.met_value
        else:
            met = 5.0

        calories_per_minute = (met * 3.5 * self.user_profile.weight_kg) / 200.0
        return calories_per_minute * (seconds / 60.0)

    # ---- Actions ----
    def start(self) -> bool:
        if self.state not in (SessionState.IDLE, SessionState.PAUSED):
            return False

        if not self.routine.steps:
            self._set_state(SessionState.COMPLETED)
            return False

        current = self.current_step
        new_state = SessionState.RESTING if (current and current.step_type == StepType.REST) else SessionState.RUNNING
        self._set_state(new_state)

        self._trigger_step_change()
        return True

    def pause(self) -> bool:
        if self.state in (SessionState.RUNNING, SessionState.RESTING):
            self._set_state(SessionState.PAUSED)
            return True
        return False

    def resume(self) -> bool:
        if self.state == SessionState.PAUSED:
            current = self.current_step
            new_state = SessionState.RESTING if (current and current.step_type == StepType.REST) else SessionState.RUNNING
            self._set_state(new_state)
            return True
        return False

    def tick(self, delta_seconds: int = 1) -> Dict[str, Any]:
        """
        Advances the workout timer by delta_seconds.
        Can be driven by a real time sleep loop or simulated during testing.
        """
        if self.state not in (SessionState.RUNNING, SessionState.RESTING):
            return self.get_snapshot()

        step = self.current_step
        if not step:
            self._finish_workout(SessionState.COMPLETED)
            return self.get_snapshot()

        # Update elapsed and calories
        self.total_elapsed_seconds += delta_seconds
        cals = self._calculate_calories_for_duration(step, delta_seconds)
        self.calories_burned += cals

        self.step_remaining_seconds -= delta_seconds

        # Trigger tick callbacks
        snapshot = self.get_snapshot()
        for cb in self.on_tick_callbacks:
            cb(snapshot)

        # Step finished?
        if self.step_remaining_seconds <= 0:
            self.completed_steps_count += 1
            self._advance_step()

        return self.get_snapshot()

    def _advance_step(self):
        self.current_step_index += 1
        if self.current_step_index >= len(self.routine.steps):
            self._finish_workout(SessionState.COMPLETED)
            return

        next_step = self.current_step
        if next_step:
            self.step_remaining_seconds = next_step.duration_seconds
            new_state = SessionState.RESTING if next_step.step_type == StepType.REST else SessionState.RUNNING
            self._set_state(new_state)
            self._trigger_step_change()

    def _trigger_step_change(self):
        curr = self.current_step
        if curr:
            for cb in self.on_step_change_callbacks:
                cb(curr, self.current_step_index + 1, len(self.routine.steps))

            # Trigger accessible voice/audio cue
            if self.user_profile.voice_cues_enabled and curr.exercise and curr.exercise.audio_cue:
                for cue_cb in self.on_audio_cue_callbacks:
                    cue_cb(curr.exercise.audio_cue)

    def skip_step(self) -> bool:
        """User can skip current exercise or rest if desired (Efficiency)."""
        if self.state in (SessionState.RUNNING, SessionState.RESTING, SessionState.PAUSED):
            self._advance_step()
            return True
        return False

    def previous_step(self) -> bool:
        """User can go back to redo a step (Usability / Error Recovery)."""
        if self.state in (SessionState.RUNNING, SessionState.RESTING, SessionState.PAUSED):
            if self.current_step_index > 0:
                self.current_step_index -= 1
                curr = self.current_step
                if curr:
                    self.step_remaining_seconds = curr.duration_seconds
                    new_state = SessionState.RESTING if curr.step_type == StepType.REST else SessionState.RUNNING
                    self._set_state(new_state)
                    self._trigger_step_change()
                    return True
        return False

    def adjust_time(self, delta_seconds: int) -> int:
        """Add or subtract time on the fly, e.g. +10s or -10s (Flexibility)."""
        if self.state in (SessionState.RUNNING, SessionState.RESTING, SessionState.PAUSED):
            new_time = max(1, self.step_remaining_seconds + delta_seconds)
            self.step_remaining_seconds = new_time
            return self.step_remaining_seconds
        return self.step_remaining_seconds

    def abort(self, confirmed: bool = False) -> Optional[WorkoutLog]:
        """
        Error Prevention: Will NOT abort unless explicit confirmation flag is True!
        """
        if not confirmed:
            raise ValueError("Workout cancellation requires explicit user confirmation to prevent accidental loss of progress.")

        return self._finish_workout(SessionState.ABORTED)

    def _finish_workout(self, final_state: SessionState) -> WorkoutLog:
        self._set_state(final_state)

        log = WorkoutLog(
            routine_id=self.routine.id,
            routine_title=self.routine.title,
            duration_spent_seconds=self.total_elapsed_seconds,
            total_routine_duration_seconds=self.routine.total_duration_seconds,
            calories_burned=round(self.calories_burned, 1),
            completed_steps_count=self.completed_steps_count,
            total_steps_count=len(self.routine.steps),
            status="COMPLETED" if final_state == SessionState.COMPLETED else "ABORTED"
        )

        for cb in self.on_complete_callbacks:
            cb(log)

        return log

    def get_snapshot(self) -> Dict[str, Any]:
        """Returns structured current state dictionary for any UI adapter."""
        curr = self.current_step
        nxt = self.next_step

        curr_ex = curr.exercise if curr else None
        nxt_ex = nxt.exercise if nxt else None

        target_reps = curr.target_reps if curr else None
        if target_reps is None and curr_ex and curr_ex.is_reps_based:
            target_reps = curr_ex.default_reps

        nxt_reps = nxt.target_reps if nxt else None
        if nxt_reps is None and nxt_ex and nxt_ex.is_reps_based:
            nxt_reps = nxt_ex.default_reps

        return {
            "state": self.state.value,
            "routine_title": self.routine.title,
            "step_index": self.current_step_index + 1,
            "total_steps": len(self.routine.steps),
            "step_type": curr.step_type.value if curr else None,
            "exercise_id": curr_ex.id if curr_ex else None,
            "exercise_name": curr_ex.name if curr_ex else ("Rest & Hydrate" if curr else "None"),
            "exercise_instruction": curr_ex.instructions if curr_ex else [],
            "accessible_description": curr_ex.accessible_description if curr_ex else "Take deep breaths and rest.",
            "audio_cue": curr_ex.audio_cue if curr_ex else "",
            "image_path": curr_ex.image_path if curr_ex else "",
            "icon_path": getattr(curr_ex, 'icon_path', f"workout_data/images/icons/icon_{curr_ex.id}.png") if curr_ex else "workout_data/images/icons/icon_rest.png",
            "focus_areas": curr_ex.focus_areas if curr_ex else [],
            "common_mistakes": curr_ex.common_mistakes if curr_ex else [],
            "breathing_tips": curr_ex.breathing_tips if curr_ex else [],
            "target_reps": target_reps,
            "is_reps_based": bool(target_reps is not None and curr and curr.step_type == StepType.EXERCISE),
            "step_remaining_seconds": self.step_remaining_seconds,
            "total_elapsed_seconds": self.total_elapsed_seconds,
            "calories_burned": round(self.calories_burned, 1),
            "progress_percentage": self.progress_percentage,
            "next_exercise_id": nxt_ex.id if nxt_ex else None,
            "next_exercise": nxt_ex.name if nxt_ex else (nxt.step_type.value if nxt else "Workout Complete"),
            "next_image_path": nxt_ex.image_path if nxt_ex else "",
            "next_icon_path": getattr(nxt_ex, 'icon_path', f"workout_data/images/icons/icon_{nxt_ex.id}.png") if nxt_ex else "",
            "next_target_reps": nxt_reps
        }
