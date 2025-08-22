"""
Custom Validators
=================

Custom validation functions untuk business rules
"""

from pydantic import field_validator, ValidationError
from datetime import datetime, date
import re

def validate_product_code(value: str) -> str:
    """Validate product code format"""
    if not re.match(r'^[A-Z0-9\-]{3,20}$', value):
        raise ValueError('Product code must be 3-20 characters, alphanumeric with hyphens only')
    return value

def validate_customer_code(value: str) -> str:
    """Validate customer code format"""
    if not re.match(r'^[A-Z0-9]{3,20}$', value):
        raise ValueError('Customer code must be 3-20 characters, alphanumeric only')
    return value

def validate_batch_number(value: str) -> str:
    """Validate batch number format"""
    if len(value) < 3 or len(value) > 50:
        raise ValueError('Batch number must be 3-50 characters')
    return value

def validate_expiry_date(value: date) -> date:
    """Validate expiry date tidak boleh masa lalu"""
    if isinstance(value, date) and value < date.today():
        raise ValueError('Expiry date cannot be in the past')
    return value

def validate_manufacturing_date(value: date) -> date:
    """Validate manufacturing date tidak boleh future"""
    if isinstance(value, date) and value > date.today():
        raise ValueError('Manufacturing date cannot be in the future')
    return value

def validate_positive_number(value: float) -> float:
    """Validate positive number"""
    if value <= 0:
        raise ValueError('Value must be positive')
    return value

def validate_non_negative_number(value: float) -> float:
    """Validate non-negative number"""
    if value < 0:
        raise ValueError('Value must be non-negative')
    return value

def validate_percentage(value: float) -> float:
    """Validate percentage (0-100)"""
    if not (0 <= value <= 100):
        raise ValueError('Percentage must be between 0 and 100')
    return value

def validate_priority_level(value: int) -> int:
    """Validate priority level (1-9)"""
    if not (1 <= value <= 9):
        raise ValueError('Priority level must be between 1 (highest) and 9 (lowest)')
    return value

def validate_phone_number(value: str) -> str:
    """Validate Indonesian phone number"""
    if value and not re.match(r'^(\+62|0)[0-9]{8,12}$', value):
        raise ValueError('Invalid Indonesian phone number format')
    return value

def validate_postal_code(value: str) -> str:
    """Validate Indonesian postal code"""
    if value and not re.match(r'^[0-9]{5}$', value):
        raise ValueError('Postal code must be 5 digits')
    return value

def validate_temperature_range(min_temp: float, max_temp: float) -> None:
    """Validate temperature range"""
    if min_temp is not None and max_temp is not None and min_temp > max_temp:
        raise ValueError('Minimum temperature cannot be greater than maximum temperature')

def validate_rack_code(value: str) -> str:
    """Validate rack code format"""
    if not re.match(r'^[A-Z0-9\-\.]{2,20}$', value):
        raise ValueError('Rack code must be 2-20 characters, alphanumeric with hyphens and dots')
    return value

def validate_contract_number(value: str) -> str:
    """Validate contract number format"""
    if not re.match(r'^[A-Z0-9\-\/]{5,50}$', value):
        raise ValueError('Contract number must be 5-50 characters')
    return value

def validate_allocation_quantities(allocated: int, shipped: int, reserved: int) -> None:
    """Validate allocation quantities business rule"""
    if shipped + reserved > allocated:
        raise ValueError('Shipped + Reserved quantities cannot exceed Allocated quantity')

def validate_so_number(value: str) -> str:
    """Validate sales order number format"""
    if not re.match(r'^SO[0-9]{6,12}$', value):
        raise ValueError('SO number must start with SO followed by 6-12 digits')
    return value

def validate_ps_number(value: str) -> str:
    """Validate packing slip number format"""
    if not re.match(r'^PS[0-9]{6,12}$', value):
        raise ValueError('PS number must start with PS followed by 6-12 digits')
    return value

def validate_nie_number(value: str) -> str:
    """Validate NIE number format"""
    if value and not re.match(r'^[A-Z]{2}[0-9]{8,12}$', value):
        raise ValueError('NIE number must start with 2 letters followed by 8-12 digits')
    return value

def validate_tracking_number(value: str) -> str:
    """Validate tracking number format"""
    if value and len(value) < 5:
        raise ValueError('Tracking number must be at least 5 characters')
    return value