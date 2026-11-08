import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def normalize_database_url(url):
    """Return a SQLAlchemy-compatible Postgres URL.

    Some hosts still hand out ``postgres://`` URLs, but SQLAlchemy 2 and
    psycopg expect the ``postgresql://`` scheme.
    """
    if not url:
        return None
    if url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://") :]
    return url


def database_uri():
    """Use DATABASE_URL when provided, otherwise the local SQLite file."""
    return normalize_database_url(os.environ.get("DATABASE_URL")) or (
        "sqlite:///" + str(BASE_DIR / "instance" / "requests.db")
    )


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "local-development-only-change-before-deploy")
    SQLALCHEMY_DATABASE_URI = database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Hosted Postgres can drop idle connections (for example, when a free
    # database scales to zero). Check connections before use and recycle them.
    SQLALCHEMY_ENGINE_OPTIONS = (
        {"pool_pre_ping": True, "pool_recycle": 300}
        if SQLALCHEMY_DATABASE_URI.startswith("postgresql")
        else {}
    )
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # Set SESSION_COOKIE_SECURE=1 on an HTTPS deployment.
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "0") == "1"
    # Production default. Tests override this with a faster method.
    PASSWORD_HASH_METHOD = "scrypt"
