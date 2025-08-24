from fastapi import APIRouter, Depends, status, Query
from typing import List, Optional

from app.dependencies import get_service_registry
from app.responses import APIResponse
from app.services import ServiceRegistry
from app.schemas.priority_level import PriorityLevelSchema, PriorityLevelCreateSchema, PriorityLevelUpdateSchema

priority_level_router = APIRouter()

@priority_level_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new priority level"
)
def create_priority_level(
    data: PriorityLevelCreateSchema,
    services: ServiceRegistry = Depends(get_service_registry)
):
    new_item = services.priority_level.create(data.dict())
    return APIResponse.success(data=new_item, message="Priority Level created successfully")

@priority_level_router.get(
    "/",
    summary="Get a list of priority levels"
)
def get_all_priority_levels(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    services: ServiceRegistry = Depends(get_service_registry)
):
    items, total = services.priority_level.get_paginated(page=page, per_page=per_page)
    return APIResponse.paginated(data=items, total=total, page=page, per_page=per_page)

@priority_level_router.get(
    "/{item_id}",
    summary="Get a single priority level"
)
def get_priority_level_by_id(
    item_id: int,
    services: ServiceRegistry = Depends(get_service_registry)
):
    item = services.priority_level.get(item_id)
    return APIResponse.success(data=item)

@priority_level_router.put(
    "/{item_id}",
    summary="Update a priority level"
)
def update_priority_level(
    item_id: int,
    data: PriorityLevelUpdateSchema,
    services: ServiceRegistry = Depends(get_service_registry)
):
    updated_item = services.priority_level.update(
        entity_id=item_id,
        data=data.dict(exclude_unset=True)
    )
    return APIResponse.success(data=updated_item, message="Priority Level updated successfully")

@priority_level_router.delete(
    "/{item_id}",
    summary="Delete a priority level"
)
def delete_priority_level(
    item_id: int,
    services: ServiceRegistry = Depends(get_service_registry)
):
    services.priority_level.delete(item_id)
    return APIResponse.success(message="Priority Level deleted successfully")
