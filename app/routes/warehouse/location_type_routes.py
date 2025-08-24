from fastapi import APIRouter, Depends, status, Query
from typing import List, Optional

from app.dependencies import get_service_registry
from app.responses import APIResponse
from app.services import ServiceRegistry
from app.schemas.location_type import LocationTypeSchema, LocationTypeCreateSchema, LocationTypeUpdateSchema

location_type_router = APIRouter()

@location_type_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new location type"
)
def create_location_type(
    data: LocationTypeCreateSchema,
    services: ServiceRegistry = Depends(get_service_registry)
):
    new_item = services.location_type.create(data.dict())
    return APIResponse.success(data=new_item, message="Location Type created successfully")

@location_type_router.get(
    "/",
    summary="Get a list of location types"
)
def get_all_location_types(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    services: ServiceRegistry = Depends(get_service_registry)
):
    items, total = services.location_type.get_paginated(page=page, per_page=per_page)
    return APIResponse.paginated(data=items, total=total, page=page, per_page=per_page)

@location_type_router.get(
    "/{item_id}",
    summary="Get a single location type"
)
def get_location_type_by_id(
    item_id: int,
    services: ServiceRegistry = Depends(get_service_registry)
):
    item = services.location_type.get(item_id)
    return APIResponse.success(data=item)

@location_type_router.put(
    "/{item_id}",
    summary="Update a location type"
)
def update_location_type(
    item_id: int,
    data: LocationTypeUpdateSchema,
    services: ServiceRegistry = Depends(get_service_registry)
):
    updated_item = services.location_type.update(
        entity_id=item_id,
        data=data.dict(exclude_unset=True)
    )
    return APIResponse.success(data=updated_item, message="Location Type updated successfully")

@location_type_router.delete(
    "/{item_id}",
    summary="Delete a location type"
)
def delete_location_type(
    item_id: int,
    services: ServiceRegistry = Depends(get_service_registry)
):
    services.location_type.delete(item_id)
    return APIResponse.success(message="Location Type deleted successfully")
