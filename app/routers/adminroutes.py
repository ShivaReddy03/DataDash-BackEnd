from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from ..services.adminservice import AdminService
from ..models.adminmodels import (
    CreateAdminRequest, 
    UpdateAdminRequest, 
    AdminResponse, 
    AdminListResponse,
    LoginRequest, 
    LoginResponse,
    SuccessResponse
)
import jwt
import os

router = APIRouter(prefix="/admin", tags=["admin"])
security = HTTPBearer(auto_error=False)

class AuthService:
    @staticmethod
    def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        try:
            payload = jwt.decode(
                credentials.credentials, 
                os.getenv("JWT_SECRET", "ramyaconstructions"), 
                algorithms=["HS256"]
            )
            return payload.get("admin_id")
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )

# AUTH ROUTES
@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Admin login endpoint"""
    try:
        result = await AdminService.authenticate_admin(request.email, request.password)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        return LoginResponse(
            success=True,
            message="Login successful",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

# ADMIN MANAGEMENT ROUTES
@router.post("/", response_model=AdminResponse)
async def create_admin(
    request: CreateAdminRequest,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """Create new admin (public for first admin, then requires authentication)"""
    try:
        # Check if any admins exist
        admin_count = await AdminService.get_admin_count()
        
        # If admins exist, require authentication
        if admin_count > 0:
            if not credentials:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required - admins already exist"
                )
            # Verify the token
            AuthService.verify_token(credentials)
        
        admin = await AdminService.create_admin(request.email, request.password)
        return AdminResponse(
            success=True,
            message="Admin created successfully",
            data=admin
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create admin: {str(e)}"
        )

@router.get("/", response_model=AdminListResponse)
async def get_all_admins(admin_id: str = Depends(AuthService.verify_token)):
    """Get all admin users"""
    try:
        admins = await AdminService.get_all_admins()
        return AdminListResponse(
            success=True,
            message="Admins retrieved successfully",
            data=admins
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve admins: {str(e)}"
        )

@router.get("/profile/me", response_model=AdminResponse)
async def get_my_profile(admin_id: str = Depends(AuthService.verify_token)):
    """Get current admin's profile"""
    try:
        admin = await AdminService.get_admin_by_id(admin_id)
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin profile not found"
            )
        
        return AdminResponse(
            success=True,
            message="Profile retrieved successfully",
            data=admin
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve profile: {str(e)}"
        )

@router.get("/{target_admin_id}", response_model=AdminResponse)
async def get_admin_by_id(
    target_admin_id: str,
    admin_id: str = Depends(AuthService.verify_token)
):
    """Get specific admin by ID"""
    try:
        admin = await AdminService.get_admin_by_id(target_admin_id)
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin not found"
            )
        
        return AdminResponse(
            success=True,
            message="Admin retrieved successfully",
            data=admin
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve admin: {str(e)}"
        )

@router.put("/{target_admin_id}", response_model=AdminResponse)
async def update_admin(
    target_admin_id: str,
    request: UpdateAdminRequest,
    admin_id: str = Depends(AuthService.verify_token)
):
    """Update admin email/password"""
    try:
        admin = await AdminService.update_admin(
            target_admin_id, 
            request.email, 
            request.password
        )
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin not found"
            )
        
        return AdminResponse(
            success=True,
            message="Admin updated successfully",
            data=admin
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update admin: {str(e)}"
        )

@router.delete("/{target_admin_id}", response_model=SuccessResponse)
async def delete_admin(
    target_admin_id: str,
    admin_id: str = Depends(AuthService.verify_token)
):
    """Delete admin"""
    try:
        # Prevent self-deletion
        if target_admin_id == admin_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )
        
        success = await AdminService.delete_admin(target_admin_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin not found"
            )
        
        return SuccessResponse(
            success=True,
            message="Admin deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete admin: {str(e)}"
        )