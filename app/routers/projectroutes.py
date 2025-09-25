from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from ..services.projectservice import ProjectService
from ..models.projectmodels import (
    CreateProjectRequest,
    UpdateProjectRequest,
    ProjectResponse,
    ProjectListResponse
)
import jwt
import os

router = APIRouter(prefix="/projects", tags=["projects"])
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
@router.post("/", response_model=ProjectResponse)
async def create_project(
    request: CreateProjectRequest,
    admin_id: str = Depends(AuthService.verify_admin_token)
):
    """Create new project (Admin only)"""
    try:
        project = await ProjectService.create_project(request)
        return ProjectResponse(
            success=True,
            message="Project created successfully",
            data=project
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project: {str(e)}"
        )

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    request: UpdateProjectRequest,
    admin_id: str = Depends(AuthService.verify_admin_token)
):
    """Update project - handles all updates including status, units, activation (Admin only)"""
    try:
        project = await ProjectService.update_project(project_id, request)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        return ProjectResponse(
            success=True,
            message="Project updated successfully",
            data=project
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
            detail=f"Failed to update project: {str(e)}"
        )

# PUBLIC READ OPERATIONS
@router.get("/", response_model=ProjectListResponse)
async def list_projects(
    limit: Optional[int] = Query(20, ge=1, le=100, description="Number of projects to return"),
    offset: Optional[int] = Query(0, ge=0, description="Number of projects to skip"),
    property_type: Optional[str] = Query(None, description="Filter by property type"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price filter")
):
    """List all active projects with pagination and filtering"""
    try:
        if min_price is not None and max_price is not None and min_price > max_price:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Minimum price cannot be greater than maximum price"
            )
        
        projects = await ProjectService.list_projects(
            limit=limit,
            offset=offset,
            property_type=property_type,
            status_filter=status_filter,
            min_price=min_price,
            max_price=max_price
        )
        return ProjectListResponse(
            success=True,
            message="Projects retrieved successfully",
            data=projects
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve projects: {str(e)}"
        )

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str):
    """Get single project by ID"""
    try:
        project = await ProjectService.get_project_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found or inactive"
            )
        
        return ProjectResponse(
            success=True,
            message="Project retrieved successfully",
            data=project
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve project: {str(e)}"
        )

@router.get("/property-type/{property_type}", response_model=ProjectListResponse)
async def get_projects_by_property_type(
    property_type: str,
    limit: Optional[int] = Query(20, ge=1, le=100, description="Number of projects to return"),
    offset: Optional[int] = Query(0, ge=0, description="Number of projects to skip")
):
    """Filter projects by property type"""
    try:
        # Validate property type
        valid_types = ['commercial', 'residential', 'plot', 'land', 'mixed_use']
        if property_type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid property type. Must be one of: {', '.join(valid_types)}"
            )
        
        projects = await ProjectService.get_projects_by_property_type(
            property_type=property_type,
            limit=limit,
            offset=offset
        )
        return ProjectListResponse(
            success=True,
            message=f"Projects with property type '{property_type}' retrieved successfully",
            data=projects
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve projects by property type: {str(e)}"
        )

@router.get("/status/available", response_model=ProjectListResponse)
async def get_available_projects(
    limit: Optional[int] = Query(20, ge=1, le=100, description="Number of projects to return"),
    offset: Optional[int] = Query(0, ge=0, description="Number of projects to skip")
):
    """Get only available projects"""
    try:
        projects = await ProjectService.get_available_projects(
            limit=limit,
            offset=offset
        )
        return ProjectListResponse(
            success=True,
            message="Available projects retrieved successfully",
            data=projects
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve available projects: {str(e)}"
        )

@router.get("/search/{search_term}", response_model=ProjectListResponse)
async def search_projects(
    search_term: str,
    limit: Optional[int] = Query(20, ge=1, le=100, description="Number of projects to return"),
    offset: Optional[int] = Query(0, ge=0, description="Number of projects to skip")
):
    """Search projects by term (searches in title, location, description)"""
    try:
        if len(search_term.strip()) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search term must be at least 2 characters long"
            )
        
        projects = await ProjectService.search_projects(
            search_term=search_term.strip(),
            limit=limit,
            offset=offset
        )
        return ProjectListResponse(
            success=True,
            message=f"Search results for '{search_term}' retrieved successfully",
            data=projects
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search projects: {str(e)}"
        )