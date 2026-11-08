"""Production WSGI entry point.

Render runs ``gunicorn wsgi:application``; PythonAnywhere and other WSGI hosts
can import the same object. The Flask development server is never used in
production.
"""

import sys
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Flask's CLI loads .env automatically; a WSGI server does not.
load_dotenv(BASE_DIR / ".env")

from app import create_app  # noqa: E402  (import after loading .env)

application = create_app()
app = application

secret_key = application.config["SECRET_KEY"]
if secret_key in {
    "local-development-only-change-before-deploy",
    "replace-with-a-long-random-value",
}:
    raise RuntimeError(
        "SECRET_KEY is still a placeholder. "
        "Create a .env file with a long random SECRET_KEY before deploying."
    )
if len(secret_key) < 32:
    raise RuntimeError(
        "SECRET_KEY is too short. Generate at least 32 characters with: "
        'python -c "import secrets; print(secrets.token_urlsafe(48))"'
    )
