"""
Product Routes
==============

CRUD routes untuk Product management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, List, Optional

from ...services import ServiceRegistry
from ...schemas import ProductSchema, ProductCreateSchema, ProductUpdateSchema
from ...dependencies import get_service_registry
from ...responses import APIResponse

router = APIRouter()

@router.get("", response_model=Dict[str, Any])
async def get_products(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None),
    product_type_id: Optional[int] = Query(None),
    manufacturer: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(True),
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """
    Get products dengan pagination dan filtering
    
    **Query Parameters:**
    - page: Page number (default: 1)
    - per_page: Items per page (default: 50, max: 100)
    - search: Search dalam product_code, name, generic_name
    - product_type_id: Filter by product type
    - manufacturer: Filter by manufacturer
    - is_active: Filter by status (default: true)
    """
    try:
        # Build filters
        filters = {}
        if product_type_id:
            filters['product_type_id'] = product_type_id
        if manufacturer:
            filters['manufacturer'] = manufacturer
        if is_active is not None:
            filters['is_active'] = is_active
        
        # Get products
        result = service_registry.product_service.get_all(
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
            message="Products retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("", response_model=Dict[str, Any])
async def create_product(
    product_data: ProductCreateSchema,
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """
    Create new product
    
    **Input validation:**
    - product_code: Must be unique
    - name: Required
    - product_type_id: Must exist
    """
    try:
        product = service_registry.product_service.create(product_data.dict())
        
        return APIResponse.success(
            data=product,
            message="Product created successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{product_id}", response_model=Dict[str, Any])
async def get_product(
    product_id: int,
    include_batches: bool = Query(False),
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """
    Get product by ID
    
    **Query Parameters:**
    - include_batches: Include product batches in response
    """
    try:
        if include_batches:
            product = service_registry.product_service.get_product_with_batches(product_id)
        else:
            product = service_registry.product_service.get_by_id(product_id)
        
        return APIResponse.success(
            data=product,
            message="Product retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.put("/{product_id}", response_model=Dict[str, Any])
async def update_product(
    product_id: int,
    product_data: ProductUpdateSchema,
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """Update product"""
    try:
        product = service_registry.product_service.update(
            product_id, 
            product_data.dict(exclude_unset=True)
        )
        
        return APIResponse.success(
            data=product,
            message="Product updated successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{product_id}")
async def delete_product(
    product_id: int,
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """Soft delete product (deactivate)"""
    try:
        service_registry.product_service.delete(product_id)
        
        return APIResponse.success(message="Product deleted successfully")
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/code/{product_code}", response_model=Dict[str, Any])
async def get_product_by_code(
    product_code: str,
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """Get product by product code"""
    try:
        product = service_registry.product_service.get_by_product_code(product_code)
        
        return APIResponse.success(
            data=product,
            message="Product retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.get("/{product_id}/stock-summary")
async def get_product_stock_summary(
    product_id: int,
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """Get comprehensive stock summary untuk product"""
    try:
        stock_summary = service_registry.inventory_service.get_stock_summary_by_product(product_id)
        
        return APIResponse.success(
            data=stock_summary,
            message="Product stock summary retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{product_id}/batches")
async def get_product_batches(
    product_id: int,
    include_inactive: bool = Query(False),
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """Get all batches untuk specific product"""
    try:
        batches = service_registry.batch_service.get_batches_by_product(
            product_id, 
            include_inactive=include_inactive
        )
        
        return APIResponse.success(
            data=batches,
            message="Product batches retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{product_id}/allocations")
async def get_product_allocations(
    product_id: int,
    status: Optional[str] = Query(None),
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """Get all allocations untuk specific product"""
    try:
        allocations = service_registry.allocation_service.get_allocations_by_product(
            product_id,
            status=status
        )
        
        return APIResponse.success(
            data=allocations,
            message="Product allocations retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{product_id}/activate")
async def activate_product(
    product_id: int,
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """Activate product"""
    try:
        product = service_registry.product_service.activate_product(product_id)
        
        return APIResponse.success(
            data=product,
            message="Product activated successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{product_id}/deactivate")
async def deactivate_product(
    product_id: int,
    reason: Dict[str, str],
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """Deactivate product"""
    try:
        product = service_registry.product_service.deactivate_product(
            product_id,
            reason.get('reason', 'Deactivated via API')
        )
        
        return APIResponse.success(
            data=product,
            message="Product deactivated successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )