"""
FitPulse Authentication & Security Module.
Provides secure password hashing (bcrypt) and JSON Web Tokens (JWT).
"""

import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import bcrypt
import jwt
from sqlalchemy.orm import Session

from .database import User, DBUserProfile, DBWeeklySchedule

# Configuration
JWT_SECRET = os.environ.get("JWT_SECRET", "fitpulse_jwt_secret_dev_key_2026_super_secure_984372")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_DAYS = int(os.environ.get("JWT_EXPIRE_DAYS", 30))


def hash_password(password: str) -> str:
    """Hashes a raw password using direct bcrypt."""
    pw_bytes = password.encode('utf-8')
    # Bcrypt max length is 72 bytes
    if len(pw_bytes) > 72:
        pw_bytes = pw_bytes[:72]
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(pw_bytes, salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a raw password against the stored bcrypt hash."""
    try:
        pw_bytes = plain_password.encode('utf-8')
        if len(pw_bytes) > 72:
            pw_bytes = pw_bytes[:72]
        return bcrypt.checkpw(pw_bytes, hashed_password.encode('utf-8'))
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a signed JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decodes and validates a JWT access token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except (jwt.PyJWTError, Exception):
        return None


# -----------------------------------------------------------------------------
# User Account Operations
# -----------------------------------------------------------------------------

def register_user(
    db: Session,
    username: str,
    email: str,
    password: str,
    name: Optional[str] = None
) -> User:
    """
    Registers a new user, hashes password, and creates initial profile + default schedule.
    Raises ValueError if username or email is already taken.
    """
    clean_username = username.strip().lower()
    clean_email = email.strip().lower()

    if len(clean_username) < 3:
        raise ValueError("Username minimal 3 karakter.")
    if len(password) < 6:
        raise ValueError("Password minimal 6 karakter.")
    if "@" not in clean_email or "." not in clean_email:
        raise ValueError("Format email tidak valid.")

    # Check duplicates
    if db.query(User).filter(User.username == clean_username).first():
        raise ValueError("Username sudah terdaftar. Silakan pilih username lain.")
    if db.query(User).filter(User.email == clean_email).first():
        raise ValueError("Email sudah terdaftar. Silakan gunakan email lain atau masuk.")

    new_user = User(
        id=str(uuid.uuid4()),
        username=clean_username,
        email=clean_email,
        password_hash=hash_password(password),
        created_at=datetime.utcnow()
    )
    db.add(new_user)
    db.flush()

    # Create associated profile
    user_name = name.strip() if name and name.strip() else clean_username.capitalize()
    profile = DBUserProfile(
        user_id=new_user.id,
        name=user_name,
        weight_kg=65.0,
        height_cm=170.0,
        fitness_level="Beginner",
        default_rest_seconds=15,
        sound_enabled=True,
        voice_cues_enabled=True,
        high_contrast_mode=False,
        show_onboarding_guide=True
    )
    db.add(profile)

    # Create initial weekly schedule (Monday to Sunday)
    default_days = [
        ("Senin", "routine_full_body_ignition", False),
        ("Selasa", "routine_core_blast", False),
        ("Rabu", None, True),
        ("Kamis", "routine_upper_body_strength", False),
        ("Jumat", "routine_lower_body_power", False),
        ("Sabtu", "routine_hiit_fat_burn", False),
        ("Minggu", None, True),
    ]
    for day_name, routine_id, is_rest in default_days:
        sched = DBWeeklySchedule(
            id=str(uuid.uuid4()),
            user_id=new_user.id,
            day_name=day_name,
            routine_id=routine_id,
            is_rest_day=is_rest,
            scheduled_time="07:00",
            reminder_enabled=True
        )
        db.add(sched)

    db.commit()
    db.refresh(new_user)
    return new_user


def authenticate_user(
    db: Session,
    identifier: str,
    password: str
) -> Optional[User]:
    """
    Authenticates a user by email OR username and password.
    Returns User if valid, None otherwise.
    """
    clean_id = identifier.strip().lower()
    user = db.query(User).filter(
        (User.username == clean_id) | (User.email == clean_id)
    ).first()

    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None

    return user


def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
    """Retrieves a user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def ensure_guest_or_default_user(db: Session) -> User:
    """
    Ensures a default user exists for backward compatibility,
    offline use, or guest mode.
    """
    default_id = "default_user"
    user = db.query(User).filter(User.id == default_id).first()
    if not user:
        user = User(
            id=default_id,
            username="guest",
            email="guest@fitpulse.local",
            password_hash=hash_password("guest123"),
            created_at=datetime.utcnow()
        )
        db.add(user)
        db.flush()

        # Create profile
        profile = DBUserProfile(
            user_id=default_id,
            name="Tamu FitPulse",
            weight_kg=65.0,
            height_cm=170.0,
            fitness_level="Beginner",
            default_rest_seconds=15,
            sound_enabled=True,
            voice_cues_enabled=True,
            high_contrast_mode=False,
            show_onboarding_guide=True
        )
        db.add(profile)

        # Default schedule
        default_days = [
            ("Senin", "routine_full_body_ignition", False),
            ("Selasa", "routine_core_blast", False),
            ("Rabu", None, True),
            ("Kamis", "routine_upper_body_strength", False),
            ("Jumat", "routine_lower_body_power", False),
            ("Sabtu", "routine_hiit_fat_burn", False),
            ("Minggu", None, True),
        ]
        for day_name, routine_id, is_rest in default_days:
            sched = DBWeeklySchedule(
                id=str(uuid.uuid4()),
                user_id=default_id,
                day_name=day_name,
                routine_id=routine_id,
                is_rest_day=is_rest,
                scheduled_time="07:00",
                reminder_enabled=True
            )
            db.add(sched)

        db.commit()
        db.refresh(user)

    return user
