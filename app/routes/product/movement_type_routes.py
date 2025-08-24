from fastapi import APIRouter, Depends, status, Query
from typing import List, Optional

from app.dependencies import get_service_registry
from app.responses import APIResponse
from app.services import ServiceRegistry
from app.schemas.movement_type import MovementTypeSchema, MovementTypeCreateSchema, MovementTypeUpdateSchema

router = APIRouter()

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new movement type"
)
def create_movement_type(
    data: MovementTypeCreateSchema,
    services: ServiceRegistry = Depends(get_service_registry)
):
    new_item = services.movement_type.create(data.dict())
    return APIResponse.success(data=new_item, message="Movement Type created successfully")

@router.get(
    "/",
    summary="Get a list of movement types"
)
def get_all_movement_types(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    services: ServiceRegistry = Depends(get_service_registry)
):
    items, total = services.movement_type.get_paginated(page=page, per_page=per_page)
    return APIResponse.paginated(data=items, total=total, page=page, per_page=per_page)

@router.get(
    "/{item_id}",
    summary="Get a single movement type"
)
def get_movement_type_by_id(
    item_id: int,
    services: ServiceRegistry = Depends(get_service_registry)
):
    item = services.movement_type.get(item_id)
    return APIResponse.success(data=item)

@router.put(
    "/{item_id}",
    summary="Update a movement type"
)
def update_movement_type(
    item_id: int,
    data: MovementTypeUpdateSchema,
    services: ServiceRegistry = Depends(get_service_registry)
):
    updated_item = services.movement_type.update(
        entity_id=item_id,
        data=data.dict(exclude_unset=True)
    )
    return APIResponse.success(data=updated_item, message="Movement Type updated successfully")

@router.delete(
    "/{item_id}",
    summary="Delete a movement type"
)
def delete_movement_type(
    item_id: int,
    services: ServiceRegistry = Depends(get_service_registry)
):
    services.movement_type.delete(item_id)
    return APIResponse.success(message="Movement Type deleted successfully")
