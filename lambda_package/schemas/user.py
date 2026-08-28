from datetime import date
from uuid import UUID

from pydantic import BaseModel, EmailStr

from data.enums import UserRole

__all__ = ["UserRole", "UserOut", "UserCreate", "UserUpdate", "UserRoleUpdate"]

class UserOut(BaseModel):
    id: UUID
    role: UserRole
    first_name: str
    last_name: str
    email: EmailStr
    dob: date

class UserCreate(BaseModel):
    role: UserRole = UserRole.CUSTOMER
    first_name: str
    last_name: str
    email: EmailStr
    dob: date
    password: str

class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None

class UserRoleUpdate(BaseModel):
    role: UserRole