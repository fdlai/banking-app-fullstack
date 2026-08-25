# Database setup

The `users` endpoints now read and write Postgres instead of `data/mock_data.py`.
Everyone runs their own local database — nothing is shared except the migrations.

## First-time setup

```powershell
git pull
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

On macOS/Linux use `source .venv/bin/activate` instead.

**1. Create the database.** In psql, or pgAdmin:

```sql
CREATE DATABASE bank;
```

**2. Point the app at it.** Copy `.env.example` to `.env` and put in your own
password:

```
DATABASE_URL=postgresql+psycopg://postgres:yourpassword@localhost:5432/bank
```

`.env` is gitignored — it never gets committed, and everyone's is different.
If your password has special characters they must be percent-encoded:
`@` becomes `%40`, `!` becomes `%21`, `#` becomes `%23`.

**3. Build the schema and load the fixtures:**

```powershell
python -m alembic upgrade head
python -m data.seed
```

**4. Check it worked:**

```powershell
python -m pytest -q          # expect 24 passed
python -m uvicorn main:app --reload
```

The test suite creates and uses a second database, `bank_test`, automatically.
You don't need to create it, and it never touches your `bank` data.

## Trying the API by hand

Auth is still a stand-in: send the acting user's id in the `X-User-Id` header.
Ids are UUIDs now, so print the one you want first:

```powershell
python -c "from database import SessionLocal; from models.user import User; [print(u.id, u.role.value, u.email) for u in SessionLocal().query(User).order_by(User.email)]"
```

Then at http://127.0.0.1:8000/docs, or:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/users -Headers @{"X-User-Id"="<admin-uuid>"}
```

Sarah Wilson and Michael Anderson are admins, Olivia Turner and Daniel Reyes are
tellers, everyone else is a customer.

## Day-to-day

**After every `git pull`:**

```powershell
pip install -r requirements.txt
python -m alembic upgrade head
```

If someone added a migration and you skip this, you'll get confusing errors
about missing columns.

**When you change a model** (`models/*.py`):

```powershell
git pull                                              # FIRST — see below
python -m alembic revision --autogenerate -m "what you changed"
```

Then **open the generated file in `alembic/versions/` and read it** before
running `upgrade head`. Autogenerate gets things wrong — it cannot express a
type change Postgres has no cast for, it does not always notice renames, and it
will happily generate an empty `upgrade()` if something is misconfigured. If the
body is just `pass` but you did change a model, stop and ask rather than
applying it.

**Always pull before generating a migration.** Two migrations created from the
same parent produce two heads, and `alembic upgrade head` then fails with
"Multiple head revisions". Untangling that means `alembic merge`. Pulling first
avoids it entirely.

**Never edit a migration that's already pushed.** Others may have applied it.
Write a new one.

**Adding a dependency:** `pip install X`, then add the pinned line to
`requirements.txt` by hand. Do not run `pip freeze > requirements.txt` — it
rewrites every line with your machine's transitive dependencies and conflicts
with everyone else's.

## Things that changed, and what they mean for your code

**User ids are random UUIDs, not 1, 2, 3.** `users.id` is a `UUID` column
defaulting to `gen_random_uuid()`. So:

- `X-User-Id` must be a UUID string. An integer gets a 422, not a 401.
- `/users/{user_id}` takes a UUID.
- `UserOut.id` serializes as a UUID string.

`data/mock_data.py` still keys users by small integers, and still backs the
accounts and transactions endpoints, which have not been migrated. The bridge is
`user_uuid()` in `data/seed.py`: it derives a fixed UUID from a mock id, so
`user_uuid(1)` is always Alice. Use it whenever you need to refer to a seeded
user from code or tests.

When you migrate accounts to the database, `accounts.user_id` will need
`user_uuid(row["user_id"])` to map onto the new user ids.

**Writing tests.** `tests/conftest.py` gives you two fixtures:

- `db` — a session whose writes are rolled back at the end of the test, so tests
  don't leak into each other. Use it to assert what actually landed in the
  database.
- the app is automatically pointed at that session, so `TestClient` requests go
  through it.

Assert against the database, not `mock_data.users` — the endpoints don't touch
that list anymore.

## When something breaks

**`ModuleNotFoundError: No module named 'psycopg'`** — the venv isn't active, or
you're on a different Python. Check with `python -c "import sys; print(sys.executable)"`.

**Everything returns 401** — your `users` table is empty. Run `python -m data.seed`.

**Everything returns 422** — you're sending an integer as `X-User-Id`. It needs a
UUID.

**`alembic upgrade head` prints nothing and creates no tables** — `alembic/env.py`
is missing the dispatch block at the bottom that calls `run_migrations_online()`.
It's there now; if a bad merge drops it, migrations silently do nothing.

**`Multiple head revisions`** — you and someone else branched migrations. Run
`python -m alembic heads` to see them, then `python -m alembic merge -m "merge heads" <rev1> <rev2>`.

**Reset your local database from scratch:**

```powershell
python -m alembic downgrade base
python -m alembic upgrade head
python -m data.seed
```
