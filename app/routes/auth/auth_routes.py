"""
Authentication Routes
=====================

CRITICAL ROUTES untuk login, logout, dan token management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Dict, Any

from ...services import ServiceRegistry
from ...schemas import LoginSchema, LoginResponseSchema, TokenRefreshSchema
from ...dependencies import get_service_registry_optional
from ...responses import APIResponse

router = APIRouter()
security = HTTPBearer()

@router.post("/login", response_model=Dict[str, Any])
async def login(
    request: Request,
    login_data: LoginSchema,
    service_registry: ServiceRegistry = Depends(get_service_registry_optional)
):
    """
    Login user dan return access token
    
    **Parameters:**
    - username: User username
    - password: User password
    - remember_me: Extended session (optional)
    
    **Returns:**
    - access_token: JWT access token
    - refresh_token: JWT refresh token
    - user: User profile data
    """
    try:
        # Get client info
        ip_address = request.client.host
        user_agent = request.headers.get("user-agent", "")
        
        # Authenticate user
        auth_result = service_registry.auth_service.authenticate_user(
            username=login_data.username,
            password=login_data.password,
            ip_address=ip_address,
            user_agent=user_agent,
            remember_me=login_data.remember_me
        )
        
        return APIResponse.success(
            data=auth_result,
            message="Login successful"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

@router.post("/refresh", response_model=Dict[str, Any])
async def refresh_token(
    refresh_data: TokenRefreshSchema,
    service_registry: ServiceRegistry = Depends(get_service_registry_optional)
):
    """
    Refresh access token menggunakan refresh token
    
    **Parameters:**
    - refresh_token: JWT refresh token
    
    **Returns:**
    - access_token: New JWT access token
    """
    try:
        token_result = service_registry.auth_service.refresh_access_token(
            refresh_token=refresh_data.refresh_token
        )
        
        return APIResponse.success(
            data=token_result,
            message="Token refreshed successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

@router.post("/logout")
async def logout(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    service_registry: ServiceRegistry = Depends(get_service_registry_optional)
):
    """
    Logout user dan invalidate session
    """
    try:
        # Extract session info from token
        token_data = service_registry.auth_service.verify_access_token(
            credentials.credentials
        )
        
        # Get client info
        ip_address = request.client.host
        user_agent = request.headers.get("user-agent", "")
        
        # Logout user
        service_registry.auth_service.logout_user(
            session_id=token_data['session_id'],
            user_id=token_data['user_id'],
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return APIResponse.success(message="Logout successful")
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/me")
async def get_current_user_profile(
    service_registry: ServiceRegistry = Depends(get_service_registry_optional),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get current user profile
    """
    try:
        # Verify token and get user info
        token_data = service_registry.auth_service.verify_access_token(
            credentials.credentials
        )
        
        # Get full user profile
        user_profile = service_registry.user_service.get_user_profile(
            token_data['user_id']
        )
        
        return APIResponse.success(
            data=user_profile,
            message="User profile retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

@router.post("/change-password")
async def change_password(
    request: Request,
    password_data: Dict[str, str],
    service_registry: ServiceRegistry = Depends(get_service_registry_optional),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Change user password
    
    **Parameters:**
    - current_password: Current password
    - new_password: New password
    """
    try:
        # Verify token
        token_data = service_registry.auth_service.verify_access_token(
            credentials.credentials
        )
        
        # Change password
        result = service_registry.user_service.change_password(
            user_id=token_data['user_id'],
            current_password=password_data['current_password'],
            new_password=password_data['new_password']
        )
        
        return APIResponse.success(
            data=result,
            message="Password changed successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/forgot-password")
async def forgot_password(
    reset_data: Dict[str, str],
    service_registry: ServiceRegistry = Depends(get_service_registry_optional)
):
    """
    Initiate password reset
    
    **Parameters:**
    - username_or_email: Username atau email
    """
    try:
        result = service_registry.user_service.reset_password(
            username_or_email=reset_data['username_or_email']
        )
        
        return APIResponse.success(
            message="Password reset instructions sent to your email"
        )
        
    except Exception as e:
        # Don't reveal if user exists or not
        return APIResponse.success(
            message="If the account exists, password reset instructions have been sent"
        )

@router.post("/reset-password")
async def reset_password(
    reset_data: Dict[str, str],
    service_registry: ServiceRegistry = Depends(get_service_registry_optional)
):
    """
    Confirm password reset dengan token
    
    **Parameters:**
    - reset_token: Password reset token
    - new_password: New password
    """
    try:
        result = service_registry.user_service.confirm_password_reset(
            reset_token=reset_data['reset_token'],
            new_password=reset_data['new_password']
        )
        
        return APIResponse.success(
            data=result,
            message="Password reset successful"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/verify-token")
async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    service_registry: ServiceRegistry = Depends(get_service_registry_optional)
):
    """
    Verify if access token is valid
    """
    try:
        token_data = service_registry.auth_service.verify_access_token(
            credentials.credentials
        )
        
        return APIResponse.success(
            data={
                "valid": True,
                "user_id": token_data['user_id'],
                "username": token_data['username'],
                "role": token_data['role']
            },
            message="Token is valid"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )