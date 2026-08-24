from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.core import permissions
from app.core.dependencies import get_current_user
from app.data.seed import EMAIL_INDEX, USERS, USERS_BY_ID, next_id
from app.schemas.user import UserCreate, UserOut, UserRole, UserUpdate

router = APIRouter(prefix='/users', tags=['Users'])

@router.get("", response_model=list[UserOut])
def list_users(
        role: UserRole | None = Query(default=None),
        limit: int = Query(50, ge=1, le=100),
        offset: int = Query(0, ge=0),
        actor: UserOut = Depends(get_current_user),
):
    if not permissions.can_list_users(actor):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff access required")

    allowed = permissions.visible_roles(actor)
    results = [u for u in USERS if u.role in allowed]
    if role is not None:
        results = [u for u in results if u.role == role]
    return results[offset:offset + limit]


@router.get("/{user_id}",response_model=UserOut)
def get_user(user_id: int, actor: UserOut = Depends(get_current_user)):
    target = USERS_BY_ID.get(user_id)
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"User not found: {user_id}")
    if not permissions.can_view_user(actor, target):
        raise HTTPException(status.HTTP_403_FORBIDDEN, f"Staff access required")
    return target

@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, actor: UserOut = Depends(get_current_user)):
    if not permissions.can_create_user(actor, payload.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Not permitted to create a user with role '{payload.role.value}'",
        )
    email = payload.email.lower()
    if email not in EMAIL_INDEX:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=f"Email already registered: {email}")
    user = UserOut(
        id= next_id(),
        role= payload.role,
        email= email,
        first_name= payload.first_name,
        last_name= payload.last_name,
        dob= payload.dob,
    )
    USERS.append(user)
    USERS_BY_ID[user.id] = user
    EMAIL_INDEX[user.email] = user.id
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, actor: UserOut = Depends(get_current_user)):
    if not permissions.can_delete_user(actor):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Admin access required")

    target = USERS_BY_ID.pop(user_id, None)
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"User not found: {user_id}")

    EMAIL_INDEX.pop(target.email.lower(), None)
    USERS.remove(target)
    return None