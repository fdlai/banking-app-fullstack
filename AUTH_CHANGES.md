# Authentication (`back-end-authentication` branch)

This branch adds real JWT-based authentication and fixes several integration
bugs that were blocking the app from starting at all. Read this before you
pull if you're touching `routers/`, `models/`, `schemas/`, or `core/`.

## What's new

### Auth endpoints (`routers/auth.py`)

| Endpoint | Description |
| --- | --- |
| `POST /auth/register` | Public self-registration. Always creates a `customer` — the request body cannot set a role. |
| `POST /auth/login` | Returns a Bearer JWT + the user's profile. Returns the same `401` for a wrong password and an unknown email (no account-existence leak). |
| `GET /auth/me` | Returns the authenticated user, resolved from the DB via the token — not from the token's claims. |
| `POST /auth/forgot-password` | Always returns the same generic message, whether or not the email exists. If the account exists, a 15-minute password-reset token is printed to the server console (there's no email sending in this project yet — that's the local/demo stand-in). |
| `POST /auth/reset-password` | Takes `{token, new_password}` and overwrites the password. Reset tokens are purpose-scoped (`"purpose": "password_reset"`) so a leaked reset token can't be reused as a normal access token. |

Protect any endpoint with `Depends(get_current_user)` (`core/dependencies.py`) —
it validates the Bearer JWT and loads the user fresh from the DB (so a
disabled/deleted user is rejected even with a still-valid token). Use
`core/permissions.py` helpers, or the `require_role(*roles)` factory in
`core/dependencies.py`, to gate by role.

### Admin-only account controls (`routers/accounts.py`)

| Endpoint | Description |
| --- | --- |
| `PATCH /accounts/{id}/freeze` | Admin-only. Sets status to `frozen`. Rejects `closed` accounts. |
| `PATCH /accounts/{id}/unfreeze` | Admin-only. Sets status back to `active`. Rejects accounts that are `closed` or not currently `frozen`. |

### Admin-only role management (`routers/users.py`)

| Endpoint | Description |
| --- | --- |
| `PATCH /users/{id}/role` | Admin-only. Changes a user's role. Deliberately kept separate from the general `PATCH /users/{id}` profile-edit endpoint (which tellers can also call for customers) so role changes always go through an admin-only check. |

## Required `.env` variables

```env
DATABASE_URL=postgresql+psycopg://<user>:<password>@localhost:5432/<db>
JWT_SECRET_KEY=<a real random secret — the app refuses to start without one>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

If you see a `ValueError: invalid interpolation syntax` from Alembic, it's
because a `%` in your URL-encoded DB password (e.g. `%40`) confuses
`configparser`. That's already handled in `alembic/env.py` — make sure you're
on the latest version of that file.

## Integration bugs fixed on this branch

These were blocking `uvicorn main:app --reload` and `pytest` from working at
all before this branch, independent of the new auth features:

- `core/database.py` didn't exist even though `core/dependencies.py`,
  `routers/auth.py`, `data/seed.py`, and `tests/conftest.py` all imported
  from it. Added it; root `database.py` now re-exports from it so every file
  still doing `from database import ...` shares the same `Base`/engine.
- `main.py` used `CORSMiddleware` without importing it.
- `data/models.py` and `models/user.py` both defined a `User` mapped to the
  `users` table — importing both raised
  `Table 'users' is already defined for this MetaData instance`. `models/user.py`
  is now the single canonical `User` (it already matched the Alembic
  migrations — UUID primary key). `data/models.py` is now just a re-export
  hub (`Account`, `Transaction`, `Transfer`, `User`) used by
  `alembic/env.py` / `tests/conftest.py` to register every table.
- `models/user.py` gained `hashed_password` and `is_active` columns
  (migration `e3383055c68b`), and its `UserRole` now comes from the shared
  `data/enums.py` instead of three separate identical enum definitions
  across `models/user.py`, `schemas/user.py`, and `data/enums.py`.
- `core/config.py` read `SECRET_KEY` from the environment while `.env` sets
  `JWT_SECRET_KEY` — the JWT secret was silently `None`. Fixed the variable
  name and the startup guard (an unset/blank secret now raises at import
  time instead of failing later with a cryptic PyJWT error).
- `routers/auth.py`'s `register()` built `User(full_name=payload.full_name, ...)`,
  but neither `UserRegister` nor `User` has a `full_name` field, and `dob`
  was never being set (a `NOT NULL` column). Fixed to pass
  `first_name`/`last_name`/`dob`.
- `tests/conftest.py` hardcoded a test database URL with the wrong password
  and a database name (`banking_test`) that didn't exist. It now derives the
  test DB URL from your real `DATABASE_URL`, swapping in a `_test` suffix.

## Known issues not fixed here (owned by other slices)

- **`data/seed.py`** builds `Account(owner_id=..., currency=...)` and
  `Transaction(from_account_id=..., to_account_id=...)`, but the real models
  use `user_id`/`account_type`/`status` and `account_id`/`transaction_type`.
  Running `python -m data.seed` will fail with a `TypeError` once it reaches
  the account-seeding step. This is accounts/transactions-shaped, not auth.
- **`tests/test_accounts.py`** doesn't run: it depends on a `seeded_users`
  fixture that doesn't exist anywhere, and it authenticates via a fabricated
  `X-User-Id` header that the app never actually implements (real auth is
  Bearer-JWT-only, via `get_current_user`). It needs a rewrite to use real
  tokens, not just a missing fixture.
- Every user seeded before this branch (i.e. not created through
  `/auth/register`) has `hashed_password = ''` and can never log in — that
  column didn't exist until migration `e3383055c68b`. A `seed-admin@example.com`
  / `admin-dev-password` admin user was manually inserted into the local dev
  DB for testing; if you need another one, hash a real password with
  `core.security.hash_password()` and update `hashed_password` directly, or
  wait until `data/seed.py` is fixed and re-run it with `--reset`.

## Running tests

```bash
pytest tests/test_auth.py tests/test_accounts_freeze.py tests/test_users_role.py tests/test_password_reset.py -q
```

These all pass, twice in a row (no leftover-data issues — `tests/conftest.py`
rolls back each test's transaction). `tests/test_accounts.py` is excluded
above; see "Known issues" for why.

## Demo script (`/docs`)

1. `POST /auth/register` with `first_name`, `last_name`, `email`, `dob`,
   `password` (8+ characters) — `201` with an `access_token` and `user`
   (no password hash visible).
2. `POST /auth/login` with the same credentials — `200` with a fresh token.
3. Click **Authorize** at the top of `/docs`, paste the token in as
   `Bearer <token>`.
4. `GET /auth/me` — returns the same user.
5. Click **Authorize** again and clear the token.
6. Call `GET /auth/me` (or any protected endpoint) with no token —
   `401 {"detail": "Could not validate credentials"}`.
