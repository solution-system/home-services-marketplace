# Home Services Marketplace — Technical Requirements

**Status:** Working draft based on the course brief and learner-approved Flask direction  
**Version:** 0.1  
**Traceability:** PRD `docs/PRD.md`; FRS `docs/FRS.md`

## Architecture

- Python Flask application using an application factory and separate route modules for public, authentication, administrator, and provider flows.
- Jinja templates with a small responsive CSS layer; no client-side framework required for the MVP.
- SQLAlchemy models and migrations. SQLite is the local learning database; PostgreSQL is the production database.
- Flask-Login manages staff sessions. Flask-WTF provides CSRF protection and form handling. Use Werkzeug's password-hashing helpers; never store plain-text passwords.
- Server-side authorization is the source of truth. Hiding a button in HTML is not authorization.

## Data model

### User

`id`, `email` (unique), `password_hash`, `role` (`admin` or `provider`), `active`, `created_at`.

### ServiceRequest

`id`, `reference` (unique and unguessable), customer name/email/phone, category, requested date, service area, description, status, optional `provider_id`, created and updated timestamps.

### StatusEvent

`id`, `request_id`, previous status, new status, actor user ID (nullable for initial customer submission), public message, created timestamp.

### InternalNote

`id`, `request_id`, `author_id`, body, created timestamp. Never return this entity to public lookup routes.

## Data and validation rules

- Validate all untrusted values on the server; apply reasonable maximum lengths and trim surrounding whitespace.
- Enforce unique request references and staff email addresses in the database.
- Generate references with Python's `secrets` module; do not expose sequential database IDs.
- Use parameterized ORM queries. Do not build SQL by concatenating user input.
- Store timestamps in UTC and format them for display at the boundary.
- Treat customer contact details as private. Avoid logging passwords, full form payloads, or lookup credentials.

## Security and reliability

- Read `SECRET_KEY` and production `DATABASE_URL` from environment variables. Do not commit secrets.
- Set secure cookie options in production and enable CSRF protection on state-changing forms.
- Require authentication and a server-side role check on every staff route. Providers can access only their assigned requests.
- Return the same public response for an unknown reference and an email mismatch.
- Use generic production error pages; keep diagnostic stack traces out of public responses.
- Keep the deployment reversible and keep a database backup before schema changes.

## Environments and deployment

- Local: Python virtual environment, Flask development server, SQLite database ignored by Git.
- Production: supported Python runtime, WSGI server, PostgreSQL, HTTPS, environment-based configuration, and deployment logs that exclude personal data and secrets.
- Deployment host will be selected after the first local workflow works; check current pricing and sleep/usage limits before publishing.

## Quality gates

- Verify each FRS acceptance scenario manually during learning and later automate the important flows.
- Confirm unauthorized admin/provider operations fail on the server.
- Confirm the public lookup never returns email, phone, description, or internal notes beyond the intended public status summary.
- Before portfolio deployment, document setup, demo accounts, environment variables, limitations, and the 60-second walkthrough in the README.
