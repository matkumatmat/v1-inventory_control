from fastapi import APIRouter, Depends, status, Query
from typing import List, Optional

from app import APIResponse, get_service_registry
from app.services import ServiceRegistry
from app.schemas.packing_slip import PackingSlipSchema, PackingSlipCreateSchema, PackingSlipUpdateSchema

packing_slip_router = APIRouter()

@packing_slip_router.post(
    "/",
    response_model=APIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new packing slip"
)
def create_packing_slip(
    ps_data: PackingSlipCreateSchema,
    services: ServiceRegistry = Depends(get_service_registry)
):
    """
    Create a new packing slip for a Sales Order.
    The slip is created in 'DRAFT' status.
    """
    new_ps = services.packing_slip.create(ps_data.dict())
    return APIResponse.success(data=new_ps, message="Packing slip created successfully")

@packing_slip_router.get(
    "/",
    response_model=APIResponse,
    summary="Get a list of packing slips"
)
def get_all_packing_slips(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    services: ServiceRegistry = Depends(get_service_registry)
):
    """
    Get a paginated list of packing slips.
    """
    filters = {'status': status} if status else {}
    slips, total = services.packing_slip.get_paginated(page=page, per_page=per_page, filters=filters)
    return APIResponse.paginated(data=slips, total=total, page=page, per_page=per_page)

@packing_slip_router.get(
    "/ready-for-shipment",
    response_model=APIResponse,
    summary="Get slips ready for shipment"
)
def get_slips_ready_for_shipment(
    services: ServiceRegistry = Depends(get_service_registry)
):
    """
    Get a list of all packing slips that are in 'FINALIZED' status
    and are ready to be converted into a shipment.
    """
    ready_slips = services.packing_slip.get_ready_for_shipment()
    return APIResponse.success(data=ready_slips)

@packing_slip_router.get(
    "/{ps_id}",
    response_model=APIResponse,
    summary="Get a single packing slip"
)
def get_packing_slip_by_id(
    ps_id: int,
    services: ServiceRegistry = Depends(get_service_registry)
):
    """
    Retrieve the details of a single packing slip.
    """
    packing_slip = services.packing_slip.get(ps_id)
    return APIResponse.success(data=packing_slip)

@packing_slip_router.post(
    "/{ps_id}/finalize",
    response_model=APIResponse,
    summary="Finalize a packing slip"
)
def finalize_packing_slip(
    ps_id: int,
    services: ServiceRegistry = Depends(get_service_registry)
):
    """
    Finalize a 'DRAFT' packing slip. This makes it ready for shipment
    and locks the slip from further editing.
    """
    finalized_ps = services.packing_slip.finalize_packing_slip(ps_id)
    return APIResponse.success(data=finalized_ps, message="Packing slip finalized and ready for shipment")
