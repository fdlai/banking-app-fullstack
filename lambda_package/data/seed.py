"""Seed the local database with development data.

Usage (from the repo root):
    python -m data.seed
    python -m data.seed --reset
"""

import argparse
import sys
from datetime import date
from decimal import Decimal

from sqlalchemy import select

from core.database import Base, SessionLocal, engine
from core.security import hash_password
from data.enums import UserRole
from data.models import Account, Transaction, User

USERS = [
    {
        "first_name": "Ada",
        "last_name": "Admin",
        "email": "admin@example.com",
        "dob": date(1985, 3, 12),
        "role": UserRole.ADMIN,
        "password": "admin-dev-password",
    },
    {
        "first_name": "Tess",
        "last_name": "Teller",
        "email": "teller@example.com",
        "dob": date(1992, 7, 30),
        "role": UserRole.TELLER,
        "password": "teller-dev-password",
    },
    {
        "first_name": "Alice",
        "last_name": "Nguyen",
        "email": "alice@example.com",
        "dob": date(1998, 11, 4),
        "role": UserRole.CUSTOMER,
        "password": "alice-dev-password",
    },
    {
        "first_name": "Bob",
        "last_name": "Ortiz",
        "email": "bob@example.com",
        "dob": date(1979, 1, 22),
        "role": UserRole.CUSTOMER,
        "password": "bob-dev-password",
    },
]

ACCOUNTS = [
    {"owner_email": "alice@example.com", "currency": "USD", "balance": Decimal("2500.00")},
    {"owner_email": "alice@example.com", "currency": "USD", "balance": Decimal("11000.50")},
    {"owner_email": "bob@example.com", "currency": "USD", "balance": Decimal("420.75")},
]

TRANSACTIONS = [
    {"from_index": 0, "to_index": 2, "amount": Decimal("100.00"), "description": "Rent split"},
    {"from_index": 1, "to_index": 0, "amount": Decimal("500.00"), "description": "Savings transfer"},
    {"from_index": 2, "to_index": 1, "amount": Decimal("25.25"), "description": "Lunch"},
]


def reset(session) -> None:
    """Delete rows child-first so foreign keys don't block the delete."""
    session.query(Transaction).delete()
    session.query(Account).delete()
    session.query(User).delete()
    session.commit()
    print("Cleared existing rows.")


def seed(session) -> None:
    users_by_email: dict[str, User] = {}

    for spec in USERS:
        existing = session.scalar(select(User).where(User.email == spec["email"]))
        if existing is not None:
            users_by_email[spec["email"]] = existing
            continue

        user = User(
            first_name=spec["first_name"],
            last_name=spec["last_name"],
            email=spec["email"],
            dob=spec["dob"],
            role=spec["role"],
            hashed_password=hash_password(spec["password"]),
        )
        session.add(user)
        users_by_email[spec["email"]] = user

    session.flush()

    accounts: list[Account] = []
    for spec in ACCOUNTS:
        account = Account(
            owner_id=users_by_email[spec["owner_email"]].id,
            currency=spec["currency"],
            balance=spec["balance"],
        )
        session.add(account)
        accounts.append(account)

    session.flush()

    for spec in TRANSACTIONS:
        session.add(
            Transaction(
                from_account_id=accounts[spec["from_index"]].id,
                to_account_id=accounts[spec["to_index"]].id,
                amount=spec["amount"],
                description=spec["description"],
            )
        )

    session.commit()
    print(f"Seeded {len(USERS)} users, {len(accounts)} accounts, {len(TRANSACTIONS)} transactions.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed the local database.")
    parser.add_argument("--reset", action="store_true", help="delete all rows before seeding")
    parser.add_argument("--create-tables", action="store_true", help="run create_all (skip if using Alembic)")
    args = parser.parse_args()

    if args.create_tables:
        Base.metadata.create_all(bind=engine)
        print("Tables created.")

    session = SessionLocal()
    try:
        if args.reset:
            reset(session)
        seed(session)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())