from fastapi import APIRouter, Depends, HTTPException, Query, status

from core import permissions
from core.dependencies import get_current_user
from data import user_store
from schemas.user import UserCreate, UserOut, UserRole, UserUpdate

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
    actor: UserOut = Depends(get_current_user),
):
    if not permissions.can_list_users(actor):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff access required",
        )

    allowed = permissions.visible_roles(actor)
    results = [u for u in user_store.list_users() if u.role in allowed]
    if role is not None:
        results = [u for u in results if u.role == role]
    return results[offset : offset + limit]


@router.get(
    "/{user_id}",
    response_model=UserOut,
    responses={
        401: {"description": "Unknown or missing acting user"},
        403: {"description": "Not permitted to view this user"},
        404: {"description": "User not found"},
    },
)
def get_user(user_id: int, actor: UserOut = Depends(get_current_user)):
    target = user_store.get_user(user_id)
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
def create_user(payload: UserCreate, actor: UserOut = Depends(get_current_user)):
    if not permissions.can_create_user(actor, payload.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Not permitted to create a user with role '{payload.role.value}'",
        )

    email = payload.email.lower()
    if user_store.email_taken(email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email already registered: {email}",
        )

    user = UserOut(
        id=user_store.next_id(),
        role=payload.role,
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=email,
        dob=payload.dob,
    )
    return user_store.add_user(user)


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
    user_id: int,
    payload: UserUpdate,
    actor: UserOut = Depends(get_current_user),
):
    target = user_store.get_user(user_id)
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

    new_email = changes.get("email")
    if new_email:
        new_email = new_email.lower()
        if user_store.email_taken(new_email, ignore_id=user_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email already registered: {new_email}",
            )
        changes["email"] = new_email

    return user_store.update_user(user_id, changes)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"description": "Unknown or missing acting user"},
        403: {"description": "Admin access required"},
        404: {"description": "User not found"},
    },
)
def delete_user(user_id: int, actor: UserOut = Depends(get_current_user)):
    if not permissions.can_delete_user(actor):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    if user_store.delete_user(user_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {user_id}",
        )
    return None