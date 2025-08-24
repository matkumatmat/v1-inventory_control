from fastapi import APIRouter, Depends, status, Query
from typing import List, Optional

from app.dependencies import get_service_registry
from app.responses import APIResponse
from app.services import ServiceRegistry
from app.schemas.status_type import StatusTypeSchema, StatusTypeCreateSchema, StatusTypeUpdateSchema

status_type_router = APIRouter()

@status_type_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new status type"
)
def create_status_type(
    data: StatusTypeCreateSchema,
    services: ServiceRegistry = Depends(get_service_registry)
):
    new_item = services.status_type.create(data.dict())
    return APIResponse.success(data=new_item, message="Status Type created successfully")

@status_type_router.get(
    "/",
    summary="Get a list of status types"
)
def get_all_status_types(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    entity_type: Optional[str] = Query(None),
    services: ServiceRegistry = Depends(get_service_registry)
):
    filters = {'entity_type': entity_type} if entity_type else {}
    items, total = services.status_type.get_paginated(page=page, per_page=per_page, filters=filters)
    return APIResponse.paginated(data=items, total=total, page=page, per_page=per_page)

@status_type_router.get(
    "/{item_id}",
    summary="Get a single status type"
)
def get_status_type_by_id(
    item_id: int,
    services: ServiceRegistry = Depends(get_service_registry)
):
    item = services.status_type.get(item_id)
    return APIResponse.success(data=item)

@status_type_router.put(
    "/{item_id}",
    summary="Update a status type"
)
def update_status_type(
    item_id: int,
    data: StatusTypeUpdateSchema,
    services: ServiceRegistry = Depends(get_service_registry)
):
    updated_item = services.status_type.update(
        entity_id=item_id,
        data=data.dict(exclude_unset=True)
    )
    return APIResponse.success(data=updated_item, message="Status Type updated successfully")

@status_type_router.delete(
    "/{item_id}",
    summary="Delete a status type"
)
def delete_status_type(
    item_id: int,
    services: ServiceRegistry = Depends(get_service_registry)
):
    services.status_type.delete(item_id)
    return APIResponse.success(message="Status Type deleted successfully")
