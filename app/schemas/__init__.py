"""
Schemas Package
===============

Marshmallow schemas untuk serialization dan validation
"""

from .base import (
    BaseSchema,
    PaginationSchema,
    TimestampMixin,
    StatusMixin,
    ERPMixin,
    AddressMixin,
    ContactMixin
)

# ==================== PRODUCT DOMAIN ====================
from .product import (
    # Enum schemas
    ProductTypeSchema, 
    PackageTypeSchema, 
    TemperatureTypeSchema,  
    AllocationTypeSchema, 
    MovementTypeSchema,  
    
    # Main schemas
    ProductSchema, ProductCreateSchema, ProductUpdateSchema,
    BatchSchema, BatchCreateSchema, BatchUpdateSchema,
    AllocationSchema, AllocationCreateSchema, AllocationUpdateSchema,
    StockMovementSchema, StockMovementCreateSchema, StockMovementUpdateSchema
)

# ==================== CUSTOMER DOMAIN ====================
from .customer import (
    # Enum schemas
    SectorTypeSchema,
    CustomerTypeSchema,
    
    # Main schemas
    CustomerSchema, CustomerCreateSchema, CustomerUpdateSchema,
    CustomerAddressSchema, CustomerAddressCreateSchema, CustomerAddressUpdateSchema
)

# ==================== WAREHOUSE DOMAIN ====================
from .warehouse import (
    WarehouseSchema, WarehouseCreateSchema, WarehouseUpdateSchema,
    RackSchema, RackCreateSchema, RackUpdateSchema,
    RackAllocationSchema, RackAllocationCreateSchema
)

# ==================== CONTRACT DOMAIN ====================
from .contract import (
    TenderContractSchema, TenderContractCreateSchema, TenderContractUpdateSchema,
    ContractReservationSchema, ContractReservationCreateSchema, ContractReservationUpdateSchema
)

# ==================== SALES DOMAIN ====================
from .sales import (
    PackingSlipSchema, PackingSlipCreateSchema, PackingSlipUpdateSchema,
    SalesOrderSchema, SalesOrderCreateSchema, SalesOrderUpdateSchema,
    SalesOrderItemSchema, SalesOrderItemCreateSchema, SalesOrderItemUpdateSchema,
    ShippingPlanSchema, ShippingPlanCreateSchema, ShippingPlanUpdateSchema,
    ShippingPlanItemSchema, ShippingPlanItemCreateSchema, ShippingPlanItemUpdateSchema
)

# ==================== PICKING DOMAIN ====================
from .picking import (
    PickingListSchema, PickingListCreateSchema, PickingListUpdateSchema,
    PickingListItemSchema, PickingListItemCreateSchema, PickingListItemUpdateSchema,
    PickingOrderSchema, PickingOrderCreateSchema, PickingOrderUpdateSchema,
    PickingOrderItemSchema, PickingOrderItemCreateSchema, PickingOrderItemUpdateSchema
)

# ==================== PACKING DOMAIN ====================
from .packing import (
    PackingOrderSchema, PackingOrderCreateSchema, PackingOrderUpdateSchema,
    PackingBoxSchema, PackingBoxCreateSchema, PackingBoxUpdateSchema,
    PackingBoxItemSchema, PackingBoxItemCreateSchema, PackingBoxItemUpdateSchema
)

# ==================== SHIPMENT DOMAIN ====================
from .shipment import (
    # Enum schemas
    DeliveryMethodSchema, DeliveryMethodCreateSchema, DeliveryMethodUpdateSchema,
    CarrierTypeSchema, CarrierTypeCreateSchema, CarrierTypeUpdateSchema,
    DocumentTypeSchema, DocumentTypeCreateSchema, DocumentTypeUpdateSchema,
    
    # Main schemas
    CarrierSchema, CarrierCreateSchema, CarrierUpdateSchema,
    ShipmentSchema, ShipmentCreateSchema, ShipmentUpdateSchema,
    ShipmentDocumentSchema, ShipmentDocumentCreateSchema, ShipmentDocumentUpdateSchema,
    ShipmentTrackingSchema, ShipmentTrackingCreateSchema, ShipmentTrackingUpdateSchema
)

# ==================== CONSIGNMENT DOMAIN ====================
from .consignment import (
    ConsignmentAgreementSchema, ConsignmentAgreementCreateSchema, ConsignmentAgreementUpdateSchema,
    ConsignmentSchema, ConsignmentCreateSchema, ConsignmentUpdateSchema,
    ConsignmentItemSchema, ConsignmentItemCreateSchema, ConsignmentItemUpdateSchema,
    ConsignmentSaleSchema, ConsignmentSaleCreateSchema, ConsignmentSaleUpdateSchema,
    ConsignmentReturnSchema, ConsignmentReturnCreateSchema, ConsignmentReturnUpdateSchema,
    ConsignmentStatementSchema, ConsignmentStatementCreateSchema, ConsignmentStatementUpdateSchema
)

# ==================== USER DOMAIN ====================
from .user import (
    UserSchema, UserCreateSchema, UserUpdateSchema, UserProfileSchema,
    PasswordChangeSchema, LoginSchema, LoginResponseSchema, TokenRefreshSchema,
    UserSessionSchema, UserActivitySchema, UserSessionCreateSchema, UserSessionUpdateSchema
)

# ==================== HELPER DOMAIN ====================
from .helper import (
    BaseEnumSchema, BaseEnumCreateSchema, BaseEnumUpdateSchema,
    SystemConfigurationSchema, SystemConfigurationCreateSchema, SystemConfigurationUpdateSchema,
    NotificationTypeSchema, NotificationTypeCreateSchema, NotificationTypeUpdateSchema,
    NotificationLogSchema, NotificationLogCreateSchema,
    AuditLogSchema, AuditLogCreateSchema,
    SystemLogSchema, SystemLogCreateSchema,
    ErrorResponseSchema, SuccessResponseSchema, PaginatedResponseSchema,
    SearchSchema, DateRangeSchema
)

# ==================== VALIDATORS ====================
from .validators import (
    validate_product_code, validate_customer_code, validate_batch_number,
    validate_expiry_date, validate_manufacturing_date, validate_positive_number,
    validate_non_negative_number, validate_percentage, validate_priority_level,
    validate_phone_number, validate_postal_code, validate_rack_code,
    validate_contract_number, validate_allocation_quantities, validate_so_number,
    validate_ps_number, validate_nie_number, validate_tracking_number
)

__all__ = [
    # Base schemas
    'BaseSchema', 'PaginationSchema', 'TimestampMixin', 'StatusMixin', 
    'ERPMixin', 'AddressMixin', 'ContactMixin',
    
    # Product domain
    'ProductTypeSchema',
    'PackageTypeSchema', 'PackageTypeCreateSchema', 'PackageTypeUpdateSchema',
    'TemperatureTypeSchema', 'TemperatureTypeCreateSchema', 'TemperatureTypeUpdateSchema',
    'AllocationTypeSchema', 'AllocationTypeCreateSchema', 'AllocationTypeUpdateSchema',
    'MovementTypeSchema', 'MovementTypeCreateSchema', 'MovementTypeUpdateSchema',
    'ProductSchema', 'ProductCreateSchema', 'ProductUpdateSchema',
    'BatchSchema', 'BatchCreateSchema', 'BatchUpdateSchema',
    'AllocationSchema', 'AllocationCreateSchema', 'AllocationUpdateSchema',
    'StockMovementSchema', 'StockMovementCreateSchema','StockMovementUpdateSchema',
    
    # Customer domain
    'SectorTypeSchema', 'SectorTypeCreateSchema', 'SectorTypeUpdateSchema',
    'CustomerTypeSchema', 'CustomerTypeCreateSchema', 'CustomerTypeUpdateSchema',
    'CustomerSchema', 'CustomerCreateSchema', 'CustomerUpdateSchema',
    'CustomerAddressSchema', 'CustomerAddressCreateSchema', 'CustomerAddressUpdateSchema',
    
    # Warehouse domain
    'WarehouseSchema', 'WarehouseCreateSchema', 'WarehouseUpdateSchema',
    'RackSchema', 'RackCreateSchema', 'RackUpdateSchema',
    'RackAllocationSchema', 'RackAllocationCreateSchema',
    
    # Contract domain
    'TenderContractSchema', 'TenderContractCreateSchema', 'TenderContractUpdateSchema',
    'ContractReservationSchema', 'ContractReservationCreateSchema', 'ContractReservationUpdateSchema',
    
    # Sales domain
    'PackingSlipSchema', 'PackingSlipCreateSchema', 'PackingSlipUpdateSchema',
    'SalesOrderSchema', 'SalesOrderCreateSchema', 'SalesOrderUpdateSchema',
    'SalesOrderItemSchema', 'SalesOrderItemCreateSchema', 'SalesOrderItemUpdateSchema',
    'ShippingPlanSchema', 'ShippingPlanCreateSchema', 'ShippingPlanUpdateSchema',
    'ShippingPlanItemSchema', 'ShippingPlanItemCreateSchema', 'ShippingPlanItemUpdateSchema',
    
    # Picking domain
    'PickingListSchema', 'PickingListCreateSchema', 'PickingListUpdateSchema',
    'PickingListItemSchema', 'PickingListItemCreateSchema', 'PickingListItemUpdateSchema',
    'PickingOrderSchema', 'PickingOrderCreateSchema', 'PickingOrderUpdateSchema',
    'PickingOrderItemSchema', 'PickingOrderItemCreateSchema', 'PickingOrderItemUpdateSchema',
    
    # Packing domain
    'PackingOrderSchema', 'PackingOrderCreateSchema', 'PackingOrderUpdateSchema',
    'PackingBoxSchema', 'PackingBoxCreateSchema', 'PackingBoxUpdateSchema',
    'PackingBoxItemSchema', 'PackingBoxItemCreateSchema', 'PackingBoxItemUpdateSchema',
    
    # Shipment domain
    'DeliveryMethodSchema', 'DeliveryMethodCreateSchema', 'DeliveryMethodUpdateSchema',
    'CarrierTypeSchema', 'CarrierTypeCreateSchema', 'CarrierTypeUpdateSchema',
    'DocumentTypeSchema', 'DocumentTypeCreateSchema', 'DocumentTypeUpdateSchema',
    'CarrierSchema', 'CarrierCreateSchema', 'CarrierUpdateSchema',
    'ShipmentSchema', 'ShipmentCreateSchema', 'ShipmentUpdateSchema',
    'ShipmentDocumentSchema', 'ShipmentDocumentCreateSchema', 'ShipmentDocumentUpdateSchema',
    'ShipmentTrackingSchema', 'ShipmentTrackingCreateSchema', 'ShipmentTrackingUpdateSchema',
    
    # Consignment domain
    'ConsignmentAgreementSchema', 'ConsignmentAgreementCreateSchema', 'ConsignmentAgreementUpdateSchema',
    'ConsignmentSchema', 'ConsignmentCreateSchema', 'ConsignmentUpdateSchema',
    'ConsignmentItemSchema', 'ConsignmentItemCreateSchema', 'ConsignmentItemUpdateSchema',
    'ConsignmentSaleSchema', 'ConsignmentSaleCreateSchema', 'ConsignmentSaleUpdateSchema',
    'ConsignmentReturnSchema', 'ConsignmentReturnCreateSchema', 'ConsignmentReturnUpdateSchema',
    'ConsignmentStatementSchema', 'ConsignmentStatementCreateSchema', 'ConsignmentStatementUpdateSchema',
    
    # User domain
    'UserSchema', 'UserCreateSchema', 'UserUpdateSchema', 'UserProfileSchema',
    'PasswordChangeSchema', 'LoginSchema', 'LoginResponseSchema', 'TokenRefreshSchema',
    'UserSessionSchema', 'UserActivitySchema','UserSessionCreateSchema', 'UserSessionUpdateSchema'
    
    # Helper domain
    'BaseEnumSchema', 'BaseEnumCreateSchema', 'BaseEnumUpdateSchema',
    'SystemConfigurationSchema', 'SystemConfigurationCreateSchema', 'SystemConfigurationUpdateSchema',
    'NotificationTypeSchema', 'NotificationTypeCreateSchema', 'NotificationTypeUpdateSchema',
    'NotificationLogSchema', 'NotificationLogCreateSchema',
    'AuditLogSchema', 'AuditLogCreateSchema',
    'SystemLogSchema', 'SystemLogCreateSchema',
    'ErrorResponseSchema', 'SuccessResponseSchema', 'PaginatedResponseSchema',
    'SearchSchema', 'DateRangeSchema',
    
    # Validators
    'validate_product_code', 'validate_customer_code', 'validate_batch_number',
    'validate_expiry_date', 'validate_manufacturing_date', 'validate_positive_number',
    'validate_non_negative_number', 'validate_percentage', 'validate_priority_level',
    'validate_phone_number', 'validate_postal_code', 'validate_rack_code',
    'validate_contract_number', 'validate_allocation_quantities', 'validate_so_number',
    'validate_ps_number', 'validate_nie_number', 'validate_tracking_number'
]

def init_schemas():
    """Initialize schemas package"""
    # Could be used for any schema-level initialization
    pass