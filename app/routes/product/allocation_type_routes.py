from fastapi import APIRouter, Depends, status, Query
from typing import List, Optional

from app.dependencies import get_service_registry
from app.responses import APIResponse
from app.services import ServiceRegistry
from app.schemas.allocation_type import AllocationTypeSchema, AllocationTypeCreateSchema, AllocationTypeUpdateSchema

router = APIRouter()

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new allocation type"
)
def create_allocation_type(
    data: AllocationTypeCreateSchema,
    services: ServiceRegistry = Depends(get_service_registry)
):
    new_item = services.allocation_type.create(data.dict())
    return APIResponse.success(data=new_item, message="Allocation Type created successfully")

@router.get(
    "/",
    summary="Get a list of allocation types"
)
def get_all_allocation_types(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    services: ServiceRegistry = Depends(get_service_registry)
):
    items, total = services.allocation_type.get_paginated(page=page, per_page=per_page)
    return APIResponse.paginated(data=items, total=total, page=page, per_page=per_page)

@router.get(
    "/{item_id}",
    summary="Get a single allocation type"
)
def get_allocation_type_by_id(
    item_id: int,
    services: ServiceRegistry = Depends(get_service_registry)
):
    item = services.allocation_type.get(item_id)
    return APIResponse.success(data=item)

@router.put(
    "/{item_id}",
    summary="Update an allocation type"
)
def update_allocation_type(
    item_id: int,
    data: AllocationTypeUpdateSchema,
    services: ServiceRegistry = Depends(get_service_registry)
):
    updated_item = services.allocation_type.update(
        entity_id=item_id,
        data=data.dict(exclude_unset=True)
    )
    return APIResponse.success(data=updated_item, message="Allocation Type updated successfully")

@router.delete(
    "/{item_id}",
    summary="Delete an allocation type"
)
def delete_allocation_type(
    item_id: int,
    services: ServiceRegistry = Depends(get_service_registry)
):
    services.allocation_type.delete(item_id)
    return APIResponse.success(message="Allocation Type deleted successfully")
