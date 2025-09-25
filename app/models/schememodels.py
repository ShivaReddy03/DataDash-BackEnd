from pydantic import BaseModel, field_validator, model_validator
from typing import Optional, List
from datetime import datetime, date
from enum import Enum

class SchemeType(str, Enum):
    single_payment = "single_payment"
    installment = "installment"

class InvestmentSchemeData(BaseModel):
    id: str
    project_id: str
    scheme_type: SchemeType
    scheme_name: str
    area_sqft: int
    
    # Booking advance for all scheme types
    booking_advance: Optional[float]
    
    # Single payment specific fields
    balance_payment_days: Optional[int]
    
    # Installment specific fields
    total_installments: Optional[int]
    monthly_installment_amount: Optional[float]
    
    # Rental-specific fields (only for commercial properties)
    rental_start_month: Optional[int]
    
    # Date range for scheme availability
    start_date: date
    end_date: Optional[date]
    
    # Active status
    is_active: bool
    created_at: datetime
    updated_at: datetime

class CreateInvestmentSchemeRequest(BaseModel):
    project_id: str
    scheme_type: SchemeType
    scheme_name: str
    area_sqft: int
    
    # Booking advance for all scheme types
    booking_advance: Optional[float] = None
    
    # Single payment specific fields
    balance_payment_days: Optional[int] = None 
    
    # Installment specific fields
    total_installments: Optional[int] = None
    monthly_installment_amount: Optional[float] = None
    
    # Rental-specific fields (only for commercial properties)
    rental_start_month: Optional[int] = None
    
    # Date range for scheme availability
    start_date: date
    end_date: Optional[date] = None
    
    # Active status
    is_active: bool = True
    
    @field_validator('area_sqft')
    @classmethod
    def validate_area_sqft(cls, v):
        if v <= 0:
            raise ValueError('Area square feet must be greater than 0')
        return v
    
    @field_validator('booking_advance')
    @classmethod
    def validate_booking_advance(cls, v):
        if v is not None and v < 0:
            raise ValueError('Booking advance cannot be negative')
        return v
    
    @field_validator('balance_payment_days')
    @classmethod
    def validate_balance_payment_days(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Balance payment days must be greater than 0')
        return v
    
    @field_validator('total_installments')
    @classmethod
    def validate_total_installments(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Total installments must be greater than 0')
        return v
    
    @field_validator('monthly_installment_amount')
    @classmethod
    def validate_monthly_installment_amount(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Monthly installment amount must be greater than 0')
        return v
    
    @field_validator('rental_start_month')
    @classmethod
    def validate_rental_start_month(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Rental start month must be greater than 0')
        return v
    
    @model_validator(mode='after')
    def validate_scheme_fields(self):
        # Validate single payment scheme
        if self.scheme_type == SchemeType.single_payment:
            if self.total_installments is not None:
                raise ValueError('Single payment schemes cannot have total_installments')
            if self.monthly_installment_amount is not None:
                raise ValueError('Single payment schemes cannot have monthly_installment_amount')
        
        # Validate installment scheme
        elif self.scheme_type == SchemeType.installment:
            if self.total_installments is None or self.total_installments <= 0:
                raise ValueError('Installment schemes must have valid total_installments')
            if self.monthly_installment_amount is None or self.monthly_installment_amount <= 0:
                raise ValueError('Installment schemes must have valid monthly_installment_amount')
        
        # Validate date range
        if self.end_date is not None and self.end_date <= self.start_date:
            raise ValueError('End date must be after start date')
        
        return self

class UpdateInvestmentSchemeRequest(BaseModel):
    scheme_name: Optional[str] = None
    area_sqft: Optional[int] = None
    
    # Booking advance for all scheme types
    booking_advance: Optional[float] = None
    
    # Single payment specific fields
    balance_payment_days: Optional[int] = None
    
    # Installment specific fields
    total_installments: Optional[int] = None
    monthly_installment_amount: Optional[float] = None
    
    # Rental-specific fields (only for commercial properties)
    rental_start_month: Optional[int] = None
    
    # Date range for scheme availability
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    
    # Active status
    is_active: Optional[bool] = None
    
    @field_validator('area_sqft')
    @classmethod
    def validate_area_sqft(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Area square feet must be greater than 0')
        return v
    
    @field_validator('booking_advance')
    @classmethod
    def validate_booking_advance(cls, v):
        if v is not None and v < 0:
            raise ValueError('Booking advance cannot be negative')
        return v
    
    @field_validator('balance_payment_days')
    @classmethod
    def validate_balance_payment_days(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Balance payment days must be greater than 0')
        return v
    
    @field_validator('total_installments')
    @classmethod
    def validate_total_installments(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Total installments must be greater than 0')
        return v
    
    @field_validator('monthly_installment_amount')
    @classmethod
    def validate_monthly_installment_amount(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Monthly installment amount must be greater than 0')
        return v
    
    @field_validator('rental_start_month')
    @classmethod
    def validate_rental_start_month(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Rental start month must be greater than 0')
        return v
    
    @model_validator(mode='after')
    def validate_date_range(self):
        if (self.start_date is not None and 
            self.end_date is not None and 
            self.end_date <= self.start_date):
            raise ValueError('End date must be after start date')
        return self

class InvestmentSchemeResponse(BaseModel):
    success: bool
    message: str
    data: InvestmentSchemeData

class InvestmentSchemeListResponse(BaseModel):
    message: str
    page: int
    limit: int
    total_pages: int
    is_previous: bool
    is_next: bool
    total_schemes: int
    schemes: List[InvestmentSchemeData]