from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from repositories import user_repo


def get_current_user(
    x_user_id: int = Header(),
    db: Session = Depends(get_db),
) -> User:
    """Stand-in for real authentication.

    Reads the acting user's id from the X-User-Id header. Replace the body
    with token decoding later — the signature and call sites stay the same.
    """
    actor = user_repo.get_by_id(db, x_user_id)
    if actor is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unknown or missing acting user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return actor