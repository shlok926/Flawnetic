import uuid
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from api.routers import auth, projects, scans, ws, health
from config.settings import settings
from observability.logging import correlation_id_var, request_id_var, trace_id_var, span_id_var, setup_structured_logging
from observability.tracing import generate_trace_id, generate_span_id
from observability.metrics import metrics_registry

setup_structured_logging()

app = FastAPI(title="Flawnetic Enterprise API Platform", version="1.0.0")

@app.middleware("http")
async def security_and_correlation_middleware(request: Request, call_next):
    # Correlation & OpenTelemetry Tracing Context
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    trace_id = request.headers.get("X-Trace-ID") or generate_trace_id()
    span_id = generate_span_id()

    token_corr = correlation_id_var.set(correlation_id)
    token_req = request_id_var.set(request_id)
    token_trace = trace_id_var.set(trace_id)
    token_span = span_id_var.set(span_id)

    start_time = time.perf_counter()
    metrics_registry.inc_counter("api_requests_total")

    try:
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        metrics_registry.observe_histogram("api_request_duration_ms", duration_ms)

        # Enterprise Telemetry Headers
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Trace-ID"] = trace_id
        response.headers["X-Span-ID"] = span_id

        # Enterprise Security Hardening Headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response
    finally:
        correlation_id_var.reset(token_corr)
        request_id_var.reset(token_req)
        trace_id_var.reset(token_trace)
        span_id_var.reset(token_span)

# Restrict CORS origins strictly to configured frontend URLs
origins = [origin.strip() for origin in settings.frontend_url.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["projects"])
app.include_router(scans.router, prefix="/api/v1", tags=["scans"])
app.include_router(ws.router, prefix="/api/v1", tags=["ws"])
app.include_router(health.router, tags=["health"])

@app.get("/")
def root():
    return {
        "name": "Flawnetic API Platform",
        "status": "online",
        "version": "1.0.0",
        "documentation": "/docs",
        "health": "/health/live"
    }

@app.get("/health")
def health_check():
    return {"status": "ok"}
