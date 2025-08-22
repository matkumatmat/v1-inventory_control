"""
Custom Exceptions untuk WMS Services
====================================

Definisi semua custom exceptions yang digunakan dalam business logic
"""

class WMSException(Exception):
    """Base exception untuk semua WMS errors"""
    def __init__(self, message, error_code=None, details=None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
    
    def to_dict(self):
        return {
            'error': True,
            'message': self.message,
            'error_code': self.error_code,
            'details': self.details
        }

class ValidationError(WMSException):
    """Error untuk validation failures"""
    def __init__(self, message, field=None, details=None):
        super().__init__(message, 'VALIDATION_ERROR', details)
        self.field = field

class BusinessRuleError(WMSException):
    """Error untuk business rule violations"""
    def __init__(self, message, rule_code=None, details=None):
        super().__init__(message, 'BUSINESS_RULE_ERROR', details)
        self.rule_code = rule_code

class InsufficientStockError(BusinessRuleError):
    """Error ketika stock tidak mencukupi"""
    def __init__(self, product_id, required_qty, available_qty, details=None):
        message = f"Insufficient stock for product {product_id}. Required: {required_qty}, Available: {available_qty}"
        super().__init__(message, 'INSUFFICIENT_STOCK', details)
        self.product_id = product_id
        self.required_qty = required_qty
        self.available_qty = available_qty

class AllocationError(BusinessRuleError):
    """Error untuk allocation operations"""
    def __init__(self, message, allocation_id=None, details=None):
        super().__init__(message, 'ALLOCATION_ERROR', details)
        self.allocation_id = allocation_id

class ContractError(BusinessRuleError):
    """Error untuk contract operations"""
    def __init__(self, message, contract_id=None, details=None):
        super().__init__(message, 'CONTRACT_ERROR', details)
        self.contract_id = contract_id

class PickingError(BusinessRuleError):
    """Error untuk picking operations"""
    def __init__(self, message, picking_id=None, details=None):
        super().__init__(message, 'PICKING_ERROR', details)
        self.picking_id = picking_id

class PackingError(BusinessRuleError):
    """Error untuk packing operations"""
    def __init__(self, message, packing_id=None, details=None):
        super().__init__(message, 'PACKING_ERROR', details)
        self.packing_id = packing_id

class ShipmentError(BusinessRuleError):
    """Error untuk shipment operations"""
    def __init__(self, message, shipment_id=None, details=None):
        super().__init__(message, 'SHIPMENT_ERROR', details)
        self.shipment_id = shipment_id

class ConsignmentError(BusinessRuleError):
    """Error untuk consignment operations"""
    def __init__(self, message, consignment_id=None, details=None):
        super().__init__(message, 'CONSIGNMENT_ERROR', details)
        self.consignment_id = consignment_id

class AuthenticationError(WMSException):
    """Error untuk authentication failures"""
    def __init__(self, message="Authentication failed", details=None):
        super().__init__(message, 'AUTHENTICATION_ERROR', details)

class AuthorizationError(WMSException):
    """Error untuk authorization failures"""
    def __init__(self, message="Access denied", required_role=None, details=None):
        super().__init__(message, 'AUTHORIZATION_ERROR', details)
        self.required_role = required_role

class ERPIntegrationError(WMSException):
    """Error untuk ERP integration failures"""
    def __init__(self, message, erp_response=None, details=None):
        super().__init__(message, 'ERP_INTEGRATION_ERROR', details)
        self.erp_response = erp_response

class NotFoundError(WMSException):
    """Error ketika resource tidak ditemukan"""
    def __init__(self, resource_type, resource_id, details=None):
        message = f"{resource_type} with ID {resource_id} not found"
        super().__init__(message, 'NOT_FOUND', details)
        self.resource_type = resource_type
        self.resource_id = resource_id

class ConflictError(WMSException):
    """Error untuk resource conflicts"""
    def __init__(self, message, resource_type=None, details=None):
        super().__init__(message, 'CONFLICT_ERROR', details)
        self.resource_type = resource_type

class ExternalServiceError(WMSException):
    """Error untuk external service failures"""
    def __init__(self, service_name, message, status_code=None, details=None):
        super().__init__(f"{service_name}: {message}", 'EXTERNAL_SERVICE_ERROR', details)
        self.service_name = service_name
        self.status_code = status_code