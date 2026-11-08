from datetime import datetime, timedelta, timezone

from app.extensions import db
from app.models import User

from helpers import login


def test_anonymous_user_is_sent_to_login(client):
    response = client.get("/admin/queue")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_admin_login_redirects_to_queue(client, admin):
    response = login(client, "admin", "adminpass")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/admin/queue")


def test_provider_login_redirects_to_jobs(client, provider):
    response = login(client, "provider", "providerpass")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/provider/jobs")


def test_invalid_password_shows_generic_message(client, admin):
    response = login(client, "admin", "wrong-password")
    assert response.status_code == 401
    assert b"Invalid username or password." in response.data


def test_unknown_username_shows_the_same_message(client):
    response = login(client, "does-not-exist", "whatever")
    assert response.status_code == 401
    assert b"Invalid username or password." in response.data


def test_five_failed_attempts_lock_the_account(client, admin):
    for _ in range(5):
        response = login(client, "admin", "wrong-password")

    assert response.status_code == 429
    assert b"Too many attempts. Try again later." in response.data

    # Even the correct password is refused during the lockout window.
    response = login(client, "admin", "adminpass")
    assert response.status_code == 429
    assert b"Too many attempts. Try again later." in response.data


def test_login_is_allowed_again_after_lock_expires(client, admin):
    user = db.session.get(User, admin.id)
    user.failed_login_attempts = 5
    user.locked_until = datetime.now(timezone.utc) - timedelta(seconds=1)
    db.session.commit()

    response = login(client, "admin", "adminpass")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/admin/queue")

    user = db.session.get(User, admin.id)
    assert user.failed_login_attempts == 0
    assert user.locked_until is None


def test_logout_clears_the_session(client, admin):
    login(client, "admin", "adminpass")
    response = client.post("/logout", follow_redirects=False)
    assert response.status_code == 302

    response = client.get("/admin/queue")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_provider_cannot_open_admin_queue(client, provider):
    login(client, "provider", "providerpass")
    assert client.get("/admin/queue").status_code == 403


def test_admin_cannot_open_provider_jobs(client, admin):
    login(client, "admin", "adminpass")
    assert client.get("/provider/jobs").status_code == 403
