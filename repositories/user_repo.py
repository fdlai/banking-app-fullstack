from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.user import User, UserRole


def get_by_id(db: Session, user_id: UUID) -> User | None:
    return db.get(User, user_id)


def get_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower()))


def list_by_roles(
    db: Session, roles: set[UserRole], limit: int = 50, offset: int = 0
) -> list[User]:
    if not roles:
        return []
    stmt = (
        select(User)
        .where(User.role.in_(roles))
        .order_by(User.id)
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(stmt))


def create(db: Session, user: User) -> User:
    db.add(user)
    db.flush()
    return user


def delete(db: Session, user: User) -> None:
    db.delete(user)
    db.flush()