from fastapi import APIRouter, Depends, status, Query
from typing import List, Optional

from app.dependencies import get_service_registry
from app.responses import APIResponse
from app.services import ServiceRegistry
from app.schemas.document_type import DocumentTypeSchema, DocumentTypeCreateSchema, DocumentTypeUpdateSchema

document_type_router = APIRouter()

@document_type_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new document type"
)
def create_document_type(
    data: DocumentTypeCreateSchema,
    services: ServiceRegistry = Depends(get_service_registry)
):
    new_item = services.document_type.create(data.dict())
    return APIResponse.success(data=new_item, message="Document Type created successfully")

@document_type_router.get(
    "/",
    summary="Get a list of document types"
)
def get_all_document_types(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    services: ServiceRegistry = Depends(get_service_registry)
):
    items, total = services.document_type.get_paginated(page=page, per_page=per_page)
    return APIResponse.paginated(data=items, total=total, page=page, per_page=per_page)

@document_type_router.get(
    "/{item_id}",
    summary="Get a single document type"
)
def get_document_type_by_id(
    item_id: int,
    services: ServiceRegistry = Depends(get_service_registry)
):
    item = services.document_type.get(item_id)
    return APIResponse.success(data=item)

@document_type_router.put(
    "/{item_id}",
    summary="Update a document type"
)
def update_document_type(
    item_id: int,
    data: DocumentTypeUpdateSchema,
    services: ServiceRegistry = Depends(get_service_registry)
):
    updated_item = services.document_type.update(
        entity_id=item_id,
        data=data.dict(exclude_unset=True)
    )
    return APIResponse.success(data=updated_item, message="Document Type updated successfully")

@document_type_router.delete(
    "/{item_id}",
    summary="Delete a document type"
)
def delete_document_type(
    item_id: int,
    services: ServiceRegistry = Depends(get_service_registry)
):
    services.document_type.delete(item_id)
    return APIResponse.success(message="Document Type deleted successfully")
