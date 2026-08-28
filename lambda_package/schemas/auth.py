"""Request/response models for authentication.

Registration input never accepts a role — new accounts are always created as
customers, server-side. Staff roles are assigned by seeding or by an
admin-only endpoint using UserCreate.
"""

from datetime import date
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    computed_field,
    field_validator,
)

from data.enums import UserRole

MAXIMUM_AGE_YEARS = 120


class UserBase(BaseModel):
    """Fields shared by user input and output."""

    first_name: str = Field(min_length=1, max_length=60)
    last_name: str = Field(min_length=1, max_length=60)
    email: EmailStr
    dob: date

    @field_validator("first_name", "last_name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Name cannot be blank.")
        return stripped

    @field_validator("dob")
    @classmethod
    def validate_dob(cls, value: date) -> date:
        today = date.today()

        if value > today:
            raise ValueError("Date of birth cannot be in the future.")

        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))

        if age > MAXIMUM_AGE_YEARS:
            raise ValueError("Date of birth is not valid.")

        return value


class UserRegister(UserBase):
    """Public self-registration payload."""

    password: str = Field(min_length=8, max_length=72)


class UserCreate(UserBase):
    """Admin-only user creation, where the role can be chosen."""

    role: UserRole = UserRole.CUSTOMER
    password: str = Field(min_length=8, max_length=72)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=72)


class MessageResponse(BaseModel):
    message: str


class UserPublic(UserBase):
    """A user as returned by the API. Never includes the password hash."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: UserRole

    @computed_field
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class UserSummary(BaseModel):
   

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    first_name: str
    last_name: str
    email: EmailStr
    role: UserRole


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic