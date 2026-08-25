"""Access layer over data.mock_data.users — the shared source of truth for users.

Every read and write goes through the same list the other features import, so a
user created, updated or deleted via the users API is immediately visible to
them. Records stay plain dicts with JSON-friendly values to match the rest of
mock_data; this module converts to and from UserOut at the boundary.
"""

from data import mock_data
from schemas.user import UserOut


def _to_model(record: dict) -> UserOut:
    return UserOut(**record)


def _to_record(user: UserOut) -> dict:
    return user.model_dump(mode="json")


def _find_record(user_id: int) -> dict | None:
    for record in mock_data.users:
        if record["id"] == user_id:
            return record
    return None


def list_users() -> list[UserOut]:
    return [_to_model(record) for record in mock_data.users]


def get_user(user_id: int) -> UserOut | None:
    record = _find_record(user_id)
    return None if record is None else _to_model(record)


def email_taken(email: str, ignore_id: int | None = None) -> bool:
    """Whether the email is already registered to someone other than ignore_id."""
    email = email.lower()
    return any(
        record["email"].lower() == email and record["id"] != ignore_id
        for record in mock_data.users
    )


def next_id() -> int:
    """Return the next unused user id."""
    return max((record["id"] for record in mock_data.users), default=0) + 1


def add_user(user: UserOut) -> UserOut:
    mock_data.users.append(_to_record(user))
    return user


def update_user(user_id: int, changes: dict) -> UserOut | None:
    record = _find_record(user_id)
    if record is None:
        return None
    updated = _to_model(record).model_copy(update=changes)
    # mutate in place so anything already holding this dict sees the change
    record.update(_to_record(updated))
    return updated


def delete_user(user_id: int) -> UserOut | None:
    record = _find_record(user_id)
    if record is None:
        return None
    mock_data.users.remove(record)
    return _to_model(record)
