from fastapi import APIRouter, Depends, status, Query, Body
from typing import List, Optional

from app.dependencies import get_service_registry
from app.responses import APIResponse
from app.services import ServiceRegistry
from app.schemas.sales import ShippingPlanSchema, ShippingPlanUpdateSchema

shipping_plan_router = APIRouter()

@shipping_plan_router.get(
    "/",
    
    summary="Get a list of shipping plans"
)
def get_all_shipping_plans(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    services: ServiceRegistry = Depends(get_service_registry)
):
    """
    Get a paginated list of shipping plans, with optional filters.
    """
    filters = {}
    if status:
        filters['status'] = status
        
    plans, total = services.shipping_plan.get_paginated(
        page=page,
        per_page=per_page,
        search_term=search,
        filters=filters
    )
    return APIResponse.paginated(data=plans, total=total, page=page, per_page=per_page)

@shipping_plan_router.get(
    "/{plan_id}",
    
    summary="Get a single shipping plan with items"
)
def get_shipping_plan_by_id(
    plan_id: int,
    services: ServiceRegistry = Depends(get_service_registry)
):
    """
    Retrieve a shipping plan and all its line items.
    """
    plan_with_items = services.shipping_plan.get_plan_with_items(plan_id)
    return APIResponse.success(data=plan_with_items)

@shipping_plan_router.post(
    "/{plan_id}/confirm",
    
    summary="Confirm a shipping plan"
)
def confirm_shipping_plan(
    plan_id: int,
    services: ServiceRegistry = Depends(get_service_registry)
):
    """
    Confirm a 'DRAFT' shipping plan. This action triggers the
    auto-allocation of inventory based on FEFO strategy.
    """
    confirmed_plan = services.shipping_plan.confirm_plan(plan_id)
    return APIResponse.success(data=confirmed_plan, message="Shipping plan confirmed and sent for allocation")

@shipping_plan_router.post(
    "/{plan_id}/allocate",
    
    summary="Manually trigger allocation for a shipping plan"
)
def allocate_shipping_plan_items(
    plan_id: int,
    strategy: str = Body("FEFO", embed=True),
    services: ServiceRegistry = Depends(get_service_registry)
):
    """
    Manually trigger the allocation of stock for a 'CONFIRMED' plan.
    This is also triggered automatically when a plan is confirmed.
    """
    allocation_result = services.shipping_plan.allocate_plan_items(plan_id, allocation_strategy=strategy)
    return APIResponse.success(data=allocation_result, message="Allocation process completed")
