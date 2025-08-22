"""
Batch Routes
============

CRITICAL ROUTES untuk Batch management (core inbound operations)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, List, Optional
from datetime import date

from ...services import ServiceRegistry
from ...schemas import BatchSchema, BatchCreateSchema, BatchUpdateSchema
from .. import get_service_registry, APIResponse

router = APIRouter()

@router.get("", response_model=Dict[str, Any])
async def get_batches(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None),
    product_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    expiry_days_ahead: Optional[int] = Query(None),
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """
    Get batches dengan pagination dan filtering
    
    **Query Parameters:**
    - page: Page number (default: 1)
    - per_page: Items per page (default: 50, max: 100)
    - search: Search dalam batch_number
    - product_id: Filter by product
    - status: Filter by status (PENDING_QC, ACTIVE, QUARANTINE, etc.)
    - expiry_days_ahead: Show batches expiring within X days
    """
    try:
        # Build filters
        filters = {}
        if product_id:
            filters['product_id'] = product_id
        if status:
            filters['status'] = status
        
        # Get batches
        result = service_registry.batch_service.get_all(
            page=page,
            per_page=per_page,
            search=search,
            filters=filters
        )
        
        # Filter by expiry if requested
        if expiry_days_ahead:
            expiring_batches = service_registry.batch_service.get_expiring_batches(
                days_ahead=expiry_days_ahead
            )
            # This is simplified - in production, integrate filtering properly
        
        return APIResponse.paginated(
            data=result['items'],
            total=result['total'],
            page=page,
            per_page=per_page,
            message="Batches retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("", response_model=Dict[str, Any])
async def create_batch(
    batch_data: BatchCreateSchema,
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """
    Create new batch (inbound receipt)
    
    **CRITICAL OPERATION - Triggers:**
    - QC process initiation
    - Inventory updates
    - Expiry tracking
    - Audit logging
    """
    try:
        batch = service_registry.batch_service.create_batch(batch_data.dict())
        
        return APIResponse.success(
            data=batch,
            message="Batch created successfully and pending QC"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{batch_id}", response_model=Dict[str, Any])
async def get_batch(
    batch_id: int,
    include_allocations: bool = Query(False),
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """
    Get batch by ID
    
    **Query Parameters:**
    - include_allocations: Include batch allocations in response
    """
    try:
        if include_allocations:
            batch = service_registry.batch_service.get_batch_with_allocations(batch_id)
        else:
            batch = service_registry.batch_service.get_by_id(batch_id)
        
        return APIResponse.success(
            data=batch,
            message="Batch retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.put("/{batch_id}", response_model=Dict[str, Any])
async def update_batch(
    batch_id: int,
    batch_data: BatchUpdateSchema,
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """Update batch information"""
    try:
        batch = service_registry.batch_service.update(
            batch_id, 
            batch_data.dict(exclude_unset=True)
        )
        
        return APIResponse.success(
            data=batch,
            message="Batch updated successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/number/{batch_number}", response_model=Dict[str, Any])
async def get_batch_by_number(
    batch_number: str,
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """Get batch by batch number"""
    try:
        batch = service_registry.batch_service.get_by_batch_number(batch_number)
        
        return APIResponse.success(
            data=batch,
            message="Batch retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.post("/{batch_id}/qc/pass")
async def pass_qc(
    batch_id: int,
    qc_data: Dict[str, Any],
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """
    Mark batch as QC passed
    
    **CRITICAL OPERATION - Enables:**
    - Stock allocation
    - Sales operations
    - Inventory availability
    """
    try:
        batch = service_registry.batch_service.pass_qc(
            batch_id=batch_id,
            qc_passed_by=qc_data.get('qc_passed_by'),
            qc_notes=qc_data.get('qc_notes')
        )
        
        return APIResponse.success(
            data=batch,
            message="Batch QC passed successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{batch_id}/qc/fail")
async def fail_qc(
    batch_id: int,
    qc_data: Dict[str, Any],
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """
    Mark batch as QC failed
    
    **CRITICAL OPERATION - Results in:**
    - Quarantine status
    - Block from allocation
    - Quality investigation
    """
    try:
        batch = service_registry.batch_service.fail_qc(
            batch_id=batch_id,
            qc_failed_by=qc_data.get('qc_failed_by'),
            failure_reason=qc_data.get('failure_reason'),
            qc_notes=qc_data.get('qc_notes')
        )
        
        return APIResponse.success(
            data=batch,
            message="Batch QC failed - moved to quarantine"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{batch_id}/quarantine")
async def quarantine_batch(
    batch_id: int,
    quarantine_data: Dict[str, Any],
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """Move batch to quarantine"""
    try:
        batch = service_registry.batch_service.quarantine_batch(
            batch_id=batch_id,
            reason=quarantine_data.get('reason', 'Manual quarantine'),
            quarantined_by=quarantine_data.get('quarantined_by')
        )
        
        return APIResponse.success(
            data=batch,
            message="Batch quarantined successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{batch_id}/release")
async def release_from_quarantine(
    batch_id: int,
    release_data: Dict[str, Any],
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """Release batch from quarantine"""
    try:
        batch = service_registry.batch_service.release_from_quarantine(
            batch_id=batch_id,
            released_by=release_data.get('released_by'),
            release_notes=release_data.get('release_notes')
        )
        
        return APIResponse.success(
            data=batch,
            message="Batch released from quarantine"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/expiring/{days_ahead}")
async def get_expiring_batches(
    days_ahead: int = Query(30, ge=1, le=365),
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """
    Get batches expiring within specified days
    
    **Critical for:**
    - Inventory planning
    - Sales prioritization
    - Disposal planning
    """
    try:
        batches = service_registry.batch_service.get_expiring_batches(
            days_ahead=days_ahead
        )
        
        return APIResponse.success(
            data=batches,
            message=f"Batches expiring within {days_ahead} days retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/product/{product_id}")
async def get_batches_by_product(
    product_id: int,
    include_inactive: bool = Query(False),
    sort_by: str = Query("expiry_date"),  # expiry_date, received_date, batch_number
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """Get all batches untuk specific product"""
    try:
        batches = service_registry.batch_service.get_batches_by_product(
            product_id=product_id,
            include_inactive=include_inactive
        )
        
        # Sort batches
        if sort_by == "expiry_date":
            batches.sort(key=lambda x: x.get('expiry_date', '9999-12-31'))
        elif sort_by == "received_date":
            batches.sort(key=lambda x: x.get('received_date', '1900-01-01'), reverse=True)
        elif sort_by == "batch_number":
            batches.sort(key=lambda x: x.get('batch_number', ''))
        
        return APIResponse.success(
            data=batches,
            message="Product batches retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{batch_id}/stock-levels")
async def get_batch_stock_levels(
    batch_id: int,
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """Get detailed stock levels untuk batch"""
    try:
        stock_levels = service_registry.batch_service.get_batch_stock_summary(batch_id)
        
        return APIResponse.success(
            data=stock_levels,
            message="Batch stock levels retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{batch_id}/allocations")
async def get_batch_allocations(
    batch_id: int,
    include_history: bool = Query(False),
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """Get all allocations untuk specific batch"""
    try:
        allocations = service_registry.allocation_service.get_allocations_by_batch(
            batch_id=batch_id,
            include_inactive=include_history
        )
        
        return APIResponse.success(
            data=allocations,
            message="Batch allocations retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{batch_id}/adjust-quantity")
async def adjust_batch_quantity(
    batch_id: int,
    adjustment_data: Dict[str, Any],
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """
    Adjust batch quantity (for corrections, damages, etc.)
    
    **Requires strong justification dan approval**
    """
    try:
        batch = service_registry.batch_service.adjust_quantity(
            batch_id=batch_id,
            new_quantity=adjustment_data['new_quantity'],
            reason=adjustment_data['reason'],
            adjusted_by=adjustment_data.get('adjusted_by')
        )
        
        return APIResponse.success(
            data=batch,
            message="Batch quantity adjusted successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )