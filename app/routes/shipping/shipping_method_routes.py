from fastapi import APIRouter, Depends, status, Query
from typing import List, Optional

from app.dependencies import get_service_registry
from app.responses import APIResponse
from app.services import ServiceRegistry
from app.schemas.shipping_method import ShippingMethodSchema, ShippingMethodCreateSchema, ShippingMethodUpdateSchema

shipping_method_router = APIRouter()

@shipping_method_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new shipping method"
)
def create_shipping_method(
    data: ShippingMethodCreateSchema,
    services: ServiceRegistry = Depends(get_service_registry)
):
    new_item = services.shipping_method.create(data.dict())
    return APIResponse.success(data=new_item, message="Shipping Method created successfully")

@shipping_method_router.get(
    "/",
    summary="Get a list of shipping methods"
)
def get_all_shipping_methods(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    services: ServiceRegistry = Depends(get_service_registry)
):
    items, total = services.shipping_method.get_paginated(page=page, per_page=per_page)
    return APIResponse.paginated(data=items, total=total, page=page, per_page=per_page)

@shipping_method_router.get(
    "/{item_id}",
    summary="Get a single shipping method"
)
def get_shipping_method_by_id(
    item_id: int,
    services: ServiceRegistry = Depends(get_service_registry)
):
    item = services.shipping_method.get(item_id)
    return APIResponse.success(data=item)

@shipping_method_router.put(
    "/{item_id}",
    summary="Update a shipping method"
)
def update_shipping_method(
    item_id: int,
    data: ShippingMethodUpdateSchema,
    services: ServiceRegistry = Depends(get_service_registry)
):
    updated_item = services.shipping_method.update(
        entity_id=item_id,
        data=data.dict(exclude_unset=True)
    )
    return APIResponse.success(data=updated_item, message="Shipping Method updated successfully")

@shipping_method_router.delete(
    "/{item_id}",
    summary="Delete a shipping method"
)
def delete_shipping_method(
    item_id: int,
    services: ServiceRegistry = Depends(get_service_registry)
):
    services.shipping_method.delete(item_id)
    return APIResponse.success(message="Shipping Method deleted successfully")
