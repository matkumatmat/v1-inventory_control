"""
API Dependencies
================

FastAPI dependencies for the WMS application.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from .services import create_service_registry
from .database import get_db_session
from .config import settings
from .services.exceptions import AuthenticationError

# Security
security = HTTPBearer()

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
        token_data = await auth_service.verify_access_token(token)
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
            token_data = await auth_service.verify_access_token(credentials.credentials)
            current_user = token_data.get('username')
        except:
            pass  # Ignore auth errors for optional auth
    
    return create_service_registry(
        db_session=db_session,
        config=settings.dict(),
        current_user=current_user
    )
