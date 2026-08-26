from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from core import permissions
from core.dependencies import get_current_user
from database import get_db
from models.user import User
from models.user import UserRole as ModelRole
from repositories import user_repo
from schemas.user import UserCreate, UserOut, UserRole, UserRoleUpdate, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "",
    response_model=list[UserOut],
    responses={
        401: {"description": "Unknown or missing acting user"},
        403: {"description": "Staff access required"},
    },
)
def list_users(
    role: UserRole | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    actor: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not permissions.can_list_users(actor):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff access required",
        )

    allowed = permissions.visible_roles(actor)
    if role is not None:
        allowed = allowed & {ModelRole(role.value)}

    return user_repo.list_by_roles(db, allowed, limit, offset)


@router.get(
    "/{user_id}",
    response_model=UserOut,
    responses={
        401: {"description": "Unknown or missing acting user"},
        403: {"description": "Not permitted to view this user"},
        404: {"description": "User not found"},
    },
)
def get_user(
    user_id: UUID,
    actor: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target = user_repo.get_by_id(db, user_id)
    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {user_id}",
        )
    if not permissions.can_view_user(actor, target):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not permitted to view this user",
        )
    return target


@router.post(
    "",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"description": "Unknown or missing acting user"},
        403: {"description": "Not permitted to create this role"},
        409: {"description": "Email already registered"},
    },
)
def create_user(
    payload: UserCreate,
    actor: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target_role = ModelRole(payload.role.value)

    if not permissions.can_create_user(actor, target_role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Not permitted to create a user with role '{payload.role.value}'",
        )

    email = payload.email.lower()
    if user_repo.get_by_email(db, email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email already registered: {email}",
        )

    user = User(
        role=target_role,
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=email,
        dob=payload.dob,
    )
    user_repo.create(db, user)
    db.commit()
    db.refresh(user)
    return user


@router.patch(
    "/{user_id}",
    response_model=UserOut,
    responses={
        401: {"description": "Unknown or missing acting user"},
        403: {"description": "Not permitted to update this user"},
        404: {"description": "User not found"},
        409: {"description": "Email already registered"},
    },
)
def update_user(
    user_id: UUID,
    payload: UserUpdate,
    actor: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target = user_repo.get_by_id(db, user_id)
    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {user_id}",
        )
    if not permissions.can_update_user(actor, target):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not permitted to update this user",
        )

    changes = payload.model_dump(exclude_unset=True)

    if "email" in changes:
        new_email = changes["email"].lower()
        existing = user_repo.get_by_email(db, new_email)
        if existing is not None and existing.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email already registered: {new_email}",
            )
        changes["email"] = new_email

    for field, value in changes.items():
        setattr(target, field, value)

    db.commit()
    db.refresh(target)
    return target


@router.patch(
    "/{user_id}/role",
    response_model=UserOut,
    responses={
        401: {"description": "Unknown or missing acting user"},
        403: {"description": "Admin access required"},
        404: {"description": "User not found"},
    },
)
def update_user_role(
    user_id: UUID,
    payload: UserRoleUpdate,
    actor: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not permissions.can_update_role(actor):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    target = user_repo.get_by_id(db, user_id)
    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {user_id}",
        )

    target.role = ModelRole(payload.role.value)
    db.commit()
    db.refresh(target)
    return target


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"description": "Unknown or missing acting user"},
        403: {"description": "Admin access required"},
        404: {"description": "User not found"},
    },
)
def delete_user(
    user_id: UUID,
    actor: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not permissions.can_delete_user(actor):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    target = user_repo.get_by_id(db, user_id)
    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {user_id}",
        )

    user_repo.delete(db, target)
    db.commit()
    return None
