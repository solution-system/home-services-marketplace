from functools import wraps
from urllib.parse import urlsplit

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from .extensions import db
from .forms import LoginForm, LogoutForm
from .models import User


auth = Blueprint("auth", __name__)


def dashboard_endpoint(user):
    return "admin.queue" if user.is_admin else "provider.jobs"


def is_safe_next_url(target):
    """Only allow redirects back to a path on this site."""
    if not target or not target.startswith("/"):
        return False
    parsed = urlsplit(target)
    return not parsed.scheme and not parsed.netloc


def roles_required(*roles):
    """Require a signed-in user with one of the given roles."""

    def decorator(view):
        @login_required
        @wraps(view)
        def wrapped(*args, **kwargs):
            if current_user.role not in roles:
                abort(403, description="You do not have permission to view this page.")
            return view(*args, **kwargs)

        return wrapped

    return decorator


@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for(dashboard_endpoint(current_user)))

    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        password = form.password.data
        user = User.query.filter(db.func.lower(User.username) == username.lower()).first()

        if user is not None and user.is_locked:
            flash("Too many attempts. Try again later.", "error")
            return render_template("auth/login.html", form=form), 429

        if user is not None and user.clear_expired_lock():
            db.session.commit()

        if user is not None and user.check_password(password):
            user.register_successful_login()
            db.session.commit()
            login_user(user)
            flash(f"Signed in as {user.display_name}.", "success")

            next_url = request.args.get("next")
            if is_safe_next_url(next_url):
                return redirect(next_url)
            return redirect(url_for(dashboard_endpoint(user)))

        if user is not None:
            user.register_failed_login()
            db.session.commit()
            if user.is_locked:
                flash("Too many attempts. Try again later.", "error")
                return render_template("auth/login.html", form=form), 429

        # The same message is shown for an unknown username and a wrong password.
        flash("Invalid username or password.", "error")
        return render_template("auth/login.html", form=form), 401

    return render_template("auth/login.html", form=form)


@auth.route("/logout", methods=["POST"])
@login_required
def logout():
    form = LogoutForm()
    if not form.validate_on_submit():
        abort(400)
    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("public.home"))
