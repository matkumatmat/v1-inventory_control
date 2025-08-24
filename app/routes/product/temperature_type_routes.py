from fastapi import APIRouter, Depends, status, Query
from typing import List, Optional

from app.dependencies import get_service_registry
from app.responses import APIResponse
from app.services import ServiceRegistry
from app.schemas.temperature_type import TemperatureTypeSchema, TemperatureTypeCreateSchema, TemperatureTypeUpdateSchema

router = APIRouter()

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new temperature type"
)
def create_temperature_type(
    data: TemperatureTypeCreateSchema,
    services: ServiceRegistry = Depends(get_service_registry)
):
    new_item = services.temperature_type.create(data.dict())
    return APIResponse.success(data=new_item, message="Temperature Type created successfully")

@router.get(
    "/",
    summary="Get a list of temperature types"
)
def get_all_temperature_types(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    services: ServiceRegistry = Depends(get_service_registry)
):
    items, total = services.temperature_type.get_paginated(page=page, per_page=per_page)
    return APIResponse.paginated(data=items, total=total, page=page, per_page=per_page)

@router.get(
    "/{item_id}",
    summary="Get a single temperature type"
)
def get_temperature_type_by_id(
    item_id: int,
    services: ServiceRegistry = Depends(get_service_registry)
):
    item = services.temperature_type.get(item_id)
    return APIResponse.success(data=item)

@router.put(
    "/{item_id}",
    summary="Update a temperature type"
)
def update_temperature_type(
    item_id: int,
    data: TemperatureTypeUpdateSchema,
    services: ServiceRegistry = Depends(get_service_registry)
):
    updated_item = services.temperature_type.update(
        entity_id=item_id,
        data=data.dict(exclude_unset=True)
    )
    return APIResponse.success(data=updated_item, message="Temperature Type updated successfully")

@router.delete(
    "/{item_id}",
    summary="Delete a temperature type"
)
def delete_temperature_type(
    item_id: int,
    services: ServiceRegistry = Depends(get_service_registry)
):
    services.temperature_type.delete(item_id)
    return APIResponse.success(message="Temperature Type deleted successfully")
