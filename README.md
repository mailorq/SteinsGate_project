# Steins;Gate Fan Platform

A single-title streaming-style web application dedicated to Steins;Gate: watch both seasons and the movie, register an account, manage a profile, rate titles and discuss them in comments.

The project is a portfolio work demonstrating a production-shaped full-stack setup: a typed SPA frontend, a Django API backend with a service layer, and a containerized deployment behind nginx with Redis-backed rate limiting and caching.

## Architecture

```
browser
   |
   v
nginx (frontend container, :4173)
   |                security headers + CSP, rate limit on /admin/
   |-- /            SPA static (React build)
   |-- /assets/     hashed bundles, cached immutable
   |-- /img/        posters and backgrounds (WebP)
   |-- /static/     Django admin static (shared volume)
   |-- /media/      user uploads (shared volume)
   |-- /api/   -----> backend (gunicorn, :8000)
   |-- /admin/ -----> backend (gunicorn, :8000)
                          |            |
                          v            v
                    PostgreSQL 16   Redis 7
                                    (throttling, IP lockout,
                                     aggregate cache)
```

- `frontend/` — React SPA. Pages, routing and UI state. API types are generated from the backend OpenAPI schema, so the contract is compile-checked.
- `backend/` — Django + django-ninja. Domain apps with a service layer; HTTP endpoints are thin wrappers over services.
- `compose.yaml` — four services: `db`, `redis`, `backend`, `frontend`.

## Tech stack

| Layer      | Technology |
|------------|------------|
| Frontend   | React 19, TypeScript (strict), Vite, Tailwind CSS 4, React Router 7, TanStack Query |
| Backend    | Python 3.14, Django 6, django-ninja, gunicorn |
| Storage    | PostgreSQL 16 (SQLite for local development), Redis 7 |
| Infra      | Docker, docker compose, nginx |
| Quality    | ruff, ESLint, GitHub Actions CI, Django test suite |

## API

Interactive documentation: `/api/docs` (OpenAPI schema at `/api/openapi.json`).

| Method     | Path | Auth |
|------------|-------------------------------|---------|
| GET        | `/api/anime`                  | public  |
| GET        | `/api/anime/{slug}`           | public  |
| POST       | `/api/anime/{slug}/view`      | public, CSRF |
| POST       | `/api/anime/{slug}/rating`    | session |
| GET, POST  | `/api/anime/{slug}/comments`  | POST: session |
| POST       | `/api/comments/{id}/reaction` | session |
| GET, PUT   | `/api/anime/{slug}/progress`  | session |
| POST       | `/api/auth/register`, `/resend-verification`, `/verify-email`, `/login`, `/logout` | — |
| GET        | `/api/auth/session`, `/api/auth/csrf` | public |
| PATCH      | `/api/profile`; POST `/api/profile/avatar` | session |

Frontend types are regenerated with `npm run gen:api` after the schema changes.

## Security

**Authentication and sessions**

- Session authentication with HttpOnly cookies. django-ninja enforces CSRF inside cookie auth, so every session-protected mutation is covered automatically; `register`, `login` and `verify-email` carry no cookie auth and therefore call `check_csrf` explicitly.
- Registration creates an inactive user; the account activates only after a 6-digit email code (15-minute TTL, attempt limit, constant-time comparison). The database stores an HMAC hash and a nonce, never the plaintext code. SMTP is dispatched only after the registration transaction; a timeout keeps the pending account intact because the original letter may still have arrived. The client receives `202` when delivery cannot be confirmed and can use the CSRF-protected resend endpoint. A valid code is resent unchanged, so a failed resend cannot invalidate a code that already works.
- An unverified registration whose code has expired releases its username and address, so a third party cannot squat someone else's email. Disabled accounts are never touched by that cleanup. A recipient-scoped, HMAC-keyed quota allows at most six delivery attempts per hour across registration replacement and resend. Run `python manage.py purge_expired_registrations` periodically to remove old pending records and expired quota entries.
- Rotating `SECRET_KEY` intentionally invalidates pending verification codes (as well as Django sessions); affected users can request a fresh code.
- `User.email` is unique through a partial case-insensitive index, which closes the race between two concurrent sign-ups.

**Abuse control**

- Client IP is read from the trusted right-hand side of `X-Forwarded-For`, matching how django-ninja resolves it. Values a client prepends to the header are ignored, so IP lockout cannot be bypassed by spoofing. Production has two trusted hops (host TLS proxy and compose nginx); the host proxy must replace, not append, the client-supplied forwarding headers.
- Two-level rate limiting per endpoint group (burst + sustained window), counters shared across workers via Redis.
- IP lockout on credential and code entry: 5 consecutive failures block for 30 seconds, escalating series block for 10 minutes; a successful attempt resets the counter.
- The Django admin login is outside the application lockout, so nginx rate-limits `/admin/` at the edge.
- Read and ordinary write throttles degrade fail-open so a transient cache outage does not take the site down. Registration, login, email-code verification and resend are different: if their shared throttle storage is unavailable, they fail closed with a controlled `503`; database attempt/resend limits remain a second line of defence.

**Input and uploads**

- Comment spam filter, request body limits, explicit Pydantic schemas on every route (no auto-binding, so mass assignment is not possible).
- Avatars are validated by decoding the image, not by trusting the extension; the previous file is deleted on replacement so repeated uploads cannot fill the disk.

**Configuration and perimeter**

- `DEBUG` defaults to `False`, and an empty `SECRET_KEY` with `DEBUG=False` aborts startup instead of silently falling back to a key from the repository.
- `HTTPS_ENABLED` switches the https redirect, Secure cookies and HSTS as one unit. Production requires it and binds the application to loopback only; a host TLS proxy is the sole public entry point and must overwrite the forwarding headers it receives from clients.
- A failing SMTP server returns a controlled `202` with a pending registration instead of an unhandled `500`; no user is deleted after an ambiguous timeout. `EMAIL_TIMEOUT` bounds how long a request can wait on the mail server. The result only confirms acceptance by the configured mail backend, not final inbox delivery.
- Both the docs UI and the schema itself are served only when `API_DOCS_ENABLED` is on (default: `DEBUG`) — hiding `/api/docs` alone would leave `/api/openapi.json` readable.
- Containers run with `no-new-privileges`; the backend and the nginx image drop all capabilities and run as non-root users.
- nginx sends `nosniff`, `Referrer-Policy`, `X-Frame-Options` and `Permissions-Policy` on everything it serves, a CSP for the SPA, and an isolating `default-src 'none'; sandbox` policy for user uploads. `server_tokens` is off. Headers are set only where nginx serves the response — `/api/` and `/admin/` keep the ones Django's `SecurityMiddleware` produces, so nothing is duplicated.

## Caching and logging

Redis caches hot aggregates: average rating (invalidated on new votes), view counters and the title list (TTL). A title-view event is an explicit CSRF-protected `POST`; Redis provides only a short cross-worker mutex, while the database remains the source of truth for the 24-hour deduplication window. Personalized data is never cached.

Logs are split by purpose in `backend/logs/` (rotating files): `access.log` (HTTP), `application.log` (domain events), `security.log` (lockouts, CSRF, spam), `error.log` (errors only), `worker.log` (gunicorn lifecycle).

## Repository layout

```
.
├── backend/
│   ├── config/          # settings, urls, api root, throttling, logging
│   ├── accounts/        # auth, email verification, profiles, IP lockout
│   ├── catalog/         # titles, ratings, view history, aggregate cache
│   ├── comments/        # comments, reactions, spam filter
│   ├── watch/           # watch progress
│   └── Dockerfile       # python 3.14-slim, non-root, gunicorn
├── frontend/
│   ├── src/
│   │   ├── app/         # router, layout
│   │   ├── pages/       # route components
│   │   ├── features/    # player, comments, rating, watch, avatar crop
│   │   └── shared/      # api client + generated types, session, ui kit
│   ├── nginx/           # server config + shared security-headers.conf
│   └── Dockerfile       # node build stage -> nginx
├── scripts/             # projectctl: guided setup and stack control
├── .claude/skills/      # security checklists used when auditing the project
├── compose.yaml         # production-shaped stack
├── compose.dev.yaml     # dev override: vite HMR + runserver, host-mounted code
├── compose.demo.yaml    # demo override: frontend published on loopback only
└── .env.example
```

## Getting started

### Environment

Copy `.env.example` to `.env` in the repository root and fill in the values. Generate the secret key with:

```
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

With `DEBUG=False`, empty `SECRET_KEY` or `EMAIL_DELIVERY_QUOTA_SECRET` stops the application on startup. The latter is a separate stable HMAC key for the recipient send budget and must not rotate with Django's session key. There is no placeholder key in the repository at all: under `DEBUG=True` a random `SECRET_KEY` is generated once into `backend/.dev-secret-key` (git-ignored, owner-only `0600` on Unix), so a forgotten `.env` can never fall back to a value an attacker already knows.

Keep the secret URL-safe. `docker compose` treats `$` as variable interpolation, so a `$` inside `SECRET_KEY` silently changes the value the container receives and breaks sessions and CSRF.

| Variable | Purpose |
|----------|---------|
| `SECRET_KEY` | Django secret key; required whenever `DEBUG=False`, startup fails without it |
| `EMAIL_DELIVERY_QUOTA_SECRET` | Stable HMAC key for the per-recipient delivery budget; required whenever `DEBUG=False`; do not change it during normal `SECRET_KEY` rotation |
| `DEBUG` | `True`/`False`, defaults to `False`; controls Django diagnostics but does not disable email delivery |
| `ALLOWED_HOSTS` | Comma-separated host list |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated origins for production |
| `APP_PORT` | Loopback-only host port for the frontend; use a different value when another project uses `4173` |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | Database connection |
| `REDIS_URL` | Optional; set by compose in Docker, in-process memory is used without it |
| `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | Gmail SMTP credentials (an App Password is required); used in every mode |
| `HTTPS_ENABLED` | Switches https redirect, Secure cookies and HSTS together; required in production, where a host TLS proxy handles the certificate and HSTS |
| `API_DOCS_ENABLED` | Serve `/api/docs` and the OpenAPI schema; defaults to `DEBUG` |

| `NINJA_NUM_PROXIES` | Trusted proxy hops in front of Django; `1` in demo, `2` in production (host TLS proxy plus compose nginx) |
| `SESSION_COOKIE_AGE` | Session lifetime in seconds (default 14 days) |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_SSL`, `EMAIL_TIMEOUT` | SMTP transport; defaults target Gmail over SSL with a 10s timeout |
| `API_AUTH_THROTTLE`, `API_AUTH_THROTTLE_SUSTAINED`, `API_RESEND_THROTTLE`, `API_WRITE_THROTTLE`, `API_WRITE_THROTTLE_SUSTAINED`, `API_VIEW_THROTTLE`, `API_VIEW_THROTTLE_SUSTAINED` | Rate limit overrides |

If migration `0011_emaildeliveryquota` was already deployed before this separate setting existed, set `EMAIL_DELIVERY_QUOTA_SECRET` to the **current** `SECRET_KEY` for the first upgraded deploy, then keep it unchanged. This preserves the active one-hour quota without revealing either value; `projectctl.py init` performs this one-time compatibility step for an existing valid `.env`.

### Run with Docker safely

`scripts/projectctl.py` prepares `.env`, validates the host and brings the stack
up under a fixed Compose project name, so other Docker projects on the machine
are untouched. It generates secrets, refuses to start on a misconfigured
environment (occupied port, `DEBUG=True` on a public interface, a `$` inside a
secret that Compose would silently mangle) and waits for a real HTTP 200 before
reporting success.

```
python scripts/projectctl.py init
# Fill EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in .env.
python scripts/projectctl.py validate
python scripts/projectctl.py up
```

See [scripts/README.md](scripts/README.md) for modes, ownership checks and the
full command reference. The application is available at `http://localhost:4173`;
migrations, title seeding and `collectstatic` run automatically on backend start.

### Public production proxy

The Compose port is intentionally bound only to `127.0.0.1`. For a public
deployment, put it behind the host's existing TLS reverse proxy; do not change
the Compose binding to `0.0.0.0`. Inside the proxy's `listen 443 ssl` server,
the location should follow this trust boundary:

```nginx
location / {
    proxy_pass http://127.0.0.1:4173;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $remote_addr;
    proxy_set_header X-Forwarded-Proto https;
}

add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

The proxy must own the certificate and redirect HTTP to HTTPS. Assigning
`X-Forwarded-For` from `$remote_addr` (rather than appending a client header)
prevents clients from forging their apparent address or scheme.

### Development mode with hot reload

For an isolated local workstation only (this direct Compose command deliberately
bypasses `projectctl` ownership and shared-host safety checks):

```
docker compose -f compose.yaml -f compose.dev.yaml up
```

Source directories are mounted from the host: vite serves the SPA with HMR at `http://localhost:5173`, Django restarts on backend changes. No image rebuilds needed while coding.

### Run locally without Docker

Backend: `cd backend`, create a venv, `pip install -r requirements.txt`, `python manage.py migrate`, `python manage.py runserver`. Frontend: `cd frontend`, `npm install`, `npm run dev` — vite proxies `/api` and `/media` to `127.0.0.1:8000`.

For a production-like scheduler, run `python manage.py purge_expired_registrations` daily. It deletes only inactive users with an expired verification record and expired delivery-quota entries; `--dry-run` previews one batch without changing data.

## Testing and linting

```
cd backend
python manage.py test        # service, API, lockout, cache and N+1 regression tests
ruff check .

cd frontend
npm run lint
npm run build                # strict type check + production build
```

The production configuration profile is verified separately, the same way CI does it:

```
cd backend
DEBUG=False SECRET_KEY=... EMAIL_DELIVERY_QUOTA_SECRET=... ALLOWED_HOSTS=example.com python manage.py check --deploy --fail-level WARNING
```

CI runs five jobs on every push to `main`/`dev` and on every pull request: backend tests, the deployment checklist above, the frontend build, `nginx -t` against the real perimeter config, and a Gitleaks scan of the full history.

## Roadmap

- [x] SPA frontend with generated API types, session auth, comments, ratings, watch progress.
- [x] django-ninja API over a service layer, domain app split.
- [x] Redis: two-level throttling, IP lockout, aggregate caching, fail-open degradation.
- [x] Structured logging, avatar cropping, responsive header, dev compose with HMR.
- [x] Application security pass: client-IP trust model, CSRF on unauthenticated routes, upload validation, edge headers and CSP, secret scanning in CI.
- [x] Production perimeter: loopback-only application port and documented TLS reverse-proxy trust boundary.
- [ ] Catalog content served from the database instead of the frontend config.
- [ ] Load testing and measured performance tuning (indexes, microcache).

## Author

- [mailor](https://github.com/mailorq) — fullstack
