from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    student_id: str
    name: str
    email: Optional[str] = None
    role: str = "student"
    department: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    student_id: Optional[str] = None
    role: Optional[str] = None


class LoginForm(BaseModel):
    student_id: str
    password: str
