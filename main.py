from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import configuration
from app.configuration.database import init_db, close_db

# Import routes
from app.routers.adminroutes import router as admin_router
from app.routers.projectroutes import router as project_router
from app.routers.schemeroutes import router as scheme_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up application...")
    await init_db()
    print("Database connection initialized")
    
    yield
    
    # Shutdown
    print("Shutting down application...")
    await close_db()
    print("Database connection closed")

# Create FastAPI app with lifespan events
app = FastAPI(
    title="Ramya Constructions API",
    description="API for managing real estate projects and investment schemes",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(admin_router)
app.include_router(project_router)
app.include_router(scheme_router)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to Ramya Constructions API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )