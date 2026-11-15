"""
FitPulse Database Layer (SQLAlchemy 2.0).
Supports:
1. TiDB Cloud Serverless (MySQL-compatible with TLS/SSL over port 4000)
2. Standard MySQL / PostgreSQL
3. SQLite (local fallback for development and offline Desktop GUI)
"""

import os
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

from sqlalchemy import (
    create_engine, Column, String, Integer, Float, Boolean, Text,
    DateTime, ForeignKey, Index, inspect
)
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session, relationship

Base = declarative_base()

# -----------------------------------------------------------------------------
# Database Engine Initialization
# -----------------------------------------------------------------------------

def get_database_url() -> str:
    """
    Resolves the Database URL from environment variables with priority:
    1. DATABASE_URL (Direct connection string, e.g. from TiDB Cloud or Vercel Env)
    2. TIDB_HOST / TIDB_USER / TIDB_PASSWORD components
    3. SQLite local fallback file in workout_data/fitpulse.db
    """
    raw_url = os.environ.get("DATABASE_URL", "").strip()
    if raw_url:
        # Normalize postgres:// -> postgresql:// for SQLAlchemy compatibility if needed
        if raw_url.startswith("postgres://"):
            raw_url = raw_url.replace("postgres://", "postgresql://", 1)
        # Ensure mysql uses pymysql driver if not specified
        if raw_url.startswith("mysql://"):
            raw_url = raw_url.replace("mysql://", "mysql+pymysql://", 1)
        return raw_url

    # Check TiDB individual environment variables
    tidb_host = os.environ.get("TIDB_HOST", "").strip()
    if tidb_host:
        tidb_port = os.environ.get("TIDB_PORT", "4000").strip()
        tidb_user = os.environ.get("TIDB_USER", "root").strip()
        tidb_password = os.environ.get("TIDB_PASSWORD", "").strip()
        tidb_db = os.environ.get("TIDB_DATABASE", "fitpulse").strip()
        
        # TiDB Cloud Serverless requires SSL
        return f"mysql+pymysql://{tidb_user}:{tidb_password}@{tidb_host}:{tidb_port}/{tidb_db}?ssl_verify_cert=true"

    # Fallback to SQLite in workout_data
    base_dir = Path(__file__).resolve().parent.parent / "workout_data"
    base_dir.mkdir(parents=True, exist_ok=True)
    sqlite_path = base_dir / "fitpulse.db"
    return f"sqlite:///{sqlite_path.as_posix()}"


def create_db_engine():
    """Creates and configures the SQLAlchemy engine."""
    url = get_database_url()
    connect_args = {}

    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        engine = create_engine(
            url,
            connect_args=connect_args,
            echo=False
        )
    elif "mysql" in url or "pymysql" in url:
        # TiDB Cloud Serverless optimization:
        # pool_recycle=300 (5 min) prevents dropped connections on serverless idle
        # pool_pre_ping=True checks connection liveness before executing queries
        connect_args = {
            "ssl": {
                "check_hostname": False,
                "verify_mode": 0
            }
        } if "tidbcloud.com" in url or "ssl_verify" in url else {}
        
        engine = create_engine(
            url,
            connect_args=connect_args,
            pool_pre_ping=True,
            pool_recycle=300,
            pool_size=10,
            max_overflow=20,
            echo=False
        )
    else:
        engine = create_engine(
            url,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=False
        )

    return engine


# Shared Engine and Session
engine = create_db_engine()
SessionFactory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
db_session = scoped_session(SessionFactory)


# -----------------------------------------------------------------------------
# SQLAlchemy Models
# -----------------------------------------------------------------------------

class User(Base):
    """User account for authentication & login."""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    profile = relationship("DBUserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    logs = relationship("DBWorkoutLog", back_populates="user", cascade="all, delete-orphan")
    schedules = relationship("DBWeeklySchedule", back_populates="user", cascade="all, delete-orphan")
    pendings = relationship("DBPendingWorkout", back_populates="user", cascade="all, delete-orphan")
    custom_routines = relationship("DBCustomRoutine", back_populates="user", cascade="all, delete-orphan")
    weight_logs = relationship("DBWeightLog", back_populates="user", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class DBUserProfile(Base):
    """User personal metrics & UI/audio preferences."""
    __tablename__ = "user_profiles"

    user_id = Column(String(36), ForeignKey("users.id"), primary_key=True)
    name = Column(String(100), default="Athlete")
    weight_kg = Column(Float, default=65.0)
    height_cm = Column(Float, default=170.0)
    fitness_level = Column(String(30), default="Beginner")
    default_rest_seconds = Column(Integer, default=15)
    sound_enabled = Column(Boolean, default=True)
    voice_cues_enabled = Column(Boolean, default=True)
    high_contrast_mode = Column(Boolean, default=False)
    show_onboarding_guide = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="profile")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "name": self.name,
            "weight_kg": self.weight_kg,
            "height_cm": self.height_cm,
            "fitness_level": self.fitness_level,
            "default_rest_seconds": self.default_rest_seconds,
            "sound_enabled": self.sound_enabled,
            "voice_cues_enabled": self.voice_cues_enabled,
            "high_contrast_mode": self.high_contrast_mode,
            "show_onboarding_guide": self.show_onboarding_guide
        }


class DBWorkoutLog(Base):
    """History log of user workout sessions (completed or aborted)."""
    __tablename__ = "workout_logs"

    log_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4())[:8])
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    routine_id = Column(String(100), nullable=False)
    routine_title = Column(String(255), nullable=False)
    timestamp = Column(String(50), default=lambda: datetime.now().isoformat())
    duration_spent_seconds = Column(Integer, default=0)
    total_routine_duration_seconds = Column(Integer, default=0)
    calories_burned = Column(Float, default=0.0)
    completed_steps_count = Column(Integer, default=0)
    total_steps_count = Column(Integer, default=0)
    status = Column(String(20), default="COMPLETED")  # COMPLETED or ABORTED
    user_feedback = Column(String(50), nullable=True)
    recommendation_given = Column(Text, nullable=True)

    user = relationship("User", back_populates="logs")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "log_id": self.log_id,
            "user_id": self.user_id,
            "routine_id": self.routine_id,
            "routine_title": self.routine_title,
            "timestamp": self.timestamp,
            "duration_spent_seconds": self.duration_spent_seconds,
            "total_routine_duration_seconds": self.total_routine_duration_seconds,
            "calories_burned": self.calories_burned,
            "completed_steps_count": self.completed_steps_count,
            "total_steps_count": self.total_steps_count,
            "status": self.status,
            "user_feedback": self.user_feedback,
            "recommendation_given": self.recommendation_given
        }


class DBWeeklySchedule(Base):
    """Weekly schedule item (Monday to Sunday) per user."""
    __tablename__ = "weekly_schedules"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    day_name = Column(String(20), nullable=False)
    routine_id = Column(String(100), nullable=True)
    is_rest_day = Column(Boolean, default=False)
    scheduled_time = Column(String(10), default="07:00")
    reminder_enabled = Column(Boolean, default=True)

    user = relationship("User", back_populates="schedules")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "day": self.day_name,
            "routine_id": self.routine_id,
            "is_rest_day": self.is_rest_day,
            "scheduled_time": self.scheduled_time,
            "reminder_enabled": self.reminder_enabled
        }


class DBPendingWorkout(Base):
    """Paused or in-progress workouts waiting to be resumed."""
    __tablename__ = "pending_workouts"

    pending_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4())[:8])
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    routine_id = Column(String(100), nullable=False)
    routine_title = Column(String(255), nullable=False)
    current_step_index = Column(Integer, default=0)
    total_steps_count = Column(Integer, default=0)
    duration_spent_seconds = Column(Integer, default=0)
    calories_burned = Column(Float, default=0.0)
    timestamp = Column(String(50), default=lambda: datetime.now().isoformat())

    user = relationship("User", back_populates="pendings")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pending_id": self.pending_id,
            "user_id": self.user_id,
            "routine_id": self.routine_id,
            "routine_title": self.routine_title,
            "current_step_index": self.current_step_index,
            "total_steps_count": self.total_steps_count,
            "duration_spent_seconds": self.duration_spent_seconds,
            "calories_burned": self.calories_burned,
            "timestamp": self.timestamp
        }


class DBCustomRoutine(Base):
    """Custom user-created workout routine templates."""
    __tablename__ = "custom_routines"

    id = Column(String(100), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, default="")
    target_muscle = Column(String(50), default="Full Body")
    difficulty = Column(String(30), default="Beginner")
    tags_json = Column(Text, default="[]")
    steps_json = Column(Text, default="[]")
    cover_image = Column(String(255), default="workout_data/images/covers/cover_default_custom.png")
    created_at = Column(String(50), default=lambda: datetime.now().isoformat())

    user = relationship("User", back_populates="custom_routines")


class DBWeightLog(Base):
    """Historical weight entries for progress tracking."""
    __tablename__ = "weight_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4())[:8])
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    weight_kg = Column(Float, nullable=False)
    timestamp = Column(String(50), default=lambda: datetime.now().isoformat())

    user = relationship("User", back_populates="weight_logs")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "weight_kg": self.weight_kg,
            "timestamp": self.timestamp
        }


# -----------------------------------------------------------------------------
# Database Setup & Initialization
# -----------------------------------------------------------------------------

_tables_initialized = False

def init_db():
    """
    Creates all tables in TiDB Cloud / MySQL / SQLite if they do not exist.
    Safe to call repeatedly on startup.
    """
    global _tables_initialized
    try:
        Base.metadata.create_all(bind=engine)
        _tables_initialized = True
        print("✅ Database tables verified & initialized.")
    except Exception as e:
        print(f"⚠️ Database init_db error: {e}")


def get_db():
    """FastAPI dependency for obtaining a database session."""
    global _tables_initialized
    if not _tables_initialized:
        init_db()
    session = SessionFactory()
    try:
        yield session
    finally:
        session.close()

