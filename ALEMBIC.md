# Alembic Migrations

This project uses **Alembic** to manage the Postgres schema. Anyone touching
`models/*.py` or `data/models.py` needs to know this workflow — model changes
that aren't accompanied by a migration will silently drift from the real
database.

## One-time setup

1. Copy `.env.example` to `.env` and fill in your real Postgres credentials.
   **Special characters in the password must be percent-encoded** —
   `@` → `%40`, `!` → `%21`, etc. Example:

   ```env
   DATABASE_URL=postgresql+psycopg://postgres:YOURPASSWORD@localhost:5432/bank
   ```

2. Also set `JWT_SECRET_KEY` in `.env`. Generate one with:

   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(64))"
   ```

   This isn't used by Alembic directly, but importing the database module
   now goes through `core/config.py`, which raises at import time if
   `JWT_SECRET_KEY` is missing — so Alembic commands will fail to even start
   without it.

3. Make sure the database named in `DATABASE_URL` already exists in Postgres
   (Alembic manages tables inside a database, not the database itself):

   ```bash
   psql -U postgres -c "CREATE DATABASE bank;"
   ```

## Bringing your local database up to date

Whenever you pull a branch with new migrations:

```bash
alembic upgrade head
```

This applies every migration in `alembic/versions/` that you don't already
have, in order. Safe to run repeatedly — it's a no-op if you're already
current.

To check what revision your database is on:

```bash
alembic current
```

To see the full migration history:

```bash
alembic history
```

## Making a schema change

1. Edit the SQLAlchemy model(s) in `models/*.py` (these are the source of
   truth — `data/models.py` just re-exports them so `alembic/env.py` and
   `tests/conftest.py` can register every table on `Base.metadata`).
2. Generate a migration from the diff between your models and the live
   database:

   ```bash
   alembic revision --autogenerate -m "short description of the change"
   ```

3. **Open the generated file in `alembic/versions/` and read it.**
   Autogenerate is a starting point, not a guarantee — it regularly gets
   these wrong:
   - Renames show up as a `drop_column` + `add_column` pair (data loss) instead
     of `alter_column`.
   - Adding a `NOT NULL` column with no default will fail against a table
     that already has rows — add a `server_default=` for the initial backfill.
   - It sometimes tries to redeclare enum types (`sa.Enum(...)`) that already
     exist in Postgres, causing `type "..." already exists` errors. Delete the
     spurious enum lines if the type isn't new.
4. Apply it locally and confirm the app still boots:

   ```bash
   alembic upgrade head
   python -c "import main"
   ```
5. Commit the migration file alongside your model change, in the same PR.

## Rolling back

```bash
alembic downgrade -1        # undo the most recent migration
alembic downgrade <revision>  # go back to a specific revision
```

Only do this on your own local database. Never downgrade a shared/deployed
database without coordinating with the team first.

## Current migration history (as of this branch)

```
a71b0709dfcd  create users table
3c26ee5fc9f3  users id to uuid
9b5136b93b33  add accounts, transactions, and transfers
e3383055c68b  add hashed_password and is_active to users
```

Run `alembic history` for the up-to-date list — this snapshot will go stale
the moment someone adds a new migration.

## Common errors

**`ValueError: invalid interpolation syntax in '...' at position N`**
A `%` in your database password (from percent-encoding, e.g. `%40`) is being
misread by Python's `configparser`. This is already handled in
`alembic/env.py` (it escapes `%` before handing the URL to Alembic's config) —
make sure you're on the latest version of that file.

**`sqlalchemy.exc.OperationalError: ... password authentication failed`**
Your `.env`'s `DATABASE_URL` password doesn't match Postgres. Double-check
percent-encoding and that you're pointed at the right host/database.

**`Target database is not up to date` / `Multiple heads`**
Someone created a migration off an older revision than yours, so the
migration graph forked. Run `alembic heads` to see both tips, then create a
merge migration:

```bash
alembic merge -m "merge heads" <revision-1> <revision-2>
```
