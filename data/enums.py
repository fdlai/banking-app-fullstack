"""Shared enumerations used by both the ORM models and the API schemas."""

from enum import Enum


class UserRole(str, Enum):
    """Roles a user account can hold."""

    CUSTOMER = "customer"
    TELLER = "teller"
    ADMIN = "admin"