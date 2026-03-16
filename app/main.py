# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from datetime import datetime
import os

# ✅ Import the routers correctly
from app.api.v1.endpoints import analysis, monitoring
from app.api.v1.models.responses import HealthResponse

# Create FastAPI app
app = FastAPI(
    title="Agentic Analyst API",
    description="Autonomous AI agent for business analytics",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers - note we're using .router attribute
app.include_router(analysis.router)
app.include_router(monitoring.router)

@app.get("/", response_class=JSONResponse)
async def root():
    """Root endpoint with API info"""
    return {
        "name": "Agentic Analyst API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "health": "/api/v1/analysis/health"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Global health check"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat()
    )

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )