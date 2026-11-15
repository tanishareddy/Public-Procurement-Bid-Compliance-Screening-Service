import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api.endpoints import router as api_router
from app.monitoring.metrics import get_prometheus_metrics
from app.database.session import init_db
from app.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite / PostgreSQL tables
    init_db()
    yield

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Multi-Agent Public Procurement Bid Compliance Screening Service for Public Tenders",
    lifespan=lifespan
)

# CORS configuration for Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Core Endpoints
app.include_router(api_router)

# Mount Static UI directory
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/")
    def serve_frontend():
        return FileResponse(os.path.join(static_dir, "index.html"))

# Health & Metrics Endpoints
@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "llm_provider": settings.LLM_PROVIDER,
        "database": "connected"
    }

@app.get("/api/v1/metrics")
def metrics():
    return get_prometheus_metrics()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
