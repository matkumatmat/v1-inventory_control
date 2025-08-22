"""
WMS Application Factory
=======================

Pusat perakitan aplikasi FastAPI menggunakan Application Factory Pattern.
"""

from fastapi import FastAPI, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import uuid
from typing import Optional

# Import semua router dari modulnya masing-masing
from .routes.auth import auth_router, user_router
from .routes.product import product_router, batch_router, allocation_router

# Import services dan dependencies
from .services import ServiceRegistry, create_service_registry
from .services.exceptions import (
    ValidationError, NotFoundError, BusinessRuleError, 
    AuthenticationError, AuthorizationError
)
from .database import get_db_session
from .config import settings

# Security (Bisa ditaruh di sini atau di dalam create_app)
security = HTTPBearer()

def setup_middleware(app: FastAPI):
    """Setup semua middleware aplikasi."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["*"],
    )
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )

    @app.middleware("http")
    async def add_request_id_and_process_time(request: Request, call_next):
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        request.state.request_id = request_id
        response = await call_next(request)
        
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = request_id
        return response

def setup_exception_handlers(app: FastAPI):
    """Setup semua custom exception handlers."""
    # (Semua @app.exception_handler(...) dari file lama lo ditaruh di sini)
    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request: Request, exc: ValidationError):
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": "Validation Error", "message": str(exc)})
    
    @app.exception_handler(NotFoundError)
    async def not_found_exception_handler(request: Request, exc: NotFoundError):
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"error": "Not Found", "message": str(exc)})
    
    @app.exception_handler(BusinessRuleError)
    async def business_rule_exception_handler(request: Request, exc: BusinessRuleError):
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"error": "Business Rule Violation", "message": str(exc)})

    @app.exception_handler(AuthenticationError)
    async def authentication_exception_handler(request: Request, exc: AuthenticationError):
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"error": "Authentication Error", "message": str(exc)})

    @app.exception_handler(AuthorizationError)
    async def authorization_exception_handler(request: Request, exc: AuthorizationError):
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"error": "Authorization Error", "message": str(exc)})
        
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        # Di production, sebaiknya log error ini
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"error": "Internal Server Error", "message": "An unexpected error occurred"})

def setup_routes(app: FastAPI):
    """Daftarkan (include) semua router ke aplikasi."""
    # Endpoint sistem
    @app.get("/health", tags=["System"])
    async def health_check():
        return {"status": "healthy", "timestamp": time.time()}

    @app.get("/", tags=["System"])
    async def root():
        return {"message": "WMS API", "version": "1.0.0", "docs": "/docs"}

    # Daftarkan semua router dari modul
    app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
    app.include_router(user_router, prefix="/api/users", tags=["User Management"])
    app.include_router(product_router, prefix="/api/products", tags=["Products"])
    app.include_router(batch_router, prefix="/api/batches", tags=["Batches"])
    app.include_router(allocation_router, prefix="/api/allocations", tags=["Allocations"])

def create_app() -> FastAPI:
    """
    Application Factory: Membuat dan mengkonfigurasi instance FastAPI.
    """
    
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Kode yang dijalankan saat startup
        print("🚀 WMS API Starting up...")
        yield
        # Kode yang dijalankan saat shutdown
        print("⛔ WMS API Shutting down...")
    
    # 1. Buat instance FastAPI
    app = FastAPI(
        title="Warehouse Management System API",
        description="Complete WMS API untuk Pharmaceutical Supply Chain",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # 2. Setup Middleware
    setup_middleware(app)
    
    # 3. Setup Exception Handlers
    setup_exception_handlers(app)
    
    # 4. Setup Routes (Blueprints)
    setup_routes(app)
    
    print("✅ FastAPI app created and configured successfully.")
    return app

# Di sini kita juga perlu dependency injections yang sebelumnya ada di routes/__init__.py
# agar bisa di-import oleh file-file routes
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db_session = Depends(get_db_session)
):
    # ... (logika get_current_user dari file lama lo)
    service_registry = create_service_registry(db_session, settings.dict())
    try:
        token_data = service_registry.auth_service.verify_access_token(credentials.credentials)
        return token_data
    except AuthenticationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e), headers={"WWW-Authenticate": "Bearer"})

async def get_service_registry(
    db_session = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    # ... (logika get_service_registry dari file lama lo)
    return create_service_registry(db_session=db_session, config=settings.dict(), current_user=current_user.get('username'))

async def get_service_registry_optional(
    db_session = Depends(get_db_session),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
):
    # ... (logika get_service_registry_optional dari file lama lo)
    current_user = None
    if credentials:
        try:
            service_registry = create_service_registry(db_session, settings.dict())
            token_data = service_registry.auth_service.verify_access_token(credentials.credentials)
            current_user = token_data.get('username')
        except:
            pass
    return create_service_registry(db_session=db_session, config=settings.dict(), current_user=current_user)

# Definisikan juga APIResponse di sini agar bisa di-import
class APIResponse:
    # ... (logika class APIResponse dari file lama lo)
    @staticmethod
    def success(data=None, message="Success"):
        return {"success": True, "message": message, "data": data}
    
    @staticmethod
    def paginated(data, total, page, per_page, message="Success"):
        return {
            "success": True,
            "message": message,
            "data": data,
            "pagination": {"total": total, "page": page, "per_page": per_page, "total_pages": (total + per_page - 1) // per_page}
        }