"""
Main FastAPI application entry point.
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.core.config import settings
from app.database import init_db
from app.routers import portfolios, transactions, assets, market_data, analytics

# Create FastAPI application
app = FastAPI(
    title=settings.project_name,
    description="A comprehensive financial portfolio tracking and analysis platform",
    version="1.0.0",
    openapi_url=f"{settings.api_v1_str}/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8050", "http://127.0.0.1:8050"],  # Dash frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    portfolios.router,
    prefix=f"{settings.api_v1_str}/portfolios",
    tags=["portfolios"]
)

app.include_router(
    transactions.router,
    prefix=f"{settings.api_v1_str}/transactions",
    tags=["transactions"]
)

app.include_router(
    assets.router,
    prefix=f"{settings.api_v1_str}/assets",
    tags=["assets"]
)

app.include_router(
    market_data.router,
    prefix=f"{settings.api_v1_str}/market-data",
    tags=["market-data"]
)

app.include_router(
    analytics.router,
    prefix=f"{settings.api_v1_str}/analytics",
    tags=["analytics"]
)

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to FPTI - Financial Portfolio Tracking Interface",
        "version": "1.0.0",
        "docs": "/docs",
        "api": settings.api_v1_str
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": "2025-09-24T12:00:00Z"}

@app.get(f"{settings.api_v1_str}/")
async def api_root():
    """API v1 root endpoint."""
    return {
        "message": "FPTI API v1",
        "version": "1.0.0",
        "available_endpoints": [
            f"{settings.api_v1_str}/portfolios",
            f"{settings.api_v1_str}/transactions", 
            f"{settings.api_v1_str}/assets",
            f"{settings.api_v1_str}/market-data",
            f"{settings.api_v1_str}/analytics"
        ]
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )