from enum import Enum
from datetime import date
from pydantic import BaseModel, EmailStr

class UserRole(str, Enum):
    CUSTOMER = "customer"
    TELLER = "teller"
    ADMIN = "admin"

Class UserOut(BaseModel):
id: int
role: UserRole
first_name: str
last_name: str
email: EmailStr
dob date