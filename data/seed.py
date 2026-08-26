"""Load data/mock_data.py into the database.

Run against a database that has already been migrated:

    python -m alembic upgrade head
    python -m data.seed

Safe to run more than once — rows already present are left alone.

users.id is a random UUID, but mock_data still keys users by small integers
(and accounts.user_id points at those integers). `user_uuid` bridges the two:
it derives a stable UUID from the mock id, so seeding the same fixture twice
produces the same ids and tests can name a user without querying first.
"""

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from data import mock_data
from database import SessionLocal
from models.user import User, UserRole

# Arbitrary but fixed — changing it changes every seeded id.
MOCK_NAMESPACE = uuid.UUID("6f9619ff-8b86-d011-b42d-00c04fc964ff")


def user_uuid(mock_id: int) -> uuid.UUID:
    """The stable UUID for a mock_data user id."""
    return uuid.uuid5(MOCK_NAMESPACE, f"user:{mock_id}")


def seed_users(db: Session) -> tuple[int, int]:
    """Insert any mock_data user not already in the table. Returns (added, skipped)."""
    existing_ids = set(db.scalars(select(User.id)))
    existing_emails = set(db.scalars(select(User.email)))

    added = 0
    for row in mock_data.users:
        if user_uuid(row["id"]) in existing_ids or row["email"].lower() in existing_emails:
            continue
        db.add(
            User(
                id=user_uuid(row["id"]),
                role=UserRole(row["role"]),
                first_name=row["first_name"],
                last_name=row["last_name"],
                email=row["email"].lower(),
                dob=date.fromisoformat(row["dob"]),
            )
        )
        added += 1

    db.commit()
    return added, len(mock_data.users) - added


def main() -> None:
    with SessionLocal() as db:
        added, skipped = seed_users(db)
        total = len(list(db.scalars(select(User.id))))
    print(f"added {added}, skipped {skipped} (already present), {total} users total")


if __name__ == "__main__":
    main()
