from fastapi import APIRouter, Depends, status, Query
from typing import List, Optional

from app.dependencies import get_service_registry
from app.responses import APIResponse
from app.services import ServiceRegistry
from app.schemas.carrier import CarrierSchema, CarrierCreateSchema, CarrierUpdateSchema

carrier_router = APIRouter()

@carrier_router.post(
    "/",
    
    status_code=status.HTTP_201_CREATED,
    summary="Create a new carrier"
)
def create_carrier(
    carrier_data: CarrierCreateSchema,
    services: ServiceRegistry = Depends(get_service_registry)
):
    """
    Create a new carrier (e.g., FedEx, DHL).
    """
    new_carrier = services.carrier.create(carrier_data.dict())
    return APIResponse.success(data=new_carrier, message="Carrier created successfully")

@carrier_router.get(
    "/",
    
    summary="Get a list of carriers"
)
def get_all_carriers(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    is_active: bool = Query(True),
    services: ServiceRegistry = Depends(get_service_registry)
):
    """
    Get a paginated list of carriers. By default, it returns active carriers.
    """
    filters = {'is_active': is_active}
    carriers, total = services.carrier.get_paginated(
        page=page,
        per_page=per_page,
        filters=filters
    )
    return APIResponse.paginated(data=carriers, total=total, page=page, per_page=per_page)

@carrier_router.get(
    "/{carrier_id}",
    
    summary="Get a single carrier"
)
def get_carrier_by_id(
    carrier_id: int,
    services: ServiceRegistry = Depends(get_service_registry)
):
    """
    Retrieve the details of a single carrier by its ID.
    """
    carrier = services.carrier.get(carrier_id)
    return APIResponse.success(data=carrier)

@carrier_router.put(
    "/{carrier_id}",
    
    summary="Update a carrier"
)
def update_carrier(
    carrier_id: int,
    carrier_data: CarrierUpdateSchema,
    services: ServiceRegistry = Depends(get_service_registry)
):
    """
    Update an existing carrier's details.
    """
    updated_carrier = services.carrier.update(
        entity_id=carrier_id,
        data=carrier_data.dict(exclude_unset=True)
    )
    return APIResponse.success(data=updated_carrier, message="Carrier updated successfully")

@carrier_router.delete(
    "/{carrier_id}",
    
    summary="Delete a carrier"
)
def delete_carrier(
    carrier_id: int,
    services: ServiceRegistry = Depends(get_service_registry)
):
    """
    Delete a carrier. Note: This is a hard delete.
    Consider deactivating with a PUT request instead for referential integrity.
    """
    services.carrier.delete(carrier_id)
    return APIResponse.success(message="Carrier deleted successfully")


