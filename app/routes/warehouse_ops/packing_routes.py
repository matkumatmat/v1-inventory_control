from fastapi import APIRouter, Depends, status, Query, Body
from typing import List, Optional

from app import APIResponse, get_service_registry
from app.services import ServiceRegistry
from app.schemas.packing import (
    PackingOrderSchema, PackingBoxSchema, PackingBoxCreateSchema,
    PackingBoxItemSchema, PackingBoxItemCreateSchema
)

packing_router = APIRouter()

# --- Packing Order Routes ---

@packing_router.post(
    "/from-picking-list/{picking_list_id}",
    response_model=APIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a Packing Order from a Picking List"
)
def create_packing_order(
    picking_list_id: int,
    packer_user_id: Optional[str] = Body(None, embed=True),
    services: ServiceRegistry = Depends(get_service_registry)
):
    """
    Create a new Packing Order from a 'COMPLETED' Picking List.
    """
    new_order = services.packing_order.create_from_picking_list(picking_list_id, packer_user_id)
    return APIResponse.success(data=new_order, message="Packing order created successfully")

@packing_router.get(
    "/",
    response_model=APIResponse,
    summary="Get a list of packing orders"
)
def get_all_packing_orders(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    services: ServiceRegistry = Depends(get_service_registry)
):
    """
    Get a paginated list of packing orders.
    """
    filters = {'status': status} if status else {}
    orders, total = services.packing_order.get_paginated(page=page, per_page=per_page, filters=filters)
    return APIResponse.paginated(data=orders, total=total, page=page, per_page=per_page)

@packing_router.get(
    "/{order_id}",
    response_model=APIResponse,
    summary="Get a single packing order with boxes"
)
def get_packing_order_by_id(
    order_id: int,
    services: ServiceRegistry = Depends(get_service_registry)
):
    """
    Retrieve a packing order and all its packed boxes.
    """
    order_with_boxes = services.packing_order.get_packing_order_with_boxes(order_id)
    return APIResponse.success(data=order_with_boxes)

@packing_router.post(
    "/{order_id}/assign",
    response_model=APIResponse,
    summary="Assign a packer to a packing order"
)
def assign_packer_to_order(
    order_id: int,
    packer_user_id: str = Body(..., embed=True),
    services: ServiceRegistry = Depends(get_service_registry)
):
    """
    Assign a warehouse operator (packer) to an unassigned packing order.
    """
    assigned_order = services.packing_order.assign_packer(order_id, packer_user_id)
    return APIResponse.success(data=assigned_order, message="Packer assigned successfully")

@packing_router.post(
    "/{order_id}/start",
    response_model=APIResponse,
    summary="Start a packing order"
)
def start_packing_order(
    order_id: int,
    services: ServiceRegistry = Depends(get_service_registry)
):
    """
    Mark an 'ASSIGNED' packing order as 'IN_PROGRESS'.
    """
    started_order = services.packing_order.start_packing(order_id)
    return APIResponse.success(data=started_order, message="Packing process started")

@packing_router.post(
    "/{order_id}/complete",
    response_model=APIResponse,
    summary="Complete a packing order"
)
def complete_packing_order(
    order_id: int,
    completion_notes: Optional[str] = Body(None, embed=True),
    services: ServiceRegistry = Depends(get_service_registry)
):
    """
    Mark an 'IN_PROGRESS' packing order as 'COMPLETED'.
    This signifies that all items are in sealed boxes and ready for shipment.
    """
    completed_order = services.packing_order.complete_packing(order_id, completion_notes)
    return APIResponse.success(data=completed_order, message="Packing order completed and ready for shipment")

# --- Packing Box Routes ---

@packing_router.post(
    "/{order_id}/boxes",
    response_model=APIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new packing box"
)
def create_packing_box(
    order_id: int,
    box_data: PackingBoxCreateSchema,
    services: ServiceRegistry = Depends(get_service_registry)
):
    """
    Create a new, empty packing box for an 'IN_PROGRESS' packing order.
    """
    new_box = services.packing_box.create_box(order_id, box_data.dict())
    return APIResponse.success(data=new_box, message="Packing box created")

@packing_router.post(
    "/boxes/{box_id}/items",
    response_model=APIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add an item to a packing box"
)
def add_item_to_box(
    box_id: int,
    item_data: PackingBoxItemCreateSchema,
    services: ServiceRegistry = Depends(get_service_registry)
):
    """
    Add a picked item (by its allocation ID) into a specific packing box.
    """
    new_item = services.packing_box.add_item_to_box(box_id, item_data.dict())
    return APIResponse.success(data=new_item, message="Item added to box")

@packing_router.post(
    "/boxes/{box_id}/seal",
    response_model=APIResponse,
    summary="Seal a packing box"
)
def seal_packing_box(
    box_id: int,
    final_weight: Optional[float] = Body(None, embed=True),
    services: ServiceRegistry = Depends(get_service_registry)
):
    """
    Seal a packing box, making it read-only.
    Optionally, the final weight can be recorded.
    """
    sealed_box = services.packing_box.seal_box(box_id, final_weight)
    return APIResponse.success(data=sealed_box, message="Box has been sealed")
