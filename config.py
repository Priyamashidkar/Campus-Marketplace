import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    """Base application configuration."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "campus-marketplace-super-secret-key-2026")

    # Primary Database: MySQL with SQLite fallback if MySQL is not configured or unavailable
    DATABASE_URL = os.environ.get("DATABASE_URL")
    if not DATABASE_URL:
        # Fallback to local SQLite database in project directory
        DATABASE_URL = f"sqlite:///{BASE_DIR / 'campus_marketplace.db'}"

    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 280,
        "pool_pre_ping": True,
    } if "mysql" in DATABASE_URL else {}

    # Uploads configuration
    UPLOAD_FOLDER = BASE_DIR / "app" / "static" / "uploads"
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB max per upload
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}

    # Campus Domain Verification (Configurable)
    CAMPUS_EMAIL_DOMAINS = ["campus.edu", "university.edu", "college.edu", "student.edu"]
    ENFORCE_CAMPUS_EMAIL = os.environ.get("ENFORCE_CAMPUS_EMAIL", "False").lower() in ("true", "1", "t")

    # ERP Configuration
    LOW_STOCK_THRESHOLD = 3


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    ENFORCE_CAMPUS_EMAIL = False


class ProductionConfig(Config):
    DEBUG = False


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
