from datetime import date, datetime, timezone

import pytest

from app import create_app
from app.extensions import db
from app.models import ServiceRequest, User


@pytest.fixture
def app(tmp_path):
    application = create_app(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "SECRET_KEY": "test-secret-key",
            "SQLALCHEMY_DATABASE_URI": "sqlite:///" + str(tmp_path / "test.db"),
            "PASSWORD_HASH_METHOD": "pbkdf2:sha256:1000",
        }
    )

    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def admin(app):
    user = User(username="admin", display_name="Admin User", role="admin")
    user.set_password("adminpass")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def provider(app):
    user = User(username="provider", display_name="Provider One", role="provider")
    user.set_password("providerpass")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def other_provider(app):
    user = User(username="other", display_name="Provider Two", role="provider")
    user.set_password("otherpass")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def make_request(app):
    def _make(reference="REF00001", **overrides):
        data = {
            "reference": reference,
            "customer_name": "Test Customer",
            "customer_email": "customer@example.com",
            "customer_phone": "03001234567",
            "category": "plumbing",
            "requested_date": date.today(),
            "service_area": "Test Area",
            "description": "A test request description.",
            "status": "New",
            "created_at": datetime.now(timezone.utc),
        }
        data.update(overrides)
        request = ServiceRequest(**data)
        db.session.add(request)
        db.session.commit()
        return request

    return _make
