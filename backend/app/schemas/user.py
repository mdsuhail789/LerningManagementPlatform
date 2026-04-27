from pydantic import BaseModel, EmailStr

from app.models.user import UserRole


class UserOut(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: UserRole
