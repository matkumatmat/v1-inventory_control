from fastapi import APIRouter, Depends, status, Query, Body
from typing import List, Optional

from app import APIResponse, get_service_registry
from app.services import ServiceRegistry
from app.schemas.sales import (
    SalesOrderSchema, SalesOrderCreateSchema, SalesOrderUpdateSchema,
    SalesOrderItemSchema, SalesOrderItemCreateSchema, SalesOrderItemUpdateSchema
)

sales_router = APIRouter()

@sales_router.post(
    "/",
    response_model=APIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new sales order"
)
def create_sales_order(
    so_data: SalesOrderCreateSchema,
    services: ServiceRegistry = Depends(get_service_registry)
):
    """
    Create a new sales order. The initial status will be 'PENDING'.
    """
    new_so = services.sales_order.create(so_data.dict())
    return APIResponse.success(data=new_so, message="Sales order created successfully")

@sales_router.get(
    "/",
    response_model=APIResponse,
    summary="Get a list of sales orders"
)
def get_all_sales_orders(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    customer_id: Optional[int] = Query(None),
    services: ServiceRegistry = Depends(get_service_registry)
):
    """
    Get a paginated list of sales orders, with optional filters.
    """
    filters = {}
    if status:
        filters['status'] = status
    if customer_id:
        filters['customer_id'] = customer_id
        
    orders, total = services.sales_order.get_paginated(
        page=page,
        per_page=per_page,
        search_term=search,
        filters=filters
    )
    return APIResponse.paginated(data=orders, total=total, page=page, per_page=per_page)

@sales_router.get(
    "/{so_id}",
    response_model=APIResponse,
    summary="Get a single sales order with items"
)
def get_sales_order_by_id(
    so_id: int,
    services: ServiceRegistry = Depends(get_service_registry)
):
    """
    Retrieve a sales order and all its line items.
    """
    so_with_items = services.sales_order.get_so_with_items(so_id)
    return APIResponse.success(data=so_with_items)

@sales_router.post(
    "/{so_id}/items",
    response_model=APIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add an item to a sales order"
)
def add_item_to_sales_order(
    so_id: int,
    item_data: SalesOrderItemCreateSchema,
    services: ServiceRegistry = Depends(get_service_registry)
):
    """
    Add a new line item to a 'PENDING' or 'CONFIRMED' sales order.
    """
    new_item = services.sales_order.add_item(so_id, item_data.dict())
    return APIResponse.success(data=new_item, message="Item added successfully")

@sales_router.put(
    "/items/{item_id}",
    response_model=APIResponse,
    summary="Update a sales order item"
)
def update_sales_order_item(
    item_id: int,
    item_data: SalesOrderItemUpdateSchema,
    services: ServiceRegistry = Depends(get_service_registry)
):
    """
    Update an existing line item in a sales order.
    """
    updated_item = services.sales_order.update_item(
        item_id,
        item_data.dict(exclude_unset=True)
    )
    return APIResponse.success(data=updated_item, message="Item updated successfully")

@sales_router.post(
    "/{so_id}/confirm",
    response_model=APIResponse,
    summary="Confirm a sales order"
)
def confirm_sales_order(
    so_id: int,
    services: ServiceRegistry = Depends(get_service_registry)
):
    """
    Confirm a 'PENDING' sales order. This action is irreversible and
    triggers the creation of a shipping plan.
    """
    confirmed_so = services.sales_order.confirm_order(so_id)
    return APIResponse.success(data=confirmed_so, message="Sales order confirmed and sent for planning")

@sales_router.post(
    "/{so_id}/cancel",
    response_model=APIResponse,
    summary="Cancel a sales order"
)
def cancel_sales_order(
    so_id: int,
    reason: str = Body("No reason provided", embed=True),
    services: ServiceRegistry = Depends(get_service_registry)
):
    """
    Cancel a sales order. Cannot be done if the order has shipped items.
    """
    cancelled_so = services.sales_order.cancel_order(so_id, reason)
    return APIResponse.success(data=cancelled_so, message="Sales order cancelled")
