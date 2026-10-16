from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.init_db import init_db
from app.routers import auth, cv, interview, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} started")
    yield
    # Shutdown
    print("👋 Shutting down...")


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
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000", "http://localhost:5173"],
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
