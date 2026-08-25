from enum import Enum
from datetime import date
from pydantic import BaseModel, EmailStr

class UserRole(str, Enum):
    CUSTOMER = "customer"
    TELLER = "teller"
    ADMIN = "admin"

class UserOut(BaseModel):
    id: int
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

class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None