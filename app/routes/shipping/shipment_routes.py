from fastapi import APIRouter, Depends, status, Query, Body
from typing import List, Optional, Dict, Any
from datetime import date

from app import APIResponse, get_service_registry
from app.services import ServiceRegistry
from app.schemas.shipment import ShipmentSchema

shipment_router = APIRouter()

@shipment_router.post(
    "/",
    response_model=APIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new shipment from a packing slip"
)
def create_shipment(
    packing_slip_id: int = Body(..., embed=True),
    carrier_id: int = Body(..., embed=True),
    delivery_method_id: int = Body(..., embed=True),
    additional_data: Optional[Dict[str, Any]] = Body(None),
    services: ServiceRegistry = Depends(get_service_registry)
):
    """
    Create a new shipment from a 'FINALIZED' packing slip.
    """
    new_shipment = services.shipment.create_from_packing_slip(
        packing_slip_id, carrier_id, delivery_method_id, additional_data
    )
    return APIResponse.success(data=new_shipment, message="Shipment created successfully")

@shipment_router.get(
    "/",
    response_model=APIResponse,
    summary="Get a list of shipments"
)
def get_all_shipments(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    carrier_id: Optional[int] = Query(None),
    services: ServiceRegistry = Depends(get_service_registry)
):
    """
    Get a paginated list of shipments.
    """
    filters = {}
    if status:
        filters['status'] = status
    if carrier_id:
        filters['carrier_id'] = carrier_id

    shipments, total = services.shipment.get_paginated(
        page=page,
        per_page=per_page,
        filters=filters
    )
    return APIResponse.paginated(data=shipments, total=total, page=page, per_page=per_page)

@shipment_router.get(
    "/{shipment_id}",
    response_model=APIResponse,
    summary="Get a single shipment"
)
def get_shipment_by_id(
    shipment_id: int,
    services: ServiceRegistry = Depends(get_service_registry)
):
    """
    Retrieve the details of a single shipment.
    """
    shipment = services.shipment.get(shipment_id)
    return APIResponse.success(data=shipment)

@shipment_router.post(
    "/{shipment_id}/dispatch",
    response_model=APIResponse,
    summary="Dispatch a shipment"
)
def dispatch_shipment(
    shipment_id: int,
    tracking_number: Optional[str] = Body(None, embed=True),
    estimated_delivery_date: Optional[date] = Body(None, embed=True),
    driver_info: Optional[Dict[str, Any]] = Body(None),
    services: ServiceRegistry = Depends(get_service_registry)
):
    """
    Dispatch a 'PENDING' shipment, marking it as in-transit.
    This is where the carrier tracking number is associated.
    """
    dispatched_shipment = services.shipment.dispatch_shipment(
        shipment_id, tracking_number, estimated_delivery_date, driver_info
    )
    return APIResponse.success(data=dispatched_shipment, message="Shipment has been dispatched")

@shipment_router.post(
    "/{shipment_id}/confirm-delivery",
    response_model=APIResponse,
    summary="Confirm delivery of a shipment"
)
def confirm_shipment_delivery(
    shipment_id: int,
    delivery_confirmation: Dict[str, Any] = Body(...),
    services: ServiceRegistry = Depends(get_service_registry)
):
    """
    Mark a shipment as 'DELIVERED'.
    """
    delivered_shipment = services.shipment.confirm_delivery(shipment_id, delivery_confirmation)
    return APIResponse.success(data=delivered_shipment, message="Shipment marked as delivered")

@shipment_router.post(
    "/{shipment_id}/cancel",
    response_model=APIResponse,
    summary="Cancel a shipment"
)
def cancel_shipment(
    shipment_id: int,
    reason: str = Body(..., embed=True),
    services: ServiceRegistry = Depends(get_service_registry)
):
    """
    Cancel a shipment that has not yet been delivered.
    """
    cancelled_shipment = services.shipment.cancel_shipment(shipment_id, reason)
    return APIResponse.success(data=cancelled_shipment, message="Shipment has been cancelled")
