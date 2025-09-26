from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime

class AdminData(BaseModel):
    id: str
    name: str
    email: EmailStr
    created_at: datetime
    updated_at: datetime

class CreateAdminRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

class UpdateAdminRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if v is not None:
            if len(v) < 6:
                raise ValueError('Password must be at least 6 characters long')
        return v

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class AdminResponse(BaseModel):
    success: bool
    message: str
    data: AdminData

class AdminListResponse(BaseModel):
    success: bool
    message: str
    data: List[AdminData]
    total: int
    page: int
    pages: int

class LoginResponse(BaseModel):
    success: bool
    message: str
    data: dict

class SuccessResponse(BaseModel):
    success: bool
    message: str