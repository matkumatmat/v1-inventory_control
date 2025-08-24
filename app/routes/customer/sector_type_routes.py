from fastapi import APIRouter, Depends, status, Query
from typing import List, Optional

from app.dependencies import get_service_registry
from app.responses import APIResponse
from app.services import ServiceRegistry
from app.schemas.sector_type import SectorTypeSchema, SectorTypeCreateSchema, SectorTypeUpdateSchema

sector_type_router = APIRouter()

@sector_type_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new sector type"
)
def create_sector_type(
    data: SectorTypeCreateSchema,
    services: ServiceRegistry = Depends(get_service_registry)
):
    new_item = services.sector_type.create(data.dict())
    return APIResponse.success(data=new_item, message="Sector Type created successfully")

@sector_type_router.get(
    "/",
    summary="Get a list of sector types"
)
def get_all_sector_types(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    services: ServiceRegistry = Depends(get_service_registry)
):
    items, total = services.sector_type.get_paginated(page=page, per_page=per_page)
    return APIResponse.paginated(data=items, total=total, page=page, per_page=per_page)

@sector_type_router.get(
    "/{item_id}",
    summary="Get a single sector type"
)
def get_sector_type_by_id(
    item_id: int,
    services: ServiceRegistry = Depends(get_service_registry)
):
    item = services.sector_type.get(item_id)
    return APIResponse.success(data=item)

@sector_type_router.put(
    "/{item_id}",
    summary="Update a sector type"
)
def update_sector_type(
    item_id: int,
    data: SectorTypeUpdateSchema,
    services: ServiceRegistry = Depends(get_service_registry)
):
    updated_item = services.sector_type.update(
        entity_id=item_id,
        data=data.dict(exclude_unset=True)
    )
    return APIResponse.success(data=updated_item, message="Sector Type updated successfully")

@sector_type_router.delete(
    "/{item_id}",
    summary="Delete a sector type"
)
def delete_sector_type(
    item_id: int,
    services: ServiceRegistry = Depends(get_service_registry)
):
    services.sector_type.delete(item_id)
    return APIResponse.success(message="Sector Type deleted successfully")
