from schemas.user import UserOut, UserRole

STAFF = (UserRole.TELLER, UserRole.ADMIN)


def can_list_users(actor: UserOut) -> bool:
    """Only staff may list users at all."""
    return actor.role in STAFF


def visible_roles(actor: UserOut) -> set[UserRole]:
    """Which roles this actor is allowed to see in a listing."""
    if actor.role == UserRole.ADMIN:
        return set(UserRole)
    if actor.role == UserRole.TELLER:
        return {UserRole.CUSTOMER}
    return set()


def can_view_user(actor: UserOut, target: UserOut) -> bool:
    """Anyone may view themselves; otherwise the target must be a visible role."""
    if actor.id == target.id:
        return True
    return target.role in visible_roles(actor)


def can_create_user(actor: UserOut, target_role: UserRole) -> bool:
    """Admins create anyone. Tellers create customers only — never staff."""
    if actor.role == UserRole.ADMIN:
        return True
    if actor.role == UserRole.TELLER:
        return target_role == UserRole.CUSTOMER
    return False


def can_update_user(actor: UserOut, target: UserOut) -> bool:
    """Admins edit anyone, anyone edits themselves, tellers edit customers."""
    if actor.role == UserRole.ADMIN:
        return True
    if actor.id == target.id:
        return True
    if actor.role == UserRole.TELLER:
        return target.role == UserRole.CUSTOMER
    return False


def can_delete_user(actor: UserOut) -> bool:
    """Admin only."""
    return actor.role == UserRole.ADMIN


def can_update_role(actor: UserOut) -> bool:
    """Admin only — role changes never ride along with a regular profile edit."""
    return actor.role == UserRole.ADMIN