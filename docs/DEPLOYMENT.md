# Deploy Goodhand on Render (free) with Neon Postgres

This guide puts the app on a public HTTPS URL for **$0/month** using:

- **Render** free web service for the Flask app.
- **Neon** free Postgres for persistent data.

> **Terms verified 8 November 2026.** Free tiers change. Re-check
> [Render's free plan](https://render.com/docs/free) and
> [Neon's pricing](https://neon.com/pricing) before relying on them.

## Why not Render's free Postgres?

Render's free web service has an **ephemeral filesystem**. SQLite data is lost
on every restart, redeploy, or spin-down. Render's free Postgres is also a poor
fit because it **expires 30 days after creation**.

Neon's free plan is permanent, needs no credit card, and keeps the data when
the app sleeps. That is the combination this guide uses.

```text
Browser
   │ HTTPS
   ▼
Render free web service  ──►  Neon free Postgres
(Flask + gunicorn)             (persistent database)
```

## Free-tier limits

### Render free web service

- 512 MB RAM, 0.1 CPU, one instance.
- Spins down after 15 minutes without traffic; the next request takes about a
  minute to wake it.
- 750 instance hours per workspace per month.
- 5 GB outbound bandwidth per month. Without a payment method, exceeding it can
  suspend free services for the rest of the month.
- Ephemeral filesystem. The app must not store data there.
- No shell access and no one-off jobs. Migrations and seeding therefore run in
  the start command.
- Custom domains and managed HTTPS are included.
- Do **not** use Render's free Postgres: it expires after 30 days.

### Neon free Postgres

- 1 GB storage per project, 20 GB total across projects.
- 100 compute-hours per project per month.
- Scales to zero after 5 minutes idle; the next query wakes it in a few hundred
  milliseconds.
- 5 GB network transfer per project per month.
- Permanent free plan, no credit card.
- Keep the Neon project in the same region as the Render service when possible.
- Don't use an uptime pinger to keep Render awake. It burns Neon compute hours;
  the free database only has 100 CU-hours per month.

## 1. Push the project to GitHub

Render deploys from a Git repository.

```bash
cd /path/to/home-services-marketplace
git init
git add .
git commit -m "Goodhand home services marketplace"
git branch -M main
git remote add origin https://github.com/YOURNAME/home-services-marketplace.git
git push -u origin main
```

`.gitignore` excludes `.env`, `.venv/`, `instance/*.db`, and `dist/`.

Do not commit real customer data or your local `.env`.

## 2. Create the Neon database

1. Sign up at [neon.com](https://neon.com/signup). No card is required.
2. Create a project. Choose the region closest to your Render region:
   - Render `singapore` → Neon AWS `ap-southeast-1` (Singapore)
   - Render `frankfurt` → Neon AWS `eu-central-1` (Frankfurt)
   - Render `oregon` → Neon AWS `us-west-2` (Oregon)
3. Open **Connect** and enable **Pooled connection**.
4. Copy the connection string. It looks like:

```text
postgresql://user:password@ep-xxx-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
```

The `-pooler` host and `sslmode=require` are both fine. The app normalizes
legacy `postgres://` URLs automatically.

Keep this string private. It is the database password.

## 3. Deploy with the Blueprint

1. In the [Render Dashboard](https://dashboard.render.com), click **New** →
   **Blueprint**.
2. Connect GitHub and select this repository.
3. Render finds `render.yaml` and shows the `goodhand` web service.
4. It prompts for `DATABASE_URL`. Paste the Neon pooled connection string.
5. Apply the Blueprint.

The free plan is selected automatically. Render generates `SECRET_KEY` and sets
`SESSION_COOKIE_SECURE=1`.

On first boot, the start command:

```text
db upgrade  →  seed-demo (only if empty)  →  gunicorn
```

`seed-demo` is idempotent: it exits early once the demo admin exists. It does
not delete data unless you pass `--reset`.

## 4. Verify the deployment

Wait for the first deploy to finish, then open:

```text
https://goodhand.onrender.com
```

Check:

- The request form loads and the stylesheet is applied.
- Submit a request and note the reference number.
- Look it up with the same reference and email.
- Sign in as `admin` / `admin1234`.
- Assign the new request to a provider.
- Sign in as `bilal` / `provider1234`, start and complete the job.
- Add a note as the provider and confirm it appears for the admin.
- Open a missing URL and confirm the styled 404 page appears.
- Open `/healthz`; it returns `{"status":"ok"}`.

The first request after 15 minutes of inactivity takes about a minute while
Render wakes the service.

## 5. Optional custom domain

The free plan includes two custom domains. In the Render service, open
**Settings → Custom Domains**, add your domain, and create the DNS records
Render shows you. HTTPS is provisioned automatically.

## 6. Deploying updates

Push to the connected branch:

```bash
git add .
git commit -m "Describe the change"
git push
```

Render rebuilds and restarts automatically. The start command runs any new
migrations before gunicorn starts.

## 7. Reset or reseed the online demo

Free Render services have no shell, so run admin commands **from your local
machine** against the Neon database.

```bash
cd /path/to/home-services-marketplace
source .venv/bin/activate
export DATABASE_URL='postgresql://...neon.tech/neondb?sslmode=require'

flask --app app:create_app db upgrade
flask --app app:create_app seed-demo --reset

unset DATABASE_URL
```

`--reset` deletes all staff accounts and requests in that database. Run it only
against the demo database, never against real customer data.

To use different demo passwords:

```bash
SEED_ADMIN_PASSWORD='...' SEED_PROVIDER_PASSWORD='...' \
  flask --app app:create_app seed-demo --reset
```

## 8. Back up the database

From your local machine, with `pg_dump` installed:

```bash
pg_dump "$DATABASE_URL" --no-owner --no-acl -f "goodhand-$(date +%F).sql"
```

Neon's free plan includes a six-hour history window and one manual snapshot.
That is not a substitute for your own backup of anything important.

## Troubleshooting

### The deploy fails with "DATABASE_URL is required on Render"

The app refuses to start on Render without a Postgres URL, because SQLite would
lose data on the ephemeral filesystem. Add the Neon pooled connection string in
**Render → goodhand → Environment**.

### `SSL connection is required`

Add `?sslmode=require` to the end of the Neon connection string.

### `connection refused` or `password authentication failed`

Re-copy the **pooled** connection string from Neon. Check that the password was
not truncated and that the project is not suspended for exceeding its free
limits.

### Migrations fail through the pooled connection

Run migrations with Neon's **direct** (non-pooler) connection string, then switch
`DATABASE_URL` back to the pooled string. Both strings are available under
**Connect** in the Neon console.

### 502 or deploy stuck at "starting"

Open **Logs** in Render. Common causes:

- A migration failed.
- `DATABASE_URL` is wrong.
- The Neon project is unavailable.
- The start command could not find `gunicorn` (the build failed first).

### Stylesheet is missing

Flask serves `/static` itself on Render; there is no separate static mapping.
Check the deploy logs for a failed build and confirm the page's CSS URL returns
200.

### The site is slow on the first visit

Render free services spin down after 15 minutes. This is expected. The first
request after idle takes about a minute.

### The demo data disappeared

Confirm `DATABASE_URL` is set. If it is missing, the app now refuses to start on
Render instead of silently using ephemeral SQLite.

## Security notes

- The hosted demo uses public credentials so reviewers can try every role.
  Keep only fictional sample data there.
- `SECRET_KEY` is generated by Render and stored as an environment secret.
- `SESSION_COOKIE_SECURE=1` ensures the session cookie is HTTPS-only.
- Never commit `.env` or paste the Neon connection string into the repository.
- For a private client demo, change the demo passwords and share them privately.
- For real customer data, add a password-change screen, rate limiting, and
  scheduled backups before launch.

## Alternative: PythonAnywhere

PythonAnywhere's free plan also works with SQLite and has a persistent disk. It
allows only one web app and no custom domain. Render is preferred here because
it supports custom domains, but it requires the external Neon database.
