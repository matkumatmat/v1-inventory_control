from fastapi import APIRouter, Depends, status, Query
from typing import List, Optional

from app.dependencies import get_service_registry
from app.responses import APIResponse
from app.services import ServiceRegistry
from app.schemas.customer_type import CustomerTypeSchema, CustomerTypeCreateSchema, CustomerTypeUpdateSchema

customer_type_router = APIRouter()

@customer_type_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new customer type"
)
def create_customer_type(
    data: CustomerTypeCreateSchema,
    services: ServiceRegistry = Depends(get_service_registry)
):
    new_item = services.customer_type.create(data.dict())
    return APIResponse.success(data=new_item, message="Customer Type created successfully")

@customer_type_router.get(
    "/",
    summary="Get a list of customer types"
)
def get_all_customer_types(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    services: ServiceRegistry = Depends(get_service_registry)
):
    items, total = services.customer_type.get_paginated(page=page, per_page=per_page)
    return APIResponse.paginated(data=items, total=total, page=page, per_page=per_page)

@customer_type_router.get(
    "/{item_id}",
    summary="Get a single customer type"
)
def get_customer_type_by_id(
    item_id: int,
    services: ServiceRegistry = Depends(get_service_registry)
):
    item = services.customer_type.get(item_id)
    return APIResponse.success(data=item)

@customer_type_router.put(
    "/{item_id}",
    summary="Update a customer type"
)
def update_customer_type(
    item_id: int,
    data: CustomerTypeUpdateSchema,
    services: ServiceRegistry = Depends(get_service_registry)
):
    updated_item = services.customer_type.update(
        entity_id=item_id,
        data=data.dict(exclude_unset=True)
    )
    return APIResponse.success(data=updated_item, message="Customer Type updated successfully")

@customer_type_router.delete(
    "/{item_id}",
    summary="Delete a customer type"
)
def delete_customer_type(
    item_id: int,
    services: ServiceRegistry = Depends(get_service_registry)
):
    services.customer_type.delete(item_id)
    return APIResponse.success(message="Customer Type deleted successfully")
