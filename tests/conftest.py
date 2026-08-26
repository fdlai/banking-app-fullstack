"""Test database setup.

The application endpoints read and write Postgres, so the suite needs a
database of its own. This builds `<db>_test` alongside the real one, and gives
each test a session wrapped in a transaction that is rolled back afterwards.

Test data is created by reusable fixtures inside that transaction, so the
suite depends on no ambient database state and leaves none behind.
"""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from config import settings
from database import Base, get_db
from main import app
from models.account import Account
from models.user import User, UserRole

TEST_URL = make_url(settings.database_url).set(
    database=make_url(settings.database_url).database + "_test"
)


def _create_test_database() -> None:
    """CREATE DATABASE if it isn't there yet — needs a connection to another db."""
    admin_url = TEST_URL.set(database="postgres")
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        exists = conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": TEST_URL.database},
        )
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{TEST_URL.database}"'))
    admin_engine.dispose()


@pytest.fixture(scope="session")
def engine():
    _create_test_database()
    engine = create_engine(TEST_URL)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db(engine):
    """A session whose writes are discarded when the test ends.

    The outer transaction is never committed; `create_savepoint` turns the
    endpoints' own db.commit() calls into savepoint releases inside it.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
        expire_on_commit=False,
    )
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(autouse=True)
def override_get_db(db):
    """Point the app at the test session for the duration of each test."""
    app.dependency_overrides[get_db] = lambda: db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def seeded_users(db):
    """One user per role, plus a second customer for the IDOR checks.

    Returns a dict keyed by role name; `customer` and `other_customer` are two
    distinct customers so "may not view another customer" can be exercised.
    """
    users = {
        "admin": User(
            role=UserRole.ADMIN,
            first_name="Ada",
            last_name="Admin",
            email="ada.admin@bank.com",
            dob=date(1982, 2, 14),
        ),
        "teller": User(
            role=UserRole.TELLER,
            first_name="Tom",
            last_name="Teller",
            email="tom.teller@bank.com",
            dob=date(1990, 5, 19),
        ),
        "customer": User(
            role=UserRole.CUSTOMER,
            first_name="Cara",
            last_name="Customer",
            email="cara.customer@example.com",
            dob=date(1988, 3, 12),
        ),
        "other_customer": User(
            role=UserRole.CUSTOMER,
            first_name="Otto",
            last_name="Other",
            email="otto.other@example.com",
            dob=date(1979, 11, 2),
        ),
    }

    db.add_all(users.values())
    db.commit()

    for user in users.values():
        db.refresh(user)

    return users


# first account
@pytest.fixture
def active_account(db, seeded_users):
    customer = seeded_users["customer"]

    account = Account(
        user_id=customer.id,
        account_type="checking",
        balance=Decimal("1000.00"),
        status="active",
    )

    db.add(account)
    db.commit()
    db.refresh(account)

    return account


# second account
@pytest.fixture
def second_active_account(db, seeded_users):
    customer = seeded_users["customer"]

    account = Account(
        user_id=customer.id,
        account_type="savings",
        balance=Decimal("500.00"),
        status="active",
    )

    db.add(account)
    db.commit()
    db.refresh(account)

    return account


@pytest.fixture
def frozen_account(db, seeded_users):
    customer = seeded_users["customer"]

    account = Account(
        user_id=customer.id,
        account_type="checking",
        balance=Decimal("1000.00"),
        status="frozen",
    )

    db.add(account)
    db.commit()
    db.refresh(account)

    return account