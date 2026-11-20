"""
Configuration settings for Face Recognition Attendance System.
"""
import os
import secrets

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Application configuration."""

    # Flask — [FIX C1] Generate random secret key if not set via env
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

    # [FIX H4] Debug mode off by default, enable via environment variable only
    DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"

    # Database
    DATABASE_PATH = os.path.join(BASE_DIR, "database.db")

    # Upload folder for student photos
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}  # [FIX C3] Whitelist extensions

    # Face Recognition
    FACE_RECOGNITION_TOLERANCE = 0.45  # Lower = stricter matching
    FACE_RECOGNITION_MODEL = "hog"  # 'hog' (CPU, faster) or 'cnn' (GPU, accurate)

    # Email (SMTP)
    SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
    SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL = os.environ.get("SMTP_FROM_EMAIL", "")

    # Camera
    CAMERA_INDEX = 0  # Default webcam

    # [FIX M6] Session timeout (2 hours)
    PERMANENT_SESSION_LIFETIME = 7200  # seconds

    # [FIX H2] Login rate limiting
    MAX_LOGIN_ATTEMPTS = 5
    LOGIN_LOCKOUT_SECONDS = 300  # 5 minutes
