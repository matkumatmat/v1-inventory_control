from fastapi import APIRouter, Depends, status, Query
from typing import List, Optional

from app.dependencies import get_service_registry
from app.responses import APIResponse
from app.services import ServiceRegistry
from app.schemas.package_type import PackageTypeSchema, PackageTypeCreateSchema, PackageTypeUpdateSchema

router = APIRouter()

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new package type"
)
def create_package_type(
    data: PackageTypeCreateSchema,
    services: ServiceRegistry = Depends(get_service_registry)
):
    new_item = services.package_type.create(data.dict())
    return APIResponse.success(data=new_item, message="Package Type created successfully")

@router.get(
    "/",
    summary="Get a list of package types"
)
def get_all_package_types(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    services: ServiceRegistry = Depends(get_service_registry)
):
    items, total = services.package_type.get_paginated(page=page, per_page=per_page)
    return APIResponse.paginated(data=items, total=total, page=page, per_page=per_page)

@router.get(
    "/{item_id}",
    summary="Get a single package type"
)
def get_package_type_by_id(
    item_id: int,
    services: ServiceRegistry = Depends(get_service_registry)
):
    item = services.package_type.get(item_id)
    return APIResponse.success(data=item)

@router.put(
    "/{item_id}",
    summary="Update a package type"
)
def update_package_type(
    item_id: int,
    data: PackageTypeUpdateSchema,
    services: ServiceRegistry = Depends(get_service_registry)
):
    updated_item = services.package_type.update(
        entity_id=item_id,
        data=data.dict(exclude_unset=True)
    )
    return APIResponse.success(data=updated_item, message="Package Type updated successfully")

@router.delete(
    "/{item_id}",
    summary="Delete a package type"
)
def delete_package_type(
    item_id: int,
    services: ServiceRegistry = Depends(get_service_registry)
):
    services.package_type.delete(item_id)
    return APIResponse.success(message="Package Type deleted successfully")
