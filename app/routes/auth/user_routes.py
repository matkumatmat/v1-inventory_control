"""
User Management Routes
======================

Routes untuk user CRUD dan management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, List, Optional

from ...services import ServiceRegistry
from ...schemas import UserSchema, UserCreateSchema, UserUpdateSchema
from ...dependencies import get_service_registry
from ...responses import APIResponse

router = APIRouter()

@router.get("", response_model=Dict[str, Any])
async def get_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """
    Get users dengan pagination dan filtering
    
    **Query Parameters:**
    - page: Page number (default: 1)
    - per_page: Items per page (default: 50, max: 100)
    - search: Search dalam username, email, full_name
    - role: Filter by role
    - is_active: Filter by status
    """
    try:
        # Build filters
        filters = {}
        if role:
            filters['role'] = role
        if is_active is not None:
            filters['is_active'] = is_active
        
        # Get users
        result = await service_registry.user_service.get_user_profile(
            page=page,
            per_page=per_page,
            search=search,
            filters=filters
        )
        
        return APIResponse.paginated(
            data=result['items'],
            total=result['total'],
            page=page,
            per_page=per_page,
            message="Users retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("", response_model=Dict[str, Any])
async def create_user(
    user_data: UserCreateSchema,
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """
    Create new user
    
    **Requires admin role**
    """
    try:
        # Check permission (implement admin check)
        # service_registry.auth_service.require_permission(current_user_id, 'admin')
        
        user = await service_registry.user_service.create(user_data.model_dump())
        
        return APIResponse.success(
            data=user,
            message="User created successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{user_id}", response_model=Dict[str, Any])
async def get_user(
    user_id: int,
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """Get user by ID dengan detail profile"""
    try:
        user = await service_registry.user_service.get_user_profile(user_id)
        
        return APIResponse.success(
            data=user,
            message="User retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.put("/{user_id}", response_model=Dict[str, Any])
async def update_user(
    user_id: int,
    user_data: UserUpdateSchema,
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """Update user"""
    try:
        user = await service_registry.user_service.update(user_id, user_data.dict(exclude_unset=True))
        
        return APIResponse.success(
            data=user,
            message="User updated successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """Soft delete user (deactivate)"""
    try:
        await service_registry.user_service.deactivate_user(user_id, "Deleted via API")
        
        return APIResponse.success(message="User deleted successfully")
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{user_id}/activate")
async def activate_user(
    user_id: int,
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """Activate user account"""
    try:
        user = await service_registry.user_service.activate_user(user_id)
        
        return APIResponse.success(
            data=user,
            message="User activated successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{user_id}/deactivate")
async def deactivate_user(
    user_id: int,
    reason: Dict[str, str],
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """Deactivate user account"""
    try:
        user = await service_registry.user_service.deactivate_user(
            user_id, 
            reason.get('reason', 'Deactivated via API')
        )
        
        return APIResponse.success(
            data=user,
            message="User deactivated successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{user_id}/unlock")
async def unlock_user(
    user_id: int,
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """Unlock user account"""
    try:
        user = await service_registry.user_service.unlock_user(user_id)
        
        return APIResponse.success(
            data=user,
            message="User unlocked successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/role/{role}")
async def get_users_by_role(
    role: str,
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """Get users by role"""
    try:
        users = await service_registry.user_service.get_users_by_role(role)
        
        return APIResponse.success(
            data=users,
            message=f"Users with role '{role}' retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )