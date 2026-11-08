import pytest

from app import create_app
from app.config import normalize_database_url


def test_normalizes_legacy_postgres_scheme():
    assert (
        normalize_database_url("postgres://user:pass@example.com/db")
        == "postgresql://user:pass@example.com/db"
    )


def test_leaves_postgresql_scheme_unchanged():
    url = "postgresql://user:pass@example.com/db?sslmode=require"
    assert normalize_database_url(url) == url


def test_missing_database_url_returns_none():
    assert normalize_database_url(None) is None
    assert normalize_database_url("") is None


def test_render_requires_a_database_url(monkeypatch):
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(RuntimeError, match="DATABASE_URL is required on Render"):
        create_app()
