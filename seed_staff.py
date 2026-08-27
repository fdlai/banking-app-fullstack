from datetime import date

from sqlalchemy import select

from core.security import hash_password  # use whatever Luis named this
from database import SessionLocal
from models.user import User, UserRole

STAFF_USERS = [
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
]


def seed_staff():
    db = SessionLocal()

    try:
        for data in STAFF_USERS:
            existing = db.scalar(select(User).where(User.email == data["email"]))

            if existing:
                continue

            user = User(
                role=data["role"],
                first_name=data["first_name"],
                last_name=data["last_name"],
                email=data["email"],
                dob=data["dob"],
                hashed_password=hash_password(data["password"]),
            )

            db.add(user)

        db.commit()

    finally:
        db.close()


if __name__ == "__main__":
    seed_staff()
