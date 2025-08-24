from fastapi import APIRouter, Depends, status, Query
from typing import List, Optional

from app.dependencies import get_service_registry
from app.responses import APIResponse
from app.services import ServiceRegistry
from app.schemas.product_type import ProductTypeSchema, ProductTypeCreateSchema, ProductTypeUpdateSchema

router = APIRouter()

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product type"
)
def create_product_type(
    data: ProductTypeCreateSchema,
    services: ServiceRegistry = Depends(get_service_registry)
):
    new_item = services.product_type.create(data.dict())
    return APIResponse.success(data=new_item, message="Product Type created successfully")

@router.get(
    "/",
    summary="Get a list of product types"
)
def get_all_product_types(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    services: ServiceRegistry = Depends(get_service_registry)
):
    items, total = services.product_type.get_paginated(page=page, per_page=per_page)
    return APIResponse.paginated(data=items, total=total, page=page, per_page=per_page)

@router.get(
    "/{item_id}",
    summary="Get a single product type"
)
def get_product_type_by_id(
    item_id: int,
    services: ServiceRegistry = Depends(get_service_registry)
):
    item = services.product_type.get(item_id)
    return APIResponse.success(data=item)

@router.put(
    "/{item_id}",
    summary="Update a product type"
)
def update_product_type(
    item_id: int,
    data: ProductTypeUpdateSchema,
    services: ServiceRegistry = Depends(get_service_registry)
):
    updated_item = services.product_type.update(
        entity_id=item_id,
        data=data.dict(exclude_unset=True)
    )
    return APIResponse.success(data=updated_item, message="Product Type updated successfully")

@router.delete(
    "/{item_id}",
    summary="Delete a product type"
)
def delete_product_type(
    item_id: int,
    services: ServiceRegistry = Depends(get_service_registry)
):
    services.product_type.delete(item_id)
    return APIResponse.success(message="Product Type deleted successfully")
