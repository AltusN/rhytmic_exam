import os
import pathlib
from typing import List

# Resolve the fastapi_backend/ directory regardless of where the server is launched from.
_BACKEND_DIR = pathlib.Path(__file__).parent.parent.resolve()

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    # dotenv is optional in case the package is not installed.
    pass


def _bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _list_env(name: str, default: str = "") -> List[str]:
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{_BACKEND_DIR}/rhytmic.db")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev_only_change_me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = _int_env("ACCESS_TOKEN_EXPIRE_MINUTES", 30)
RESET_TOKEN_EXPIRE_SECONDS = _int_env("RESET_TOKEN_EXPIRE_SECONDS", 5400)
DISABLE_EXAM_DATE = _bool_env("DISABLE_EXAM_DATE", True)

MAIL_SERVER = os.getenv("MAIL_SERVER", "")
MAIL_PORT = _int_env("MAIL_PORT", 587)
MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
MAIL_SENDER = os.getenv("MAIL_SENDER", "no-reply.rhytmic_exam.co.za")
MAIL_USE_TLS = _bool_env("MAIL_USE_TLS", True)
ADMINS = _list_env("ADMINS", "")
