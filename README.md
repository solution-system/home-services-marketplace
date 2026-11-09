# Goodhand Home Services

A learning project for coordinating local plumbing, electrical, and cleaning requests. A customer can submit a request and track it; staff can sign in, triage the queue, assign a provider, update job status, and keep internal notes.

## What works today

- Public service request form with validation and a unique reference number (FR-01, FR-02).
- Customer status lookup using the reference and email address (FR-03).
- Staff sign-in and sign-out with `admin` and `provider` roles (FR-04).
- Five failed sign-in attempts lock an account for five minutes.
- Role-based redirect after sign-in: administrators go to the queue, providers go to their jobs.
- Administrator request queue sorted newest first, with status/service filters, reference/name search, and empty states (FR-05).
- Request detail pages: administrators see any request; providers see only their own assigned jobs (FR-06).
- Administrator provider assignment and reassignment before work starts, with assignment timestamps and customer-safe activity entries (FR-07).
- Provider job list showing only requests assigned to the signed-in provider (FR-08 groundwork).
- Provider status updates: `Assigned → In Progress → Completed`, with `started_at` and `completed_at` recorded (FR-09).
- Internal notes with author, timestamp, and an optional customer-visible flag; only admins and the assigned provider can add them (FR-10).
- Friendly 403, 404, and 500 pages plus flash messages.

Not built yet: customer display of customer-visible notes, an append-only audit trail, and administrator cancellation.

## Requirements

- Python 3.10 or newer
- Git
- Zed, VS Code, or another editor

## Run locally

Run every command from the project root (the folder that contains `app/`, `migrations/`, and `requirements.txt`), not from inside `app/`.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
flask --app app:create_app db upgrade
flask --app app:create_app seed-demo --reset
flask --app app:create_app run --debug
```

Open the URL printed by Flask. The default database is SQLite at `instance/requests.db`, which is excluded from Git.

If you already created the database before this stage, `db upgrade` adds the `users` table and the provider assignment columns.

## Demo accounts

`seed-demo` creates these demo accounts:

| Role | Username | Password |
|---|---|---|
| Administrator | `admin` | `admin1234` |
| Service provider | `bilal` | `provider1234` |
| Service provider | `chloe` | `provider1234` |

It also creates six sample requests in mixed statuses so the queue and provider list are not empty.

These are intentionally public demo credentials. Treat the hosted demo as a
sandbox containing fictional data only. For a private client walkthrough,
override the passwords at seed time and share the new values privately:

```bash
SEED_ADMIN_PASSWORD='...' SEED_PROVIDER_PASSWORD='...' flask --app app:create_app seed-demo --reset
```

Rebuild the sample data at any time with `flask --app app:create_app seed-demo --reset`. This deletes existing staff accounts and requests, so never run it against a database you care about.

## Deploy for free on Render

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/solution-system/home-services-marketplace)

The app deploys as a **Render free web service** with a **Neon free Postgres**
database. That combination costs $0/month, gives you HTTPS and a custom domain,
and keeps the data when Render spins the app down.

Do **not** use Render's free Postgres: it expires 30 days after creation. Do not
use SQLite on Render: the free filesystem is ephemeral and the data disappears
on restart.

`render.yaml` defines the service, build command, start command, health check,
and environment variables. Migrations and the idempotent demo seed run at boot.

The full walkthrough is in [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md). It covers
GitHub, Neon, the Blueprint deploy, verification, updates, resetting the demo,
backups, free-tier limits, and troubleshooting.

Use `python -m pytest -q` and `flask --app app:create_app db check` before
deploying, and never publish the development `SECRET_KEY` or real customer data.

## Main routes

| Method | Path | Access | Purpose |
|---|---|---|---|
| GET | `/` | Public | Request form |
| POST | `/requests` | Public | Create a request |
| GET/POST | `/lookup` | Public | Track a request |
| GET | `/healthz` | Public | Lightweight health check for Render |
| GET/POST | `/login` | Public | Staff sign-in |
| POST | `/logout` | Staff | Sign out |
| GET | `/admin/queue` | Administrator | Request queue with filters |
| GET | `/admin/requests/<id>` | Administrator | Full request details and assignment form |
| POST | `/admin/requests/<id>/assign` | Administrator | Assign or reassign a provider |
| GET | `/provider/jobs` | Service provider | Jobs assigned to the signed-in provider |
| GET | `/provider/jobs/<id>` | Service provider | Details for an assigned job only |
| POST | `/provider/jobs/<id>/status` | Assigned provider | Move a job to its next allowed status |
| POST | `/requests/<id>/notes` | Admin or assigned provider | Add an internal note |

Unauthenticated staff pages redirect to `/login`. A signed-in user with the wrong role receives a 403 page.

## Tests

```bash
source .venv/bin/activate
python -m pytest -q
```

The tests cover sign-in success and failure, lockout and lock expiry, role protection, queue sorting/filtering/search, empty states, provider job scoping, request-detail permissions, provider assignment/reassignment rules, the provider status sequence, and note validation/permissions.

## Project layout

```
app/
  __init__.py       app factory, login setup, error pages, CLI commands
  admin.py          administrator queue
  auth.py           sign-in, sign-out, role decorator
  constants.py      categories, statuses, roles, lockout values
  extensions.py     SQLAlchemy, Migrate, LoginManager
  forms.py          request, lookup, login, and logout forms
  models.py         User, ServiceRequest, StatusEvent, Note
  notes.py          internal-note route shared by admins and providers
  provider.py       provider job list, details, and status updates
  references.py     reference-number generation
  routes.py         public request, lookup, and health-check routes
  seed.py           demo accounts and sample requests
  templates/        Jinja pages, including auth/, admin/, provider/, errors/
  static/css/       single responsive stylesheet
migrations/         Alembic migrations
tests/              pytest suite
instance/           local SQLite database (ignored by Git)
docs/               PRD, FRS, TRS, and the deployment guide
render.yaml         Render Blueprint: free web service, build, start, health check
wsgi.py             production WSGI entry point (gunicorn on Render)
```

## Current build stages

1. Requirements: `docs/PRD.md`, `docs/FRS.md`, and `docs/TRS.md`.
2. Public request submission, unique reference, and email-matched status lookup.
3. Staff authentication and role authorization.
4. Administrator queue, request details, provider assignment, and provider job list.
5. Provider status updates with timestamps.
6. Internal notes with author and optional customer visibility.
7. Free deployment on Render with Neon Postgres. **Current.**
8. Audit trail, administrator cancellation, and the portfolio case study.

## Security notes

- Accounts are created by the company; there is no self-registration.
- Passwords are stored as salted hashes using Werkzeug.
- Unknown usernames and wrong passwords show the same message to avoid account enumeration.
- Lockout is tracked per account: five failed attempts trigger a five-minute block.
- Demo credentials are intentionally public for the portfolio demo. Keep only fictional data on that site; set strong values for a private deployment.
- Use HTTPS on any hosted deployment and keep `.env` and `DATABASE_URL` out of Git.
- On Render, `SECRET_KEY` is generated and `DATABASE_URL` is stored as environment secrets in the dashboard.
- This remains a student/demo build. Rate limiting and penetration testing are deferred. Backups are manual; see the deployment guide.
