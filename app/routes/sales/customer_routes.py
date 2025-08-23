from fastapi import APIRouter, Depends, status, Query
from typing import List, Optional

from app import APIResponse, get_service_registry
from app.services import ServiceRegistry
from app.schemas.customer import CustomerSchema, CustomerCreateSchema, CustomerUpdateSchema

customer_router = APIRouter()

@customer_router.post(
    "/",
    response_model=APIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new customer"
)
def create_customer(
    customer_data: CustomerCreateSchema,
    services: ServiceRegistry = Depends(get_service_registry)
):
    """
    Create a new customer in the system.
    """
    new_customer = services.customer.create(customer_data.dict())
    return APIResponse.success(data=new_customer, message="Customer created successfully")

@customer_router.get(
    "/",
    response_model=APIResponse,
    summary="Get a list of customers"
)
def get_all_customers(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    services: ServiceRegistry = Depends(get_service_registry)
):
    """
    Get a paginated list of customers.
    Allows searching by name, code, legal name, or email.
    """
    customers, total = services.customer.get_paginated(
        page=page,
        per_page=per_page,
        search_term=search
    )
    return APIResponse.paginated(data=customers, total=total, page=page, per_page=per_page)

@customer_router.get(
    "/{customer_id}",
    response_model=APIResponse,
    summary="Get a single customer by ID"
)
def get_customer_by_id(
    customer_id: int,
    services: ServiceRegistry = Depends(get_service_registry)
):
    """
    Retrieve the details of a single customer by their ID.
    """
    customer = services.customer.get(customer_id)
    return APIResponse.success(data=customer)

@customer_router.put(
    "/{customer_id}",
    response_model=APIResponse,
    summary="Update a customer"
)
def update_customer(
    customer_id: int,
    customer_data: CustomerUpdateSchema,
    services: ServiceRegistry = Depends(get_service_registry)
):
    """
    Update an existing customer's details.
    """
    updated_customer = services.customer.update(
        entity_id=customer_id,
        data=customer_data.dict(exclude_unset=True)
    )
    return APIResponse.success(data=updated_customer, message="Customer updated successfully")

@customer_router.get(
    "/search/",
    response_model=APIResponse,
    summary="Search for customers"
)
def search_customers(
    term: str = Query(..., min_length=2),
    services: ServiceRegistry = Depends(get_service_registry)
):
    """
    Search for customers by name or code for autocomplete fields.
    """
    customers = services.customer.search_customers(search_term=term)
    return APIResponse.success(data=customers)
