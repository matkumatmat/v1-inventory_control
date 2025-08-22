"""
Allocation Routes
=================

MOST CRITICAL ROUTES - Core WMS allocation engine
FIFO/FEFO algorithms dan stock management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, List, Optional

from ...services import ServiceRegistry
from ...schemas import AllocationSchema, AllocationCreateSchema, AllocationUpdateSchema
from .. import get_service_registry, APIResponse

router = APIRouter()

@router.get("", response_model=Dict[str, Any])
async def get_allocations(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    batch_id: Optional[int] = Query(None),
    customer_id: Optional[int] = Query(None),
    allocation_type_id: Optional[int] = Query(None),
    status: Optional[str] = Query("active"),
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """
    Get allocations dengan filtering
    
    **Query Parameters:**
    - batch_id: Filter by specific batch
    - customer_id: Filter by customer
    - allocation_type_id: Filter by allocation type (1=Regular, 2=Tender, 3=Consignment)
    - status: Filter by status (active, shipped, cancelled)
    """
    try:
        # Build filters
        filters = {}
        if batch_id:
            filters['batch_id'] = batch_id
        if customer_id:
            filters['customer_id'] = customer_id
        if allocation_type_id:
            filters['allocation_type_id'] = allocation_type_id
        if status:
            filters['status'] = status
        
        # Get allocations
        result = service_registry.allocation_service.get_all(
            page=page,
            per_page=per_page,
            filters=filters
        )
        
        return APIResponse.paginated(
            data=result['items'],
            total=result['total'],
            page=page,
            per_page=per_page,
            message="Allocations retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("", response_model=Dict[str, Any])
async def create_allocation(
    allocation_data: AllocationCreateSchema,
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """
    Create new allocation
    
    **CRITICAL OPERATION - Core WMS function**
    - Validates stock availability
    - Applies business rules
    - Updates inventory
    - Triggers workflow
    """
    try:
        allocation = service_registry.allocation_service.create_allocation(
            allocation_data.dict()
        )
        
        return APIResponse.success(
            data=allocation,
            message="Allocation created successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/auto-allocate")
async def auto_allocate(
    auto_allocation_data: Dict[str, Any],
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """
    Auto-allocate stock menggunakan FIFO/FEFO algorithm
    
    **CRITICAL FEATURE - Intelligent allocation:**
    - FIFO (First In, First Out)
    - FEFO (First Expired, First Out)  
    - Business rule compliance
    - Optimal stock utilization
    """
    try:
        # Extract parameters
        product_id = auto_allocation_data['product_id']
        quantity = auto_allocation_data['quantity']
        allocation_type_id = auto_allocation_data['allocation_type_id']
        customer_id = auto_allocation_data.get('customer_id')
        strategy = auto_allocation_data.get('strategy', 'FEFO')  # FIFO or FEFO
        
        # Perform auto-allocation
        allocations = service_registry.allocation_service.auto_allocate_by_strategy(
            product_id=product_id,
            quantity=quantity,
            allocation_type_id=allocation_type_id,
            customer_id=customer_id,
            strategy=strategy
        )
        
        return APIResponse.success(
            data=allocations,
            message=f"Auto-allocation completed using {strategy} strategy"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{allocation_id}", response_model=Dict[str, Any])
async def get_allocation(
    allocation_id: int,
    include_movements: bool = Query(False),
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """
    Get allocation by ID
    
    **Query Parameters:**
    - include_movements: Include stock movement history
    """
    try:
        if include_movements:
            allocation = service_registry.allocation_service.get_allocation_with_movements(
                allocation_id
            )
        else:
            allocation = service_registry.allocation_service.get_by_id(allocation_id)
        
        return APIResponse.success(
            data=allocation,
            message="Allocation retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.put("/{allocation_id}", response_model=Dict[str, Any])
async def update_allocation(
    allocation_id: int,
    allocation_data: AllocationUpdateSchema,
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """
    Update allocation
    
    **Restricted operations:**
    - Cannot reduce below shipped quantity
    - Business rule validation
    """
    try:
        allocation = service_registry.allocation_service.update_allocation(
            allocation_id, 
            allocation_data.dict(exclude_unset=True)
        )
        
        return APIResponse.success(
            data=allocation,
            message="Allocation updated successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{allocation_id}/ship")
async def ship_allocation(
    allocation_id: int,
    shipment_data: Dict[str, Any],
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """
    Ship allocation (mark as shipped)
    
    **CRITICAL OPERATION:**
    - Updates shipped quantity
    - Creates stock movement
    - Triggers downstream processes
    """
    try:
        allocation = service_registry.allocation_service.ship_allocation(
            allocation_id=allocation_id,
            quantity=shipment_data['quantity'],
            reference_type=shipment_data.get('reference_type', 'MANUAL'),
            reference_id=shipment_data.get('reference_id')
        )
        
        return APIResponse.success(
            data=allocation,
            message="Allocation shipped successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{allocation_id}/reserve")
async def reserve_allocation(
    allocation_id: int,
    reservation_data: Dict[str, Any],
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """
    Reserve allocation for picking/packing
    
    **Workflow operation:**
    - Marks stock as reserved
    - Prevents other allocations
    - Supports picking process
    """
    try:
        allocation = service_registry.allocation_service.reserve_for_picking(
            allocation_id=allocation_id,
            quantity=reservation_data['quantity']
        )
        
        return APIResponse.success(
            data=allocation,
            message="Allocation reserved for picking"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{allocation_id}/release-reservation")
async def release_reservation(
    allocation_id: int,
    release_data: Dict[str, Any],
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """Release reservation (cancel picking reservation)"""
    try:
        allocation = service_registry.allocation_service.release_reservation(
            allocation_id=allocation_id,
            quantity=release_data['quantity']
        )
        
        return APIResponse.success(
            data=allocation,
            message="Reservation released successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{allocation_id}/cancel")
async def cancel_allocation(
    allocation_id: int,
    cancellation_data: Dict[str, Any],
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """
    Cancel allocation
    
    **Validation:**
    - Cannot cancel shipped allocations
    - Returns stock to available pool
    """
    try:
        allocation = service_registry.allocation_service.cancel_allocation(
            allocation_id=allocation_id,
            reason=cancellation_data.get('reason', 'Manual cancellation')
        )
        
        return APIResponse.success(
            data=allocation,
            message="Allocation cancelled successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/batch/{batch_id}")
async def get_allocations_by_batch(
    batch_id: int,
    include_inactive: bool = Query(False),
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """Get all allocations untuk specific batch"""
    try:
        allocations = service_registry.allocation_service.get_allocations_by_batch(
            batch_id=batch_id,
            include_inactive=include_inactive
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

@router.get("/customer/{customer_id}")
async def get_allocations_by_customer(
    customer_id: int,
    status: Optional[str] = Query(None),
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """Get all allocations untuk specific customer"""
    try:
        allocations = service_registry.allocation_service.get_allocations_by_customer(
            customer_id=customer_id,
            status=status
        )
        
        return APIResponse.success(
            data=allocations,
            message="Customer allocations retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/product/{product_id}")
async def get_allocations_by_product(
    product_id: int,
    status: Optional[str] = Query("active"),
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """Get all allocations untuk specific product"""
    try:
        allocations = service_registry.allocation_service.get_allocations_by_product(
            product_id=product_id,
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

@router.get("/available-stock/{product_id}")
async def get_available_stock(
    product_id: int,
    strategy: str = Query("FEFO"),  # FIFO or FEFO
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """
    Get available stock untuk product dengan allocation preview
    
    **Shows:**
    - Available quantities per batch
    - Allocation order (FIFO/FEFO)
    - Expiry information
    - Optimal allocation suggestions
    """
    try:
        available_stock = service_registry.allocation_service.get_available_stock_for_product(
            product_id=product_id,
            strategy=strategy
        )
        
        return APIResponse.success(
            data=available_stock,
            message=f"Available stock retrieved using {strategy} strategy"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/bulk-allocate")
async def bulk_allocate(
    bulk_allocation_data: Dict[str, Any],
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """
    Bulk allocation untuk multiple products
    
    **Use cases:**
    - Sales order fulfillment
    - Tender allocations
    - Bulk customer orders
    """
    try:
        items = bulk_allocation_data['items']  # List of {product_id, quantity, customer_id}
        allocation_type_id = bulk_allocation_data['allocation_type_id']
        strategy = bulk_allocation_data.get('strategy', 'FEFO')
        
        results = []
        for item in items:
            try:
                allocations = service_registry.allocation_service.auto_allocate_by_strategy(
                    product_id=item['product_id'],
                    quantity=item['quantity'],
                    allocation_type_id=allocation_type_id,
                    customer_id=item.get('customer_id'),
                    strategy=strategy
                )
                results.append({
                    'product_id': item['product_id'],
                    'success': True,
                    'allocations': allocations
                })
            except Exception as e:
                results.append({
                    'product_id': item['product_id'],
                    'success': False,
                    'error': str(e)
                })
        
        return APIResponse.success(
            data=results,
            message="Bulk allocation completed"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/reports/utilization")
async def get_allocation_utilization_report(
    product_id: Optional[int] = Query(None),
    customer_id: Optional[int] = Query(None),
    days_back: int = Query(30),
    service_registry: ServiceRegistry = Depends(get_service_registry)
):
    """
    Get allocation utilization report
    
    **Analytics:**
    - Allocation vs shipment rates
    - Customer performance
    - Product movement analysis
    - Efficiency metrics
    """
    try:
        report = service_registry.allocation_service.get_allocation_utilization_report(
            product_id=product_id,
            customer_id=customer_id,
            days_back=days_back
        )
        
        return APIResponse.success(
            data=report,
            message="Allocation utilization report generated successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )