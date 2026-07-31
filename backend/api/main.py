from fastapi import FastAPI
from api.routers import auth, projects, scans, ws
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Flawnetic API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["projects"])
app.include_router(scans.router, prefix="/api/v1", tags=["scans"])
app.include_router(ws.router, prefix="/api/v1", tags=["ws"])

@app.get("/health")
def health_check():
    return {"status": "ok"}
