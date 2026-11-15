"""
FitPulse Web Server Application (FastAPI).
Provides full REST API, Multi-User Authentication, TiDB Cloud / SQLite DB support,
and serves the responsive modern Web Application.
"""

import os
import io
import sys
import uuid
from typing import Optional, List, Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response, Depends, Header
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from homeworkout.service import WorkoutAppService
from homeworkout.models import (
    MuscleGroup, DifficultyLevel, StepType, SessionState,
    WorkoutRoutine, WorkoutStep, Exercise, UserProfile, WorkoutLog,
    DailySchedule, DayOfWeek
)
from homeworkout.anatomy import generate_muscle_anatomy_image
from homeworkout.database import get_db, SessionFactory, User, init_db, engine
from homeworkout.auth import (
    register_user, authenticate_user, create_access_token, decode_access_token,
    get_user_by_id, ensure_guest_or_default_user
)

# Base directory
BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"
IMAGES_DIR = BASE_DIR / "workout_data" / "images"

# Ensure directories exist
WEB_DIR.mkdir(exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Initialize service & database
service = WorkoutAppService()

app = FastAPI(
    title="FitPulse - Home Workout Companion Web API",
    description="Responsive Multi-User Web App backend with TiDB Cloud & Vercel deployment support",
    version="2.5.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_no_cache_header(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/static") or request.url.path == "/":
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


# ============================================================================
# AUTHENTICATION DEPENDENCY
# ============================================================================

def get_current_user_id(request: Request) -> str:
    """
    Extracts the authenticated user ID from:
    1. Authorization: Bearer <token>
    2. x-auth-token header
    3. fitpulse_token cookie
    Falls back to 'default_user' (guest mode) if unauthenticated.
    """
    auth_header = request.headers.get("Authorization", "")
    token = None
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
    elif "x-auth-token" in request.headers:
        token = request.headers["x-auth-token"].strip()
    elif "fitpulse_token" in request.cookies:
        token = request.cookies["fitpulse_token"]

    if token:
        payload = decode_access_token(token)
        if payload and "sub" in payload:
            return payload["sub"]

    return "default_user"


# ============================================================================
# API MODELS (Pydantic)
# ============================================================================

class UserRegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    name: Optional[str] = None


class UserLoginRequest(BaseModel):
    identifier: str
    password: str


class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    fitness_level: Optional[str] = None
    default_rest_seconds: Optional[int] = None
    sound_enabled: Optional[bool] = None
    voice_cues_enabled: Optional[bool] = None
    high_contrast_mode: Optional[bool] = None
    show_onboarding_guide: Optional[bool] = None


class ScheduleUpdateRequest(BaseModel):
    day: str
    routine_id: Optional[str] = None
    is_rest_day: bool = False
    scheduled_time: Optional[str] = "07:00"
    reminder_enabled: Optional[bool] = True


class StepEditItem(BaseModel):
    step_id: Optional[str] = None
    step_type: Optional[str] = "Exercise"
    exercise_id: Optional[str] = None
    duration_seconds: int
    target_reps: Optional[int] = None


class RoutineStepsUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    steps: List[StepEditItem]


class CustomRoutineCreateRequest(BaseModel):
    title: str
    description: str
    target_muscle: str
    difficulty: str
    selected_exercise_ids: List[str]
    exercise_durations: Optional[Dict[str, int]] = None
    exercise_reps: Optional[Dict[str, int]] = None
    rest_seconds: Optional[int] = None


class SaveLogRequest(BaseModel):
    routine_id: str
    routine_title: str
    duration_spent_seconds: int
    total_routine_duration_seconds: int
    calories_burned: float
    completed_steps_count: int
    total_steps_count: int
    status: str
    user_feedback: Optional[str] = None
    recommendation_given: Optional[str] = None


class FeedbackRequest(BaseModel):
    log_id: str
    user_feedback: str  # "TOO_EASY", "JUST_RIGHT", "CHALLENGING", "EXHAUSTING"


class ResetDataRequest(BaseModel):
    confirm_text: str


class PendingWorkoutRequest(BaseModel):
    pending_id: Optional[str] = None
    routine_id: str
    routine_title: str
    current_step_index: int
    total_steps_count: int
    duration_spent_seconds: int
    calories_burned: float


# ============================================================================
# SYSTEM HEALTH & DEPLOYMENT DIAGNOSTICS
# ============================================================================

@app.get("/api/health")
def api_health():
    """Health check endpoint for Vercel, TiDB Cloud, and deployment verification."""
    from sqlalchemy import text
    init_db()
    driver_name = getattr(engine.url, 'drivername', 'unknown')
    db_type = "TiDB Cloud Serverless (MySQL)" if "mysql" in driver_name else ("SQLite" if "sqlite" in driver_name else driver_name)
    db_connected = False
    db_err = None

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            db_connected = True
    except Exception as e:
        db_err = str(e)

    return {
        "status": "healthy" if db_connected else "degraded",
        "app": "FitPulse - Home Workout Companion",
        "version": "2.5.0",
        "database": {
            "connected": db_connected,
            "type": db_type,
            "error": db_err
        },
        "hosting": "Vercel / Cloud Ready"
    }


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.post("/api/auth/register")
def api_register(req: UserRegisterRequest):
    """Registers a new user and returns JWT access token + profile."""
    init_db()
    session = SessionFactory()
    try:
        user = register_user(
            session,
            username=req.username,
            email=req.email,
            password=req.password,
            name=req.name
        )
        token = create_access_token({"sub": user.id, "username": user.username})
        profile = service.get_profile(user_id=user.id)
        return {
            "success": True,
            "token": token,
            "user": user.to_dict(),
            "profile": profile.to_dict(),
            "message": f"Selamat datang di FitPulse, {user.username}!"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal mendaftar: {e}")
    finally:
        session.close()


@app.post("/api/auth/login")
def api_login(req: UserLoginRequest):
    """Logs in an existing user and returns JWT token + profile."""
    init_db()
    session = SessionFactory()
    try:
        user = authenticate_user(session, identifier=req.identifier, password=req.password)
        if not user:
            raise HTTPException(status_code=401, detail="Email/Username atau kata sandi tidak cocok.")
        token = create_access_token({"sub": user.id, "username": user.username})
        profile = service.get_profile(user_id=user.id)
        return {
            "success": True,
            "token": token,
            "user": user.to_dict(),
            "profile": profile.to_dict(),
            "message": f"Halo {user.username}, Anda berhasil masuk!"
        }
    finally:
        session.close()


@app.get("/api/auth/me")
def api_get_me(user_id: str = Depends(get_current_user_id)):
    """Returns currently authenticated user data and profile."""
    session = SessionFactory()
    try:
        user = get_user_by_id(session, user_id)
        if not user:
            user = ensure_guest_or_default_user(session)
        profile = service.get_profile(user_id=user.id)
        is_guest = (user.id == "default_user")
        return {
            "authenticated": not is_guest,
            "is_guest": is_guest,
            "user": user.to_dict(),
            "profile": profile.to_dict()
        }
    finally:
        session.close()


@app.post("/api/auth/logout")
def api_logout():
    """Logs out user (client removes stored token)."""
    return {"success": True, "message": "Berhasil keluar."}


# ============================================================================
# APPLICATION DATA ENDPOINTS (Scattered per authenticated user)
# ============================================================================

@app.get("/api/today")
def get_today_info(user_id: str = Depends(get_current_user_id)):
    """Returns today's day name, schedule, streak, and quick-start status."""
    today_name = service.get_today_day_name()
    today_sched = service.get_today_schedule(user_id=user_id)
    profile = service.get_profile(user_id=user_id)
    stats = service.get_user_dashboard_stats(user_id=user_id)
    consistency = service.storage.compute_weekly_consistency(user_id=user_id)

    return {
        "today_day_name": today_name,
        "schedule": today_sched.to_dict(),
        "streak_days": stats.get("current_streak_days", stats.get("streak_days", 0)),
        "user_name": profile.name,
        "weight_kg": profile.weight_kg,
        "height_cm": profile.height_cm,
        "consistency": consistency
    }


@app.get("/api/profile")
def get_profile(user_id: str = Depends(get_current_user_id)):
    """Returns user profile."""
    return service.get_profile(user_id=user_id).to_dict()


@app.post("/api/profile")
def update_profile(req: ProfileUpdateRequest, user_id: str = Depends(get_current_user_id)):
    """Updates user biometrics and preferences."""
    kwargs = {k: v for k, v in req.model_dump().items() if v is not None}
    try:
        updated = service.update_profile(user_id=user_id, **kwargs)
        return {"success": True, "profile": updated.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/stats")
def get_dashboard_stats(user_id: str = Depends(get_current_user_id)):
    """Returns dashboard metrics, lifetime records, and schedule-based consistency analysis."""
    stats = service.get_user_dashboard_stats(user_id=user_id)
    profile = service.get_profile(user_id=user_id)
    consistency_data = service.storage.compute_weekly_consistency(user_id=user_id)

    # BMI calculation
    height_m = profile.height_cm / 100.0
    bmi = profile.weight_kg / (height_m * height_m) if height_m > 0 else 22.0

    if bmi < 18.5:
        bmi_cat = "Kekurangan Berat Badan (Underweight)"
        bmi_color = "#3B82F6"
    elif bmi < 25.0:
        bmi_cat = "Berat Badan Sehat / Ideal (Healthy)"
        bmi_color = "#10B981"
    elif bmi < 30.0:
        bmi_cat = "Kelebihan Berat Badan (Overweight)"
        bmi_color = "#F59E0B"
    else:
        bmi_cat = "Obesitas (Obese)"
        bmi_color = "#EF4444"

    return {
        "streak_days": stats.get("current_streak_days", stats.get("streak_days", 0)),
        "personal_best_streak": stats.get("personal_best_streak", stats.get("current_streak_days", 0)),
        "total_workouts": stats.get("total_workouts", 0),
        "total_calories": round(stats.get("total_calories", 0.0), 1),
        "total_minutes": round(stats.get("total_minutes", 0.0), 1),
        "weight_kg": profile.weight_kg,
        "height_cm": profile.height_cm,
        "bmi": round(bmi, 1),
        "bmi_category": bmi_cat,
        "bmi_color": bmi_color,
        "consistency": consistency_data
    }


@app.get("/api/routines")
def list_routines(keyword: str = "", target_muscle: str = "", user_id: str = Depends(get_current_user_id)):
    """Lists routines with search and target muscle filter."""
    routines = service.list_routines(user_id=user_id)

    if target_muscle and target_muscle != "Semua":
        routines = [r for r in routines if r.target_muscle.value.lower() == target_muscle.lower()]

    if keyword:
        kw = keyword.lower().strip()
        routines = [
            r for r in routines
            if kw in r.title.lower() or kw in r.description.lower() or kw in r.target_muscle.value.lower()
        ]

    return [r.to_dict() for r in routines]


@app.get("/api/routines/{routine_id}")
def get_routine(routine_id: str, user_id: str = Depends(get_current_user_id)):
    """Returns single routine detail with full steps and exercises."""
    routine = service.get_routine_by_id(routine_id, user_id=user_id)
    if not routine:
        raise HTTPException(status_code=404, detail="Program latihan tidak ditemukan.")
    return routine.to_dict()


@app.post("/api/routines/{routine_id}/steps")
def update_routine_steps(routine_id: str, req: RoutineStepsUpdateRequest, user_id: str = Depends(get_current_user_id)):
    """Customizes title, description, order, duration, and reps for steps in a routine."""
    routine = service.get_routine_by_id(routine_id, user_id=user_id)
    if not routine:
        raise HTTPException(status_code=404, detail="Program latihan tidak ditemukan.")

    if req.title and req.title.strip():
        routine.title = req.title.strip()
    if req.description and req.description.strip():
        routine.description = req.description.strip()

    ex_map = {ex.id: ex for ex in service.list_exercises()}
    existing_step_map = {s.step_id: s for s in routine.steps}

    new_steps = []
    for idx, item in enumerate(req.steps):
        s_id = item.step_id or f"step_{idx+1}_{uuid.uuid4().hex[:4]}"
        st_type_str = item.step_type or "Exercise"
        st_type = StepType.REST if st_type_str.lower() in ["rest", "istirahat"] else StepType.EXERCISE

        exercise = None
        if st_type == StepType.EXERCISE:
            if item.exercise_id and item.exercise_id in ex_map:
                exercise = ex_map[item.exercise_id]
            elif item.step_id and item.step_id in existing_step_map:
                exercise = existing_step_map[item.step_id].exercise

        dur = max(5, item.duration_seconds)
        reps = item.target_reps if (item.target_reps is not None and item.target_reps > 0) else None

        new_steps.append(WorkoutStep(
            step_id=s_id,
            step_type=st_type,
            duration_seconds=dur,
            exercise=exercise,
            target_reps=reps
        ))

    if not any(s.step_type == StepType.EXERCISE for s in new_steps):
        raise HTTPException(status_code=400, detail="Program latihan harus memiliki minimal 1 gerakan latihan.")

    routine.steps = new_steps
    service.save_or_update_routine(routine, user_id=user_id)
    return {"success": True, "routine": routine.to_dict()}


@app.delete("/api/routines/{routine_id}")
def delete_routine_endpoint(routine_id: str, user_id: str = Depends(get_current_user_id)):
    """Deletes a workout routine."""
    all_routines = service.list_routines(user_id=user_id)
    if len(all_routines) <= 1:
        raise HTTPException(
            status_code=400,
            detail="Tidak dapat menghapus template terakhir. Aplikasi membutuhkan minimal 1 program latihan."
        )

    success = service.delete_routine(routine_id, user_id=user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Program latihan tidak ditemukan.")
    return {"success": True, "message": f"Template '{routine_id}' berhasil dihapus."}


@app.post("/api/routines/custom")
def create_custom_routine(req: CustomRoutineCreateRequest, user_id: str = Depends(get_current_user_id)):
    """Creates a new personalized custom workout routine."""
    try:
        muscle = MuscleGroup(req.target_muscle)
        diff = DifficultyLevel(req.difficulty)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Parameter tidak valid: {e}")

    try:
        durations = req.exercise_durations or {}
        pairs = []
        for ex_id in req.selected_exercise_ids:
            dur = durations.get(ex_id, 30)
            pairs.append((ex_id, dur))

        new_routine = service.create_custom_routine(
            title=req.title,
            description=req.description,
            target_muscle=muscle,
            difficulty=diff,
            exercise_ids_and_durations=pairs,
            rest_seconds=req.rest_seconds,
            user_id=user_id
        )
        return {"success": True, "routine": new_routine.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/exercises")
def list_exercises(keyword: str = "", target_muscle: str = ""):
    """Returns exercise library."""
    exercises = service.list_exercises()
    if target_muscle and target_muscle != "Semua":
        exercises = [e for e in exercises if e.target_muscle.value.lower() == target_muscle.lower()]
    if keyword:
        kw = keyword.lower().strip()
        exercises = [
            e for e in exercises
            if kw in e.name.lower() or any(kw in f.lower() for f in e.focus_areas)
        ]
    return [e.to_dict() for e in exercises]


@app.get("/api/exercises/{exercise_id}")
def get_exercise_detail(exercise_id: str):
    """Returns single exercise detail with biometrics, mistakes, and breathing tips."""
    ex = service.get_exercise_by_id(exercise_id)
    if not ex:
        raise HTTPException(status_code=404, detail="Gerakan tidak ditemukan.")
    return ex.to_dict()


@app.get("/api/exercises/{exercise_id}/anatomy")
def get_exercise_anatomy(exercise_id: str):
    """Returns dynamic PNG anatomy diagram highlighting targeted muscle groups."""
    ex = service.get_exercise_by_id(exercise_id)
    if not ex:
        raise HTTPException(status_code=404, detail="Gerakan tidak ditemukan.")

    img = generate_muscle_anatomy_image(
        target_muscle=ex.target_muscle.value,
        focus_areas=ex.focus_areas,
        width=360,
        height=220
    )

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")


@app.get("/api/schedule")
def get_schedule(user_id: str = Depends(get_current_user_id)):
    """Returns weekly 7-day schedule."""
    sched = service.get_weekly_schedule(user_id=user_id)
    return sched.to_dict()


@app.post("/api/schedule")
def update_schedule(req: ScheduleUpdateRequest, user_id: str = Depends(get_current_user_id)):
    """Updates schedule assignment for a specific day."""
    try:
        updated = service.update_daily_schedule(
            day=req.day,
            day_name=req.day,
            routine_id=req.routine_id,
            is_rest_day=req.is_rest_day,
            scheduled_time=req.scheduled_time or "07:00",
            reminder_enabled=req.reminder_enabled if req.reminder_enabled is not None else True,
            user_id=user_id
        )
        return {"success": True, "schedule": updated.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/schedule/bulk")
def update_schedule_bulk(days_payload: Dict[str, Dict[str, Any]], user_id: str = Depends(get_current_user_id)):
    """Updates multiple or all days of the weekly schedule at once."""
    try:
        updated = service.update_all_daily_schedules(days_payload, user_id=user_id)
        return {"success": True, "schedule": updated.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/history")
def get_workout_history(user_id: str = Depends(get_current_user_id)):
    """Returns chronological list of past workout logs (newest first)."""
    logs = service.get_history(user_id=user_id)
    return [lg.to_dict() for lg in reversed(logs)]


@app.post("/api/session/save_log")
def save_workout_log(req: SaveLogRequest, user_id: str = Depends(get_current_user_id)):
    """Saves completed or partial workout log to history and updates streak."""
    completed_steps = req.completed_steps_count
    if req.status == "COMPLETED":
        completed_steps = req.total_steps_count

    log = WorkoutLog(
        routine_id=req.routine_id,
        routine_title=req.routine_title,
        duration_spent_seconds=req.duration_spent_seconds,
        total_routine_duration_seconds=req.total_routine_duration_seconds,
        calories_burned=req.calories_burned,
        completed_steps_count=completed_steps,
        total_steps_count=req.total_steps_count,
        status=req.status,
        user_feedback=req.user_feedback,
        recommendation_given=req.recommendation_given
    )

    # Generate adaptive recommendation
    rec = req.recommendation_given
    if not rec:
        if req.status == "ABORTED":
            rec = "Sesi dihentikan lebih awal. Tidak apa-apa! Dengarkan tubuh Anda, istirahat sejenak, dan coba lagi nanti."
        elif req.calories_burned >= 80:
            rec = "Luar biasa! Pembakaran kalori sangat tinggi. Pastikan minum air putih yang cukup dan konsumsi protein untuk pemulihan."
        elif req.duration_spent_seconds >= 600:
            rec = "Kerja keras yang hebat! Ketahanan kardiovaskular Anda terus berkembang. Pertahankan konsistensi ini!"
        else:
            rec = "Latihan selesai dengan sangat baik! Konsistensi adalah kunci utama kebugaran tubuh."
    log.recommendation_given = rec

    # Save log
    service.storage.append_log(log, user_id=user_id)

    return {
        "success": True,
        "log": log.to_dict(),
        "recommendation": rec
    }


@app.post("/api/session/feedback")
def submit_feedback(req: FeedbackRequest, user_id: str = Depends(get_current_user_id)):
    """Records user physical feeling and returns adaptive recovery advice."""
    advice_map = {
        "TOO_EASY": "Latihan terasa terlalu ringan? Kami sarankan menaikkan tingkat kesulitan ke Intermediate atau menambah repetisi sebesar 20% pada sesi berikutnya!",
        "JUST_RIGHT": "Pilihan intensitas sempurna! Pertahankan ritme ini untuk pembentukan otot optimal dan kebiasaan sehat jangka panjang.",
        "CHALLENGING": "Bagus sekali! Otot Anda terstimulasi maksimal. Jangan lupa penuhi kebutuhan hidrasi dan protein hari ini.",
        "EXHAUSTING": "Latihan terasa cukup berat? Berikan waktu istirahat ekstra 24 jam dan pastikan tidur nyenyak malam ini untuk pemulihan optimal."
    }

    advice = advice_map.get(req.user_feedback, "Terima kasih atas masukan Anda. Tetap konsisten dan jaga kesehatan!")
    service.storage.update_latest_log_feedback(req.user_feedback, advice, user_id=user_id)
    return {"success": True, "advice": advice}


# ============================================================================
# PENDING WORKOUTS & RESET DATA ENDPOINTS
# ============================================================================

@app.get("/api/pending_workouts")
def get_pending_workouts(user_id: str = Depends(get_current_user_id)):
    """Returns list of paused/incomplete workouts."""
    return service.get_pending_workouts(user_id=user_id)


@app.post("/api/pending_workouts")
def save_pending_workout(req: PendingWorkoutRequest, user_id: str = Depends(get_current_user_id)):
    """Saves or updates an incomplete workout session."""
    saved = service.save_pending_workout(req.model_dump(), user_id=user_id)
    return {"success": True, "pending": saved}


@app.delete("/api/pending_workouts/{pending_id}")
def delete_pending_workout(pending_id: str, user_id: str = Depends(get_current_user_id)):
    """Removes a pending workout."""
    success = service.remove_pending_workout(pending_id, user_id=user_id)
    return {"success": success}


@app.post("/api/reset_data")
def reset_all_user_data(req: ResetDataRequest, user_id: str = Depends(get_current_user_id)):
    """Resets all logs, profile, schedule, and pending workouts after 'confirm' validation."""
    if req.confirm_text.strip().lower() != "confirm":
        raise HTTPException(
            status_code=400,
            detail="Ketik kata 'confirm' dengan tepat untuk mengonfirmasi reset data."
        )
    service.reset_user_data(user_id=user_id)
    return {"success": True, "message": "Seluruh data pengguna berhasil direset ke setelan awal."}


# ============================================================================
# STATIC FILES & SPA FALLBACK
# ============================================================================

# Mount images directory (supports both /images and /workout_data/images paths)
app.mount("/images", StaticFiles(directory=str(IMAGES_DIR)), name="images")
app.mount("/workout_data/images", StaticFiles(directory=str(IMAGES_DIR)), name="workout_data_images")

# Mount web static directory
app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")


@app.get("/")
def serve_index():
    """Serves the Single Page Application."""
    index_file = WEB_DIR / "index.html"
    if not index_file.exists():
        return JSONResponse(
            status_code=500,
            content={"error": "web/index.html not found"}
        )
    return FileResponse(str(index_file))
