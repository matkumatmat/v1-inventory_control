from fastapi import APIRouter, Depends, status, Query, Body
from typing import List, Optional

from app import APIResponse, get_service_registry
from app.services import ServiceRegistry
from app.schemas.picking import PickingListSchema, PickingListItemSchema

picking_router = APIRouter()

@picking_router.post(
    "/from-shipping-plan/{plan_id}",
    response_model=APIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a Picking List from a Shipping Plan"
)
def create_picking_list(
    plan_id: int,
    picker_user_id: Optional[str] = Body(None, embed=True),
    services: ServiceRegistry = Depends(get_service_registry)
):
    """
    Create a new Picking List from a confirmed and allocated Shipping Plan.
    """
    new_list = services.picking_list.create_from_shipping_plan(plan_id, picker_user_id)
    return APIResponse.success(data=new_list, message="Picking list created successfully")

@picking_router.get(
    "/",
    response_model=APIResponse,
    summary="Get a list of picking lists"
)
def get_all_picking_lists(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    picker_user_id: Optional[str] = Query(None),
    services: ServiceRegistry = Depends(get_service_registry)
):
    """
    Get a paginated list of picking lists, with optional filters.
    """
    filters = {}
    if status:
        filters['status'] = status
    if picker_user_id:
        filters['picker_user_id'] = picker_user_id

    lists, total = services.picking_list.get_paginated(
        page=page,
        per_page=per_page,
        filters=filters
    )
    return APIResponse.paginated(data=lists, total=total, page=page, per_page=per_page)

@picking_router.get(
    "/{list_id}",
    response_model=APIResponse,
    summary="Get a single picking list with items"
)
def get_picking_list_by_id(
    list_id: int,
    services: ServiceRegistry = Depends(get_service_registry)
):
    """
    Retrieve a picking list and all its line items, sorted by rack location.
    """
    list_with_items = services.picking_list.get_picking_list_with_items(list_id)
    return APIResponse.success(data=list_with_items)

@picking_router.post(
    "/{list_id}/assign",
    response_model=APIResponse,
    summary="Assign a picker to a picking list"
)
def assign_picker_to_list(
    list_id: int,
    picker_user_id: str = Body(..., embed=True),
    services: ServiceRegistry = Depends(get_service_registry)
):
    """
    Assign a warehouse operator (picker) to an unassigned picking list.
    """
    assigned_list = services.picking_list.assign_picker(list_id, picker_user_id)
    return APIResponse.success(data=assigned_list, message="Picker assigned successfully")

@picking_router.post(
    "/{list_id}/start",
    response_model=APIResponse,
    summary="Start a picking list"
)
def start_picking_list(
    list_id: int,
    services: ServiceRegistry = Depends(get_service_registry)
):
    """
    Mark an 'ASSIGNED' picking list as 'IN_PROGRESS'.
    """
    started_list = services.picking_list.start_picking(list_id)
    return APIResponse.success(data=started_list, message="Picking process started")

@picking_router.put(
    "/items/{item_id}/pick",
    response_model=APIResponse,
    summary="Update a picked item's quantity"
)
def update_picked_item(
    item_id: int,
    quantity_picked: int = Body(..., embed=True),
    picker_notes: Optional[str] = Body(None, embed=True),
    services: ServiceRegistry = Depends(get_service_registry)
):
    """
    Update the quantity that has been physically picked for a single item on a list.
    This is the primary action for a picker.
    """
    updated_item = services.picking_list.update_item_picked_quantity(
        item_id, quantity_picked, picker_notes
    )
    return APIResponse.success(data=updated_item, message="Picked quantity updated")

@picking_router.post(
    "/{list_id}/complete",
    response_model=APIResponse,
    summary="Complete a picking list"
)
def complete_picking_list(
    list_id: int,
    completion_notes: Optional[str] = Body(None, embed=True),
    services: ServiceRegistry = Depends(get_service_registry)
):
    """
    Mark an 'IN_PROGRESS' picking list as 'COMPLETED'.
    Requires all items to have their picked quantity recorded.
    """
    completed_list = services.picking_list.complete_picking(list_id, completion_notes)
    return APIResponse.success(data=completed_list, message="Picking list completed")
