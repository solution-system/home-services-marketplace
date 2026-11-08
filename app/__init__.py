import os
from pathlib import Path

import click
from flask import Flask, render_template

from .config import Config
from .constants import CATEGORY_LABELS, STATUSES
from .extensions import db, login_manager, migrate


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    # Render's free web service has an ephemeral filesystem. Falling back to
    # SQLite there would silently lose every request on restart or redeploy.
    if (
        os.environ.get("RENDER", "").lower() == "true"
        and not os.environ.get("DATABASE_URL", "").strip()
    ):
        raise RuntimeError(
            "DATABASE_URL is required on Render. Free Render services have an "
            "ephemeral filesystem, so SQLite data would be lost on restart. "
            "Create a free Neon Postgres database and add its pooled connection "
            "string as DATABASE_URL in the Render dashboard."
        )

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please sign in to continue."
    login_manager.login_message_category = "error"

    @login_manager.user_loader
    def load_user(user_id):
        from .models import User

        if not user_id or not str(user_id).isdigit():
            return None
        return db.session.get(User, int(user_id))

    from . import models  # noqa: F401 - registers models with SQLAlchemy metadata
    from .admin import admin
    from .auth import auth
    from .forms import LogoutForm
    from .notes import notes
    from .provider import provider
    from .routes import public

    app.register_blueprint(public)
    app.register_blueprint(auth)
    app.register_blueprint(admin)
    app.register_blueprint(provider)
    app.register_blueprint(notes)

    @app.context_processor
    def inject_navigation():
        return {
            "logout_form": LogoutForm(),
            "category_labels": CATEGORY_LABELS,
            "statuses": STATUSES,
        }

    @app.errorhandler(403)
    def forbidden(error):
        return (
            render_template(
                "errors/403.html",
                description=getattr(error, "description", None),
            ),
            403,
        )

    @app.errorhandler(404)
    def not_found(error):
        description = getattr(error, "description", None)
        if description and "requested URL was not found" in description:
            description = None
        return render_template("errors/404.html", description=description), 404

    @app.errorhandler(500)
    def server_error(error):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    @app.cli.command("seed-demo")
    @click.option("--reset", is_flag=True, help="Delete existing staff and requests before seeding.")
    def seed_demo(reset):
        """Create demo staff accounts and sample requests."""
        from .seed import seed_demo_data

        click.echo(seed_demo_data(reset=reset))

    return app
