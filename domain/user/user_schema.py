from pydantic import BaseModel
from typing import Optional

class UserBase(BaseModel):
    phone: str
    name: str
    gender: Optional[str] = None
    birth_year: Optional[int] = None
    birth_month: Optional[int] = None
    birth_day: Optional[int] = None
    education: Optional[str] = None
    subscription_type: Optional[str] = "standard"

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str

class TokenData(BaseModel):
    phone: Optional[str] = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str
