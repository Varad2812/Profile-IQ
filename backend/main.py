import logging
import logging.config
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from models.database import init_db
from routes import auth, analysis, admin
from utils.limiter import limiter

# ── Structured logging ────────────────────────────────────────────────────────

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "structured": {
            "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "structured",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": "profileiq.log",
            "formatter": "structured",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"],
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(title="ProfileIQ API", version="1.0.0")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:8001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request logging middleware ────────────────────────────────────────────────

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"→ {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"← {request.method} {request.url.path} [{response.status_code}]")
    return response


# ── Standardized error handler ────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Don't mask HTTPExceptions as 500s
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail if isinstance(exc.detail, dict) else {"error": True, "message": str(exc.detail), "code": exc.status_code},
        )
    
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    print(f"DEBUG ERROR: {exc}") # Direct console output
    import traceback
    traceback.print_exc() # Direct traceback to console
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "An unexpected server error occurred. Please contact support if the issue persists.", "error_code": 500},
    )


# ── Startup ───────────────────────────────────────────────────────────────────

@app.on_event("startup")
def startup():
    init_db()
    logger.info("ProfileIQ API started — DB initialized")


app.include_router(auth.router)
app.include_router(analysis.router)
app.include_router(admin.router)


@app.get("/")
def root():
    return {"message": "ProfileIQ API is running"}
