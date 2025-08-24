from fastapi import APIRouter, Depends, status, Query
from typing import List, Optional

from app.dependencies import get_service_registry
from app.responses import APIResponse
from app.services import ServiceRegistry
from app.schemas.notification_type import NotificationTypeSchema, NotificationTypeCreateSchema, NotificationTypeUpdateSchema

notification_type_router = APIRouter()

@notification_type_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new notification type"
)
def create_notification_type(
    data: NotificationTypeCreateSchema,
    services: ServiceRegistry = Depends(get_service_registry)
):
    new_item = services.notification_type.create(data.dict())
    return APIResponse.success(data=new_item, message="Notification Type created successfully")

@notification_type_router.get(
    "/",
    summary="Get a list of notification types"
)
def get_all_notification_types(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    services: ServiceRegistry = Depends(get_service_registry)
):
    items, total = services.notification_type.get_paginated(page=page, per_page=per_page)
    return APIResponse.paginated(data=items, total=total, page=page, per_page=per_page)

@notification_type_router.get(
    "/{item_id}",
    summary="Get a single notification type"
)
def get_notification_type_by_id(
    item_id: int,
    services: ServiceRegistry = Depends(get_service_registry)
):
    item = services.notification_type.get(item_id)
    return APIResponse.success(data=item)

@notification_type_router.put(
    "/{item_id}",
    summary="Update a notification type"
)
def update_notification_type(
    item_id: int,
    data: NotificationTypeUpdateSchema,
    services: ServiceRegistry = Depends(get_service_registry)
):
    updated_item = services.notification_type.update(
        entity_id=item_id,
        data=data.dict(exclude_unset=True)
    )
    return APIResponse.success(data=updated_item, message="Notification Type updated successfully")

@notification_type_router.delete(
    "/{item_id}",
    summary="Delete a notification type"
)
def delete_notification_type(
    item_id: int,
    services: ServiceRegistry = Depends(get_service_registry)
):
    services.notification_type.delete(item_id)
    return APIResponse.success(message="Notification Type deleted successfully")
