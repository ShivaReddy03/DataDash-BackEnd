import psycopg
from psycopg_pool import AsyncConnectionPool
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection pool
_pool = None

async def init_db():
    """Initialize database connection pool"""
    global _pool
    
    # Database configuration from environment variables
    database_url = os.getenv("DATABASE_URL")
    
    if database_url:
        # Use DATABASE_URL if provided (for production/cloud deployments)
        _pool = AsyncConnectionPool(database_url, min_size=1, max_size=10, open=False)
    else:
        # Use individual parameters (for local development)
        host = os.getenv("DB_HOST", "localhost")
        port = int(os.getenv("DB_PORT", 5432))
        user = os.getenv("DB_USER", "postgres")
        password = os.getenv("DB_PASSWORD", "2004")
        database = os.getenv("DB_NAME", "ramya_constructions")
        
        connection_string = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        _pool = AsyncConnectionPool(connection_string, min_size=1, max_size=10, open=False)
    
    # Open the pool explicitly
    await _pool.open()
    
    # Create tables if they don't exist
    await create_tables()

async def close_db():
    """Close database connection pool"""
    global _pool
    if _pool:
        await _pool.close()

@asynccontextmanager
async def get_cursor() -> AsyncGenerator[psycopg.AsyncConnection, None]:
    """Get database connection from pool"""
    global _pool
    if not _pool:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    
    async with _pool.connection() as connection:
        yield connection

async def create_tables():
    """Create database tables if they don't exist"""
    async with get_cursor() as conn:
        async with conn.cursor() as cur:
            # Create admin_credentials table
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS admin_credentials (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create projects table
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    title VARCHAR(255) NOT NULL,
                    location VARCHAR(255) NOT NULL,
                    description TEXT,
                    long_description TEXT,
                    website_url TEXT,
                    status VARCHAR(50) NOT NULL DEFAULT 'available',
                    base_price DECIMAL(15,2) NOT NULL,
                    property_type VARCHAR(50) NOT NULL,
                    has_rental_income BOOLEAN DEFAULT FALSE,
                    pricing_details JSONB,
                    quick_info JSONB,
                    gallery_images JSONB,
                    key_highlights JSONB,
                    features JSONB,
                    investment_highlights JSONB,
                    amenities JSONB,
                    total_units INTEGER NOT NULL,
                    available_units INTEGER DEFAULT 0,
                    sold_units INTEGER DEFAULT 0,
                    reserved_units INTEGER DEFAULT 0,
                    rera_number VARCHAR(100),
                    building_permission VARCHAR(100),
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    
                    CONSTRAINT check_status CHECK (status IN ('available', 'sold_out', 'coming_soon')),
                    CONSTRAINT check_property_type CHECK (property_type IN ('commercial', 'residential', 'plot', 'land', 'mixed_use')),
                    CONSTRAINT check_base_price CHECK (base_price > 0),
                    CONSTRAINT check_total_units CHECK (total_units > 0),
                    CONSTRAINT check_available_units CHECK (available_units >= 0),
                    CONSTRAINT check_sold_units CHECK (sold_units >= 0),
                    CONSTRAINT check_reserved_units CHECK (reserved_units >= 0)
                )
            """)
            
            # Create investment_schemes table
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS investment_schemes (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                    scheme_type VARCHAR(50) NOT NULL,
                    scheme_name VARCHAR(255) NOT NULL,
                    area_sqft INTEGER NOT NULL,
                    booking_advance DECIMAL(15,2),
                    balance_payment_days INTEGER,
                    total_installments INTEGER,
                    monthly_installment_amount DECIMAL(15,2),
                    rental_start_month INTEGER,
                    start_date DATE NOT NULL,
                    end_date DATE,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    
                    CONSTRAINT check_scheme_type CHECK (scheme_type IN ('single_payment', 'installment')),
                    CONSTRAINT check_area_sqft CHECK (area_sqft > 0),
                    CONSTRAINT check_booking_advance CHECK (booking_advance >= 0),
                    CONSTRAINT check_balance_payment_days CHECK (balance_payment_days > 0),
                    CONSTRAINT check_total_installments CHECK (total_installments > 0),
                    CONSTRAINT check_monthly_installment_amount CHECK (monthly_installment_amount > 0),
                    CONSTRAINT check_rental_start_month CHECK (rental_start_month > 0),
                    CONSTRAINT check_date_range CHECK (end_date IS NULL OR end_date > start_date)
                )
            """)
            
            # Create indexes for better performance
            await cur.execute("CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status)")
            await cur.execute("CREATE INDEX IF NOT EXISTS idx_projects_property_type ON projects(property_type)")
            await cur.execute("CREATE INDEX IF NOT EXISTS idx_projects_is_active ON projects(is_active)")
            await cur.execute("CREATE INDEX IF NOT EXISTS idx_projects_base_price ON projects(base_price)")
            await cur.execute("CREATE INDEX IF NOT EXISTS idx_projects_created_at ON projects(created_at)")
            
            await cur.execute("CREATE INDEX IF NOT EXISTS idx_investment_schemes_project_id ON investment_schemes(project_id)")
            await cur.execute("CREATE INDEX IF NOT EXISTS idx_investment_schemes_scheme_type ON investment_schemes(scheme_type)")
            await cur.execute("CREATE INDEX IF NOT EXISTS idx_investment_schemes_is_active ON investment_schemes(is_active)")
            await cur.execute("CREATE INDEX IF NOT EXISTS idx_investment_schemes_start_date ON investment_schemes(start_date)")
            
            await cur.execute("CREATE INDEX IF NOT EXISTS idx_admin_credentials_email ON admin_credentials(email)")
            
            # Commit changes
            await conn.commit()

# Utility function to get database URL for external tools
def get_database_url():
    """Get database URL for external tools like migrations"""
    database_url = os.getenv("DATABASE_URL")
    
    if database_url:
        return database_url
    else:
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", 5432)
        user = os.getenv("DB_USER", "postgres")
        password = os.getenv("DB_PASSWORD", "2004")
        database = os.getenv("DB_NAME", "ramya_constructions")
        
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"