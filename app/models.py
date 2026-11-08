from datetime import datetime, timedelta, timezone

from flask import current_app
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .constants import LOCKOUT_MINUTES, MAX_FAILED_LOGIN_ATTEMPTS
from .extensions import db


def utc_now():
    return datetime.now(timezone.utc)


def as_utc(value):
    """Treat naive datetimes from SQLite as UTC so comparisons stay safe."""
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    display_name = db.Column(db.String(120), nullable=False)
    failed_login_attempts = db.Column(db.Integer, nullable=False, default=0)
    locked_until = db.Column(db.DateTime(timezone=True))
    last_login_at = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)

    assigned_requests = db.relationship(
        "ServiceRequest",
        back_populates="assigned_provider",
        foreign_keys="ServiceRequest.assigned_provider_id",
    )
    authored_notes = db.relationship(
        "Note",
        back_populates="author",
        foreign_keys="Note.author_id",
    )

    def set_password(self, password):
        method = current_app.config.get("PASSWORD_HASH_METHOD", "scrypt")
        self.password_hash = generate_password_hash(password, method=method)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def is_provider(self):
        return self.role == "provider"

    @property
    def is_locked(self):
        return self.locked_until is not None and as_utc(self.locked_until) > utc_now()

    @property
    def lock_seconds_remaining(self):
        if not self.is_locked:
            return 0
        return max(0, int((as_utc(self.locked_until) - utc_now()).total_seconds()))

    def clear_expired_lock(self):
        """Release a lock once its five-minute window has passed."""
        if self.locked_until is not None and as_utc(self.locked_until) <= utc_now():
            self.locked_until = None
            self.failed_login_attempts = 0
            return True
        return False

    def register_failed_login(self):
        self.clear_expired_lock()
        if self.is_locked:
            return
        self.failed_login_attempts = (self.failed_login_attempts or 0) + 1
        if self.failed_login_attempts >= MAX_FAILED_LOGIN_ATTEMPTS:
            self.locked_until = utc_now() + timedelta(minutes=LOCKOUT_MINUTES)

    def register_successful_login(self):
        self.failed_login_attempts = 0
        self.locked_until = None
        self.last_login_at = utc_now()

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"


class ServiceRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(16), unique=True, nullable=False, index=True)
    customer_name = db.Column(db.String(120), nullable=False)
    customer_email = db.Column(db.String(254), nullable=False, index=True)
    customer_phone = db.Column(db.String(40), nullable=False)
    category = db.Column(db.String(30), nullable=False)
    requested_date = db.Column(db.Date, nullable=False)
    service_area = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(2000), nullable=False)
    status = db.Column(db.String(30), nullable=False, default="New")
    assigned_provider_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", name="fk_service_request_assigned_provider"),
        index=True,
    )
    assigned_at = db.Column(db.DateTime(timezone=True))
    started_at = db.Column(db.DateTime(timezone=True))
    completed_at = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    assigned_provider = db.relationship(
        "User",
        back_populates="assigned_requests",
        foreign_keys=[assigned_provider_id],
    )
    events = db.relationship(
        "StatusEvent",
        back_populates="service_request",
        cascade="all, delete-orphan",
        order_by="StatusEvent.created_at",
    )
    notes = db.relationship(
        "Note",
        back_populates="service_request",
        cascade="all, delete-orphan",
        order_by="Note.created_at",
    )


class StatusEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey("service_request.id"), nullable=False, index=True)
    previous_status = db.Column(db.String(30))
    new_status = db.Column(db.String(30), nullable=False)
    public_message = db.Column(db.String(240), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)

    service_request = db.relationship("ServiceRequest", back_populates="events")


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(
        db.Integer,
        db.ForeignKey("service_request.id"),
        nullable=False,
        index=True,
    )
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    body = db.Column(db.String(500), nullable=False)
    is_customer_visible = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)

    service_request = db.relationship("ServiceRequest", back_populates="notes")
    author = db.relationship("User", back_populates="authored_notes")
