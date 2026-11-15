"""
Domain models for Home Workout application.
Designed with HCI usability and UX principles:
- Clear types, sensible defaults, accessibility fields, and metadata.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid


class MuscleGroup(str, Enum):
    FULL_BODY = "Full Body"
    CHEST = "Chest"
    ABS_CORE = "Abs & Core"
    ARMS = "Arms"
    LEGS = "Legs"
    BACK = "Back"


class DifficultyLevel(str, Enum):
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"


class StepType(str, Enum):
    WARMUP = "Warm-up"
    EXERCISE = "Exercise"
    REST = "Rest"
    COOLDOWN = "Cool-down"


class SessionState(str, Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    RESTING = "RESTING"
    COMPLETED = "COMPLETED"
    ABORTED = "ABORTED"


@dataclass
class Exercise:
    """
    Represents an exercise in the workout library.
    UX: Accessible description, audio cue text, clear instruction, MET value for credible calorie calculations.
    Home Workout Features:
    - 1:1 image area support (image_path)
    - Specific targeted muscle regions (focus_areas)
    - Common mistakes with detailed explanations (common_mistakes)
    - Form and breathing tips (breathing_tips)
    - Rep-based vs time-based support (is_reps_based, default_reps)
    """
    id: str
    name: str
    target_muscle: MuscleGroup
    difficulty: DifficultyLevel
    instructions: List[str]
    accessible_description: str  # For accessibility (TTS/screen readers/visual guidance)
    met_value: float = 6.0       # Metabolic Equivalent of Task for credible calorie calculation
    equipment_needed: str = "None (Bodyweight)"
    audio_cue: str = ""          # Speech cue trigger (e.g. "Keep your back straight")
    image_path: str = ""         # Path to 1:1 image file
    icon_path: str = ""          # Path to exercise icon file
    focus_areas: List[str] = field(default_factory=list) # e.g. ["Quadriceps", "Glutes", "Hamstrings", "Calves"]
    common_mistakes: List[Dict[str, str]] = field(default_factory=list) # e.g. [{"title": "...", "desc": "..."}]
    breathing_tips: List[str] = field(default_factory=list)
    is_reps_based: bool = False
    default_reps: int = 12

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['target_muscle'] = self.target_muscle.value
        data['difficulty'] = self.difficulty.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Exercise':
        ex_id = data['id']
        img_p = data.get('image_path')
        if not img_p:
            img_p = f"workout_data/images/{ex_id}.png"
        icon_p = data.get('icon_path')
        if not icon_p:
            icon_p = f"workout_data/images/icons/icon_{ex_id}.png"

        return cls(
            id=ex_id,
            name=data['name'],
            target_muscle=MuscleGroup(data['target_muscle']),
            difficulty=DifficultyLevel(data['difficulty']),
            instructions=data.get('instructions', []),
            accessible_description=data.get('accessible_description', ''),
            met_value=float(data.get('met_value', 6.0)),
            equipment_needed=data.get('equipment_needed', 'None (Bodyweight)'),
            audio_cue=data.get('audio_cue', ''),
            image_path=img_p,
            icon_path=icon_p,
            focus_areas=data.get('focus_areas', []),
            common_mistakes=data.get('common_mistakes', []),
            breathing_tips=data.get('breathing_tips', []),
            is_reps_based=bool(data.get('is_reps_based', False)),
            default_reps=int(data.get('default_reps', 12))
        )


@dataclass
class WorkoutStep:
    """
    A single step inside a workout routine (either an exercise or a rest interval).
    """
    step_id: str
    step_type: StepType
    duration_seconds: int
    exercise: Optional[Exercise] = None
    target_reps: Optional[int] = None  # None if time-based

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "step_type": self.step_type.value,
            "duration_seconds": self.duration_seconds,
            "exercise": self.exercise.to_dict() if self.exercise else None,
            "target_reps": self.target_reps
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkoutStep':
        ex = Exercise.from_dict(data['exercise']) if data.get('exercise') else None
        return cls(
            step_id=data['step_id'],
            step_type=StepType(data['step_type']),
            duration_seconds=data['duration_seconds'],
            exercise=ex,
            target_reps=data.get('target_reps')
        )


@dataclass
class WorkoutRoutine:
    """
    A complete structured routine (e.g. 7-Minute Full Body, Core Burner).
    """
    id: str
    title: str
    description: str
    target_muscle: MuscleGroup
    difficulty: DifficultyLevel
    steps: List[WorkoutStep] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    cover_image: str = ""

    @property
    def total_duration_seconds(self) -> int:
        return sum(step.duration_seconds for step in self.steps)

    @property
    def exercise_count(self) -> int:
        return sum(1 for step in self.steps if step.step_type == StepType.EXERCISE)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "target_muscle": self.target_muscle.value,
            "difficulty": self.difficulty.value,
            "tags": self.tags,
            "cover_image": self.cover_image or f"workout_data/images/covers/cover_{self.id}.png",
            "steps": [step.to_dict() for step in self.steps]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkoutRoutine':
        return cls(
            id=data['id'],
            title=data['title'],
            description=data['description'],
            target_muscle=MuscleGroup(data['target_muscle']),
            difficulty=DifficultyLevel(data['difficulty']),
            tags=data.get('tags', []),
            cover_image=data.get('cover_image') or f"workout_data/images/covers/cover_{data['id']}.png",
            steps=[WorkoutStep.from_dict(s) for s in data.get('steps', [])]
        )


@dataclass
class UserProfile:
    """
    User settings and biometrics for personalized experience.
    UX: Learnability, Memorability (preferences retained), Credible calorie calculation.
    """
    user_id: str = "default_user"
    name: str = "Athlete"
    age: int = 25
    gender: str = "pria"
    weight_kg: float = 65.0
    height_cm: float = 170.0
    fitness_level: DifficultyLevel = DifficultyLevel.BEGINNER
    target_focus: str = "Full Body"
    default_rest_seconds: int = 15
    sound_enabled: bool = True
    high_contrast_mode: bool = False
    voice_cues_enabled: bool = True
    show_onboarding_guide: bool = True
    is_profile_completed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['fitness_level'] = self.fitness_level.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserProfile':
        return cls(
            user_id=data.get('user_id', 'default_user'),
            name=data.get('name', 'Athlete'),
            age=int(data.get('age', 25)),
            gender=data.get('gender', 'pria'),
            weight_kg=float(data.get('weight_kg', 65.0)),
            height_cm=float(data.get('height_cm', 170.0)),
            fitness_level=DifficultyLevel(data.get('fitness_level', DifficultyLevel.BEGINNER.value)),
            target_focus=data.get('target_focus', 'Full Body'),
            default_rest_seconds=int(data.get('default_rest_seconds', 15)),
            sound_enabled=bool(data.get('sound_enabled', True)),
            high_contrast_mode=bool(data.get('high_contrast_mode', False)),
            voice_cues_enabled=bool(data.get('voice_cues_enabled', True)),
            show_onboarding_guide=bool(data.get('show_onboarding_guide', True)),
            is_profile_completed=bool(data.get('is_profile_completed', False))
        )


@dataclass
class WorkoutLog:
    """
    Record of completed or attempted workout session.
    UX: Credible (scientific calorie estimation), Valuable (streak, progress tracker).
    """
    log_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    routine_id: str = ""
    routine_title: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    duration_spent_seconds: int = 0
    total_routine_duration_seconds: int = 0
    calories_burned: float = 0.0
    completed_steps_count: int = 0
    total_steps_count: int = 0
    status: str = "COMPLETED"  # COMPLETED or ABORTED
    user_feedback: Optional[str] = None
    recommendation_given: Optional[str] = None

    @property
    def completion_percentage(self) -> float:
        if self.status == "COMPLETED":
            return 100.0
        if self.total_steps_count == 0:
            return 0.0
        return round((self.completed_steps_count / self.total_steps_count) * 100, 1)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['completion_percentage'] = self.completion_percentage
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkoutLog':
        return cls(
            log_id=data.get('log_id', str(uuid.uuid4())[:8]),
            routine_id=data.get('routine_id', ''),
            routine_title=data.get('routine_title', ''),
            timestamp=data.get('timestamp', datetime.now().isoformat()),
            duration_spent_seconds=int(data.get('duration_spent_seconds', 0)),
            total_routine_duration_seconds=int(data.get('total_routine_duration_seconds', 0)),
            calories_burned=float(data.get('calories_burned', 0.0)),
            completed_steps_count=int(data.get('completed_steps_count', 0)),
            total_steps_count=int(data.get('total_steps_count', 0)),
            status=data.get('status', 'COMPLETED'),
            user_feedback=data.get('user_feedback'),
            recommendation_given=data.get('recommendation_given')
        )


class DayOfWeek(str, Enum):
    SENIN = "Senin"
    SELASA = "Selasa"
    RABU = "Rabu"
    KAMIS = "Kamis"
    JUMAT = "Jumat"
    SABTU = "Sabtu"
    MINGGU = "Minggu"


@dataclass
class DailySchedule:
    """
    Schedule entry for a single day of the week.
    User can assign a routine (preset or custom), or mark it as Rest Day.
    """
    day: str
    is_rest_day: bool = False
    routine_id: Optional[str] = None
    routine_title: Optional[str] = None
    scheduled_time: str = "07:00"
    reminder_enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DailySchedule':
        return cls(**data)


@dataclass
class WeeklySchedule:
    """
    User's 7-day routine schedule.
    UX: Helpful for habit building, structure, and future notification reminders.
    """
    schedule_id: str = "default_weekly"
    days: Dict[str, DailySchedule] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schedule_id": self.schedule_id,
            "days": {day: item.to_dict() for day, item in self.days.items()}
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WeeklySchedule':
        days_dict = {}
        for d, item_data in data.get("days", {}).items():
            days_dict[d] = DailySchedule.from_dict(item_data)
        return cls(
            schedule_id=data.get("schedule_id", "default_weekly"),
            days=days_dict
        )
