"""
WMS Routes Module
=================

API Routes untuk WMS application
FastAPI-based REST API dengan authentication dan validation
"""

from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import uuid
from typing import Optional

# Import route modules
from .auth import auth_router, user_router
from .product import product_router, batch_router, allocation_router

# Import services and dependencies
from ..services import ServiceRegistry, create_service_registry
from ..services.exceptions import (
    ValidationError, NotFoundError, BusinessRuleError, 
    AuthenticationError, AuthorizationError
)
from ..database import get_db_session
from ..config import settings

# Security
security = HTTPBearer()

def create_app() -> FastAPI:
    """Create FastAPI application dengan middleware dan routes"""
    
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Application lifespan events"""
        # Startup
        print("🚀 WMS API Starting up...")
        yield
        # Shutdown  
        print("⛔ WMS API Shutting down...")
    
    app = FastAPI(
        title="Warehouse Management System API",
        description="Complete WMS API untuk Pharmaceutical Supply Chain",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )
    
    # Add middleware
    setup_middleware(app)
    
    # Add exception handlers
    setup_exception_handlers(app)
    
    # Add routes
    setup_routes(app)
    
    return app

def setup_middleware(app: FastAPI):
    """Setup application middleware"""
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["*"],
    )
    
    # Trusted host middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )
    
    # Request ID middleware
    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Add to response headers
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    
    # Performance monitoring middleware
    @app.middleware("http")
    async def add_process_time(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response

def setup_exception_handlers(app: FastAPI):
    """Setup custom exception handlers"""
    
    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request: Request, exc: ValidationError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "Validation Error",
                "message": str(exc),
                "details": exc.details if hasattr(exc, 'details') else None,
                "request_id": getattr(request.state, 'request_id', None)
            }
        )
    
    @app.exception_handler(NotFoundError)
    async def not_found_exception_handler(request: Request, exc: NotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": "Not Found",
                "message": str(exc),
                "entity_type": exc.entity_type,
                "entity_id": exc.entity_id,
                "request_id": getattr(request.state, 'request_id', None)
            }
        )
    
    @app.exception_handler(BusinessRuleError)
    async def business_rule_exception_handler(request: Request, exc: BusinessRuleError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Business Rule Violation",
                "message": str(exc),
                "rule": exc.rule if hasattr(exc, 'rule') else None,
                "request_id": getattr(request.state, 'request_id', None)
            }
        )
    
    @app.exception_handler(AuthenticationError)
    async def authentication_exception_handler(request: Request, exc: AuthenticationError):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": "Authentication Error",
                "message": str(exc),
                "request_id": getattr(request.state, 'request_id', None)
            }
        )
    
    @app.exception_handler(AuthorizationError)
    async def authorization_exception_handler(request: Request, exc: AuthorizationError):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "error": "Authorization Error", 
                "message": str(exc),
                "request_id": getattr(request.state, 'request_id', None)
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred",
                "request_id": getattr(request.state, 'request_id', None)
            }
        )

def setup_routes(app: FastAPI):
    """Setup application routes"""
    
    # Health check endpoint
    @app.get("/health", tags=["System"])
    async def health_check():
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "version": "1.0.0"
        }
    
    # API info endpoint
    @app.get("/", tags=["System"])
    async def root():
        return {
            "message": "WMS API",
            "version": "1.0.0",
            "docs_url": "/docs",
            "redoc_url": "/redoc"
        }
    
    # Include route modules
    app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
    app.include_router(user_router, prefix="/api/users", tags=["User Management"])
    app.include_router(product_router, prefix="/api/products", tags=["Products"])
    app.include_router(batch_router, prefix="/api/batches", tags=["Batches"])
    app.include_router(allocation_router, prefix="/api/allocations", tags=["Allocations"])

# Dependency untuk get current user
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db_session = Depends(get_db_session)
):
    """Get current authenticated user"""
    token = credentials.credentials
    
    # Create service registry
    service_registry = create_service_registry(db_session, settings.dict())
    auth_service = service_registry.auth_service
    
    try:
        token_data = auth_service.verify_access_token(token)
        return token_data
    except AuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )

# Dependency untuk get service registry
async def get_service_registry(
    db_session = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    """Get service registry dengan current user"""
    return create_service_registry(
        db_session=db_session,
        config=settings.dict(),
        current_user=current_user.get('username')
    )

# Optional dependency untuk endpoints yang tidak memerlukan auth
async def get_service_registry_optional(
    db_session = Depends(get_db_session),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
):
    """Get service registry tanpa authentication requirement"""
    current_user = None
    
    if credentials:
        try:
            service_registry = create_service_registry(db_session, settings.dict())
            auth_service = service_registry.auth_service
            token_data = auth_service.verify_access_token(credentials.credentials)
            current_user = token_data.get('username')
        except:
            pass  # Ignore auth errors for optional auth
    
    return create_service_registry(
        db_session=db_session,
        config=settings.dict(),
        current_user=current_user
    )

# Response models
class APIResponse:
    """Standard API response format"""
    
    @staticmethod
    def success(data=None, message="Success"):
        return {
            "success": True,
            "message": message,
            "data": data
        }
    
    @staticmethod
    def error(message="Error", error_code=None):
        return {
            "success": False,
            "message": message,
            "error_code": error_code
        }
    
    @staticmethod
    def paginated(data, total, page, per_page, message="Success"):
        return {
            "success": True,
            "message": message,
            "data": data,
            "pagination": {
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page
            }
        }

# Create the app instance
app = create_app()