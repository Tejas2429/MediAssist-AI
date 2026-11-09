from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"

class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: Optional[str] = "clinician"
    department: Optional[str] = "General / Triage"

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    department: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

Token.model_rebuild()

