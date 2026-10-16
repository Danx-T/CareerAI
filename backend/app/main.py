import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.init_db import init_db
from app.routers import auth, cv, interview, admin
from app.services import ai_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    force=True,
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    logger.info("Application started: %s v%s", settings.APP_NAME, settings.APP_VERSION)
    yield
    # Shutdown
    await ai_service.close_client()
    logger.info("Application shutdown completed")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered CV optimization and interview preparation platform",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)

# CORS
cors_origins = [settings.FRONTEND_URL] if settings.FRONTEND_URL else ["*"]
if settings.DEBUG and cors_origins != ["*"]:
    for dev_origin in ("http://localhost:3000", "http://localhost:5173"):
        if dev_origin not in cors_origins:
            cors_origins.append(dev_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(cv.router)
app.include_router(interview.router)
app.include_router(admin.router)


@app.get("/", tags=["Health"])
async def root():
    response = {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }
    if settings.DEBUG:
        response["docs"] = "/docs"
    return response


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}
