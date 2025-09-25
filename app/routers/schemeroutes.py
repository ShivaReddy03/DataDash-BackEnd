from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from ..services.schemeservice import InvestmentSchemeService
from ..models.schememodels import (
    CreateInvestmentSchemeRequest,
    UpdateInvestmentSchemeRequest,
    InvestmentSchemeResponse,
    InvestmentSchemeListResponse
)
import jwt
import os

router = APIRouter(prefix="/investment-schemes", tags=["investment-schemes"])
security = HTTPBearer()

class AuthService:
    @staticmethod
    def verify_admin_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
        try:
            payload = jwt.decode(
                credentials.credentials, 
                os.getenv("JWT_SECRET", "ramyaconstructions"), 
                algorithms=["HS256"]
            )
            admin_id = payload.get("admin_id")
            if not admin_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: Admin access required"
                )
            return admin_id
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )

# ADMIN WRITE OPERATIONS
@router.post("/", response_model=InvestmentSchemeResponse)
async def create_investment_scheme(
    request: CreateInvestmentSchemeRequest,
    admin_id: str = Depends(AuthService.verify_admin_token)
):
    """Create new investment scheme (Admin only)"""
    try:
        scheme = await InvestmentSchemeService.create_scheme(request)
        return InvestmentSchemeResponse(
            success=True,
            message="Investment scheme created successfully",
            data=scheme
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create investment scheme: {str(e)}"
        )

@router.put("/{scheme_id}", response_model=InvestmentSchemeResponse)
async def update_investment_scheme(
    scheme_id: str,
    request: UpdateInvestmentSchemeRequest,
    admin_id: str = Depends(AuthService.verify_admin_token)
):
    """Update investment scheme (Admin only)"""
    try:
        scheme = await InvestmentSchemeService.update_scheme(scheme_id, request)
        if not scheme:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Investment scheme not found"
            )
        
        return InvestmentSchemeResponse(
            success=True,
            message="Investment scheme updated successfully",
            data=scheme
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
            detail=f"Failed to update investment scheme: {str(e)}"
        )

# PUBLIC READ OPERATIONS
@router.get("/", response_model=InvestmentSchemeListResponse)
async def get_all_investment_schemes(
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    scheme_type: Optional[str] = Query(None, description="Filter by scheme type: single_payment, installment"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: Optional[int] = Query(20, ge=1, le=100, description="Number of schemes to return"),
    offset: Optional[int] = Query(0, ge=0, description="Number of schemes to skip")
):
    """Get all active investment schemes with optional filters"""
    try:
        schemes = await InvestmentSchemeService.get_all_schemes(
            project_id=project_id,
            scheme_type=scheme_type,
            is_active=is_active,
            limit=limit,
            offset=offset
        )
        return InvestmentSchemeListResponse(
            success=True,
            message="Investment schemes retrieved successfully",
            data=schemes
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve investment schemes: {str(e)}"
        )

@router.get("/{scheme_id}", response_model=InvestmentSchemeResponse)
async def get_investment_scheme_by_id(scheme_id: str):
    """Get specific investment scheme by ID"""
    try:
        scheme = await InvestmentSchemeService.get_scheme_by_id(scheme_id)
        if not scheme:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Investment scheme not found"
            )
        
        return InvestmentSchemeResponse(
            success=True,
            message="Investment scheme retrieved successfully",
            data=scheme
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve investment scheme: {str(e)}"
        )

@router.get("/project/{project_id}", response_model=InvestmentSchemeListResponse)
async def get_schemes_by_project(
    project_id: str,
    scheme_type: Optional[str] = Query(None, description="Filter by scheme type: single_payment, installment"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    page: Optional[int] = Query(1, ge=1, description="Page number"),
    limit: Optional[int] = Query(20, ge=1, le=100, description="Number of schemes per page")
):
    """Get investment schemes for a specific project with pagination"""
    try:
        schemes, total_schemes = await InvestmentSchemeService.get_schemes_by_project(
            project_id=project_id,
            scheme_type=scheme_type,
            is_active=is_active,
            page=page,
            limit=limit
        )
        
        total_pages = (total_schemes + limit - 1) // limit

        return InvestmentSchemeListResponse(
            message=f"Investment schemes for project retrieved successfully",
            page=page,
            limit=limit,
            total_pages=total_pages,
            is_previous=page > 1,
            is_next=page < total_pages,
            total_schemes=total_schemes,
            schemes=schemes
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve investment schemes for project: {str(e)}"
        )