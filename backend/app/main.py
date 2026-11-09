from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
from app.api.endpoints import auth, intake, clinician, red_flags

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="MediAssist AI - Multilingual Patient Intake & Clinical Triage Workflow Platform",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for development & preview
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event to ensure database tables are initialized
@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# API Routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(intake.router, prefix=f"{settings.API_V1_STR}/intake", tags=["Patient Intake"])
app.include_router(clinician.router, prefix=f"{settings.API_V1_STR}/clinician", tags=["Clinician Dashboard"])
app.include_router(red_flags.router, prefix=f"{settings.API_V1_STR}/red-flags", tags=["Red Flags & Alerts"])

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "gemini_live": bool(settings.GEMINI_API_KEY)
    }

@app.get("/")
async def root():
    return {
        "message": "Welcome to MediAssist AI API. Visit /docs for the interactive Swagger documentation.",
        "status": "online"
    }

