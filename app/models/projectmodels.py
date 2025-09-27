import uuid
from pydantic import BaseModel, HttpUrl, field_validator, model_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class ProjectStatus(str, Enum):
    available = "available"
    sold_out = "sold_out"
    coming_soon = "coming_soon"

class PropertyType(str, Enum):
    commercial = "commercial"
    residential = "residential"
    plot = "plot"
    land = "land"
    mixed_use = "mixed_use"

class ProjectData(BaseModel):
    id: str
    title: str
    location: str
    description: Optional[str]
    long_description: Optional[str]
    website_url: Optional[str]  # Changed from HttpUrl to str to avoid validation issues
    status: ProjectStatus
    base_price: float
    property_type: PropertyType
    has_rental_income: bool
    
    # JSON fields
    pricing_details: Optional[Dict[str, Any]]
    quick_info: Optional[Dict[str, Any]]
    gallery_images: Optional[List[Dict[str, Any]]]
    key_highlights: Optional[List[str]]
    features: Optional[List[str]]
    investment_highlights: Optional[List[str]]
    amenities: Optional[List[Dict[str, Any]]]
    
    # Unit inventory
    total_units: int
    available_units: int
    sold_units: int
    reserved_units: int
    
    # Legal info
    rera_number: Optional[str]
    building_permission: Optional[str]
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    is_active: bool

class CreateProjectRequest(BaseModel):
    title: str
    location: str
    description: Optional[str] = None
    long_description: Optional[str] = None
    website_url: Optional[str] = None  # Changed from HttpUrl to str
    status: ProjectStatus = ProjectStatus.available
    base_price: float
    property_type: PropertyType
    has_rental_income: bool = False
    
    # JSON fields
    pricing_details: Optional[Dict[str, Any]] = None
    quick_info: Optional[Dict[str, Any]] = None
    gallery_images: Optional[List[Dict[str, Any]]] = None
    key_highlights: Optional[List[str]] = None
    features: Optional[List[str]] = None
    investment_highlights: Optional[List[str]] = None
    amenities: Optional[List[Dict[str, Any]]] = None
    
    # Unit inventory
    total_units: int
    available_units: int = 0
    sold_units: int = 0
    reserved_units: int = 0
    
    # Legal info
    rera_number: Optional[str] = None
    building_permission: Optional[str] = None
    
    # Validators
    @field_validator('base_price')
    @classmethod
    def validate_base_price(cls, v):
        if v <= 0:
            raise ValueError('Base price must be greater than 0')
        return v
    
    @field_validator('total_units')
    @classmethod
    def validate_total_units(cls, v):
        if v <= 0:
            raise ValueError('Total units must be greater than 0')
        return v
    
    @field_validator('available_units')
    @classmethod
    def validate_available_units(cls, v):
        if v < 0:
            raise ValueError('Available units cannot be negative')
        return v
    
    @field_validator('sold_units')
    @classmethod
    def validate_sold_units(cls, v):
        if v < 0:
            raise ValueError('Sold units cannot be negative')
        return v
    
    @field_validator('reserved_units')
    @classmethod
    def validate_reserved_units(cls, v):
        if v < 0:
            raise ValueError('Reserved units cannot be negative')
        return v
    
    @model_validator(mode='after')
    def validate_model(self):
        # Validate rental income logic
        if self.property_type in ['plot', 'land'] and self.has_rental_income:
            raise ValueError('Plot and land properties cannot have rental income')
        
        # Validate unit totals
        if self.total_units != (self.available_units + self.sold_units + self.reserved_units):
            raise ValueError('Total units must equal sum of available, sold, and reserved units')
        
        return self

class UpdateProjectRequest(BaseModel):
    # Basic fields
    title: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    long_description: Optional[str] = None
    website_url: Optional[str] = None  # Changed from HttpUrl to str
    status: Optional[ProjectStatus] = None
    base_price: Optional[float] = None
    property_type: Optional[PropertyType] = None
    has_rental_income: Optional[bool] = None
    
    # JSON fields
    pricing_details: Optional[Dict[str, Any]] = None
    quick_info: Optional[Dict[str, Any]] = None
    gallery_images: Optional[List[Dict[str, Any]]] = None
    key_highlights: Optional[List[str]] = None
    features: Optional[List[str]] = None
    investment_highlights: Optional[List[str]] = None
    amenities: Optional[List[Dict[str, Any]]] = None
    
    # Unit inventory
    total_units: Optional[int] = None
    available_units: Optional[int] = None
    sold_units: Optional[int] = None
    reserved_units: Optional[int] = None
    
    # Legal info
    rera_number: Optional[str] = None
    building_permission: Optional[str] = None
    
    # Active status
    is_active: Optional[bool] = None
    
    # Validators
    @field_validator('base_price')
    @classmethod
    def validate_base_price(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Base price must be greater than 0')
        return v
    
    @field_validator('total_units')
    @classmethod
    def validate_total_units(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Total units must be greater than 0')
        return v
    
    @field_validator('available_units')
    @classmethod
    def validate_available_units(cls, v):
        if v is not None and v < 0:
            raise ValueError('Available units cannot be negative')
        return v
    
    @field_validator('sold_units')
    @classmethod
    def validate_sold_units(cls, v):
        if v is not None and v < 0:
            raise ValueError('Sold units cannot be negative')
        return v
    
    @field_validator('reserved_units')
    @classmethod
    def validate_reserved_units(cls, v):
        if v is not None and v < 0:
            raise ValueError('Reserved units cannot be negative')
        return v

class ProjectSummary(BaseModel):
    """Simplified project data for listing views"""
    id: str
    title: str
    location: str
    status: ProjectStatus
    base_price: float
    property_type: PropertyType
    has_rental_income: bool
    available_units: int
    total_units: int
    primary_image: Optional[str]  # URL of primary gallery image

class ProjectResponse(BaseModel):
    success: bool
    message: str
    data: ProjectData

class ProjectListResponse(BaseModel):
    success: bool
    message: str
    data: List[ProjectData]

class ProjectSummaryListResponse(BaseModel):
    success: bool
    message: str
    data: List[ProjectSummary]

class ListProjectResponse(BaseModel):
    message: str
    page: int
    limit: int
    total_pages: int
    is_previous: bool
    is_next: bool
    total_projects: int
    projects: List[ProjectData]

class ProjectOption(BaseModel):
    id: uuid.UUID
    title: str
    property_type: Optional[PropertyType] = None

class ProjectOptionsResponse(BaseModel):
    success: bool
    message: str
    data: List[ProjectOption]