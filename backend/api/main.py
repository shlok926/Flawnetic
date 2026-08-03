from fastapi import FastAPI
from api.routers import auth, projects, scans, ws
from fastapi.middleware.cors import CORSMiddleware

from config.settings import settings

app = FastAPI(title="Flawnetic API", version="1.0.0")

# Restrict CORS origins strictly to configured frontend URLs
origins = [origin.strip() for origin in settings.frontend_url.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["projects"])
app.include_router(scans.router, prefix="/api/v1", tags=["scans"])
app.include_router(ws.router, prefix="/api/v1", tags=["ws"])

@app.get("/")
def root():
    return {
        "name": "Flawnetic API Platform",
        "status": "online",
        "version": "1.0.0",
        "documentation": "/docs",
        "health": "/health"
    }

@app.get("/health")
def health_check():
    return {"status": "ok"}
