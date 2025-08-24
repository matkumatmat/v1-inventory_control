from fastapi import APIRouter, Depends, status, Query
from typing import List, Optional

from app.dependencies import get_service_registry
from app.responses import APIResponse
from app.services import ServiceRegistry
from app.schemas.carrier_type import CarrierTypeSchema, CarrierTypeCreateSchema, CarrierTypeUpdateSchema

carrier_type_router = APIRouter()

@carrier_type_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new carrier type"
)
def create_carrier_type(
    data: CarrierTypeCreateSchema,
    services: ServiceRegistry = Depends(get_service_registry)
):
    new_item = services.carrier_type.create(data.dict())
    return APIResponse.success(data=new_item, message="Carrier Type created successfully")

@carrier_type_router.get(
    "/",
    summary="Get a list of carrier types"
)
def get_all_carrier_types(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    services: ServiceRegistry = Depends(get_service_registry)
):
    items, total = services.carrier_type.get_paginated(page=page, per_page=per_page)
    return APIResponse.paginated(data=items, total=total, page=page, per_page=per_page)

@carrier_type_router.get(
    "/{item_id}",
    summary="Get a single carrier type"
)
def get_carrier_type_by_id(
    item_id: int,
    services: ServiceRegistry = Depends(get_service_registry)
):
    item = services.carrier_type.get(item_id)
    return APIResponse.success(data=item)

@carrier_type_router.put(
    "/{item_id}",
    summary="Update a carrier type"
)
def update_carrier_type(
    item_id: int,
    data: CarrierTypeUpdateSchema,
    services: ServiceRegistry = Depends(get_service_registry)
):
    updated_item = services.carrier_type.update(
        entity_id=item_id,
        data=data.dict(exclude_unset=True)
    )
    return APIResponse.success(data=updated_item, message="Carrier Type updated successfully")

@carrier_type_router.delete(
    "/{item_id}",
    summary="Delete a carrier type"
)
def delete_carrier_type(
    item_id: int,
    services: ServiceRegistry = Depends(get_service_registry)
):
    services.carrier_type.delete(item_id)
    return APIResponse.success(message="Carrier Type deleted successfully")
