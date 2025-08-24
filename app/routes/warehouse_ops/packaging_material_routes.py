from fastapi import APIRouter, Depends, status, Query
from typing import List, Optional

from app.dependencies import get_service_registry
from app.responses import APIResponse
from app.services import ServiceRegistry
from app.schemas.packaging_material import PackagingMaterialSchema, PackagingMaterialCreateSchema, PackagingMaterialUpdateSchema

packaging_material_router = APIRouter()

@packaging_material_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new packaging material"
)
def create_packaging_material(
    data: PackagingMaterialCreateSchema,
    services: ServiceRegistry = Depends(get_service_registry)
):
    new_item = services.packaging_material.create(data.dict())
    return APIResponse.success(data=new_item, message="Packaging Material created successfully")

@packaging_material_router.get(
    "/",
    summary="Get a list of packaging materials"
)
def get_all_packaging_materials(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    services: ServiceRegistry = Depends(get_service_registry)
):
    items, total = services.packaging_material.get_paginated(page=page, per_page=per_page)
    return APIResponse.paginated(data=items, total=total, page=page, per_page=per_page)

@packaging_material_router.get(
    "/{item_id}",
    summary="Get a single packaging material"
)
def get_packaging_material_by_id(
    item_id: int,
    services: ServiceRegistry = Depends(get_service_registry)
):
    item = services.packaging_material.get(item_id)
    return APIResponse.success(data=item)

@packaging_material_router.put(
    "/{item_id}",
    summary="Update a packaging material"
)
def update_packaging_material(
    item_id: int,
    data: PackagingMaterialUpdateSchema,
    services: ServiceRegistry = Depends(get_service_registry)
):
    updated_item = services.packaging_material.update(
        entity_id=item_id,
        data=data.dict(exclude_unset=True)
    )
    return APIResponse.success(data=updated_item, message="Packaging Material updated successfully")

@packaging_material_router.delete(
    "/{item_id}",
    summary="Delete a packaging material"
)
def delete_packaging_material(
    item_id: int,
    services: ServiceRegistry = Depends(get_service_registry)
):
    services.packaging_material.delete(item_id)
    return APIResponse.success(message="Packaging Material deleted successfully")
