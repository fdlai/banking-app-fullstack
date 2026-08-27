from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import select

from core.security import hash_password
from data.enums import UserRole
from database import SessionLocal
from models.account import Account
from models.transactions import Transaction
from models.transfers import Transfer
from models.user import User

DEMO_PASSWORD = "Customer123!"


# ---------------------------------------------------------
# DEMO USERS
# ---------------------------------------------------------

USERS = [
    {
        "role": UserRole.ADMIN,
        "first_name": "Ada",
        "last_name": "Admin",
        "email": "admin@bank.com",
        "dob": date(1982, 2, 14),
        "password": "Admin123!",
    },
    {
        "role": UserRole.TELLER,
        "first_name": "Tom",
        "last_name": "Teller",
        "email": "teller@bank.com",
        "dob": date(1990, 5, 19),
        "password": "Teller123!",
    },
    {
        "role": UserRole.CUSTOMER,
        "first_name": "Alex",
        "last_name": "Johnson",
        "email": "alex.johnson@example.com",
        "dob": date(1990, 1, 15),
        "password": DEMO_PASSWORD,
    },
    {
        "role": UserRole.CUSTOMER,
        "first_name": "Maria",
        "last_name": "Garcia",
        "email": "maria.garcia@example.com",
        "dob": date(1985, 6, 22),
        "password": DEMO_PASSWORD,
    },
    {
        "role": UserRole.CUSTOMER,
        "first_name": "Jordan",
        "last_name": "Lee",
        "email": "jordan.lee@example.com",
        "dob": date(1992, 11, 3),
        "password": DEMO_PASSWORD,
    },
    {
        "role": UserRole.CUSTOMER,
        "first_name": "Taylor",
        "last_name": "Brown",
        "email": "taylor.brown@example.com",
        "dob": date(1978, 9, 14),
        "password": DEMO_PASSWORD,
    },
    {
        "role": UserRole.CUSTOMER,
        "first_name": "Morgan",
        "last_name": "Davis",
        "email": "morgan.davis@example.com",
        "dob": date(2000, 2, 29),
        "password": DEMO_PASSWORD,
    },
    {
        "role": UserRole.CUSTOMER,
        "first_name": "Sophia",
        "last_name": "Wilson",
        "email": "sophia.wilson@example.com",
        "dob": date(1994, 4, 8),
        "password": DEMO_PASSWORD,
    },
    {
        "role": UserRole.CUSTOMER,
        "first_name": "Ethan",
        "last_name": "Martinez",
        "email": "ethan.martinez@example.com",
        "dob": date(1988, 12, 19),
        "password": DEMO_PASSWORD,
    },
    {
        "role": UserRole.CUSTOMER,
        "first_name": "Olivia",
        "last_name": "Anderson",
        "email": "olivia.anderson@example.com",
        "dob": date(1996, 7, 27),
        "password": DEMO_PASSWORD,
    },
    {
        "role": UserRole.CUSTOMER,
        "first_name": "Noah",
        "last_name": "Thomas",
        "email": "noah.thomas@example.com",
        "dob": date(1983, 3, 10),
        "password": DEMO_PASSWORD,
    },
    {
        "role": UserRole.CUSTOMER,
        "first_name": "Emma",
        "last_name": "Jackson",
        "email": "emma.jackson@example.com",
        "dob": date(1998, 10, 5),
        "password": DEMO_PASSWORD,
    },
]


# Each customer gets checking + savings.
CUSTOMER_BALANCES = {
    "alex.johnson@example.com": ("4250.75", "12600.00"),
    "maria.garcia@example.com": ("1875.20", "8400.50"),
    "jordan.lee@example.com": ("6320.40", "22500.00"),
    "taylor.brown@example.com": ("940.65", "5100.25"),
    "morgan.davis@example.com": ("3100.00", "9750.80"),
    "sophia.wilson@example.com": ("7825.15", "15400.00"),
    "ethan.martinez@example.com": ("2540.55", "6300.20"),
    "olivia.anderson@example.com": ("5190.10", "11800.75"),
    "noah.thomas@example.com": ("1335.45", "7200.00"),
    "emma.jackson@example.com": ("8910.30", "20150.90"),
}


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------


def get_or_create_user(db, data):
    existing = db.scalar(select(User).where(User.email == data["email"]))

    if existing:
        return existing

    user = User(
        role=data["role"],
        first_name=data["first_name"],
        last_name=data["last_name"],
        email=data["email"],
        dob=data["dob"],
        hashed_password=hash_password(data["password"]),
        is_active=True,
    )

    db.add(user)

    # Sends INSERT without committing the transaction.
    # This lets PostgreSQL generate the UUID so we can use user.id
    # when creating the user's accounts.
    db.flush()

    return user


def get_or_create_account(
    db,
    user,
    account_type,
    balance,
):
    existing = db.scalar(
        select(Account).where(
            Account.user_id == user.id,
            Account.account_type == account_type,
        )
    )

    if existing:
        return existing

    account = Account(
        user_id=user.id,
        account_type=account_type,
        balance=Decimal(balance),
        status="active",
    )

    db.add(account)
    db.flush()

    return account


def create_transaction_if_missing(
    db,
    account,
    transaction_type,
    amount,
    timestamp,
    description,
):
    existing = db.scalar(
        select(Transaction).where(
            Transaction.account_id == account.id,
            Transaction.description == description,
        )
    )

    if existing:
        return existing

    transaction = Transaction(
        account_id=account.id,
        transaction_type=transaction_type,
        amount=Decimal(amount),
        timestamp=timestamp,
        description=description,
    )

    db.add(transaction)

    return transaction


def create_transfer_if_missing(
    db,
    from_account,
    to_account,
    amount,
    timestamp,
):
    existing = db.scalar(
        select(Transfer).where(
            Transfer.from_account_id == from_account.id,
            Transfer.to_account_id == to_account.id,
            Transfer.amount == Decimal(amount),
            Transfer.timestamp == timestamp,
        )
    )

    if existing:
        return existing

    transfer = Transfer(
        from_account_id=from_account.id,
        to_account_id=to_account.id,
        amount=Decimal(amount),
        timestamp=timestamp,
        status="completed",
    )

    db.add(transfer)

    return transfer


# ---------------------------------------------------------
# MAIN SEED FUNCTION
# ---------------------------------------------------------


def seed_demo_data():
    db = SessionLocal()

    try:
        # -------------------------
        # USERS
        # -------------------------

        users = {}

        for data in USERS:
            user = get_or_create_user(db, data)
            users[data["email"]] = user

        db.flush()

        # -------------------------
        # ACCOUNTS
        # -------------------------

        accounts = {}

        for email, balances in CUSTOMER_BALANCES.items():
            customer = users[email]

            checking = get_or_create_account(
                db,
                customer,
                "checking",
                balances[0],
            )

            savings = get_or_create_account(
                db,
                customer,
                "savings",
                balances[1],
            )

            accounts[email] = {
                "checking": checking,
                "savings": savings,
            }

        db.flush()

        # -------------------------
        # TRANSACTIONS
        # -------------------------

        transaction_templates = [
            (
                "deposit",
                "2450.00",
                datetime(2026, 8, 1, 9, 15),
                "Payroll deposit - Demo Seed",
            ),
            (
                "withdrawal",
                "84.37",
                datetime(2026, 8, 3, 12, 30),
                "Publix groceries - Demo Seed",
            ),
            (
                "withdrawal",
                "42.18",
                datetime(2026, 8, 5, 17, 45),
                "Shell gas station - Demo Seed",
            ),
            (
                "withdrawal",
                "79.99",
                datetime(2026, 8, 8, 14, 20),
                "Amazon sunglasses - Demo Seed",
            ),
            (
                "withdrawal",
                "18.99",
                datetime(2026, 8, 10, 8, 10),
                "Netflix subscription - Demo Seed",
            ),
            (
                "withdrawal",
                "63.42",
                datetime(2026, 8, 13, 19, 5),
                "Olive Garden dinner - Demo Seed",
            ),
            (
                "withdrawal",
                "31.50",
                datetime(2026, 8, 16, 11, 40),
                "Amazon household supplies - Demo Seed",
            ),
            (
                "deposit",
                "300.00",
                datetime(2026, 8, 20, 10, 25),
                "Freelance payment - Demo Seed",
            ),
        ]

        # Give each customer realistic checking activity.
        for email in CUSTOMER_BALANCES:
            checking = accounts[email]["checking"]

            for (
                transaction_type,
                amount,
                timestamp,
                description,
            ) in transaction_templates:
                create_transaction_if_missing(
                    db,
                    checking,
                    transaction_type,
                    amount,
                    timestamp,
                    description,
                )

        # Give each customer some savings activity.
        for index, email in enumerate(CUSTOMER_BALANCES):
            savings = accounts[email]["savings"]

            create_transaction_if_missing(
                db,
                savings,
                "deposit",
                str(200 + (index * 25)),
                datetime(2026, 8, 6, 10, index),
                f"Monthly savings contribution {index + 1} - Demo Seed",
            )

        db.flush()

        # -------------------------
        # TRANSFERS
        # -------------------------

        customer_emails = list(CUSTOMER_BALANCES.keys())

        # Several transfers from checking to savings.
        for index, email in enumerate(customer_emails[:5]):
            create_transfer_if_missing(
                db,
                accounts[email]["checking"],
                accounts[email]["savings"],
                str(100 + (index * 50)),
                datetime(2026, 8, 15 + index, 13, 0),
            )

        # A couple customer-to-customer transfers.
        create_transfer_if_missing(
            db,
            accounts["alex.johnson@example.com"]["checking"],
            accounts["maria.garcia@example.com"]["checking"],
            "125.00",
            datetime(2026, 8, 22, 15, 30),
        )

        create_transfer_if_missing(
            db,
            accounts["jordan.lee@example.com"]["checking"],
            accounts["sophia.wilson@example.com"]["checking"],
            "275.00",
            datetime(2026, 8, 23, 11, 45),
        )

        # -------------------------
        # COMMIT EVERYTHING
        # -------------------------

        db.commit()

        print("Demo data seeded successfully.")
        print()
        print("Staff logins:")
        print("Admin:  admin@bank.com / Admin123!")
        print("Teller: teller@bank.com / Teller123!")
        print()
        print("Customer login:")
        print(f"alex.johnson@example.com / {DEMO_PASSWORD}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()
