from fastapi import Header, HTTPException, status

from data import user_store
from schemas.user import UserOut


def get_current_user(x_user_id: int = Header()) -> UserOut:
    """Stand-in for real authentication.

    Reads the acting user's id from the X-User-Id header. Replace the body
    with token decoding later — the signature and call sites stay the same.
    """
    actor = user_store.get_user(x_user_id)
    if actor is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unknown or missing acting user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return actor