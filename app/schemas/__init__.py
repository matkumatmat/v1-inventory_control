"""
Schemas Package
===============

Pydantic schemas for serialization and validation.
"""

from .base import (
    BaseSchema,
    PaginationSchema,
    TimestampMixin,
    StatusMixin,
    ERPMixin,
    AddressMixin,
    ContactMixin,
)

# ==================== DOMAIN SCHEMAS ====================

from .product import (
    ProductSchema, ProductCreateSchema, ProductUpdateSchema,
    BatchSchema, BatchCreateSchema, BatchUpdateSchema,
    AllocationSchema, AllocationCreateSchema, AllocationUpdateSchema,
    StockMovementSchema, StockMovementCreateSchema, StockMovementUpdateSchema,
)

from .customer import (
    CustomerSchema, CustomerCreateSchema, CustomerUpdateSchema,
    CustomerAddressSchema, CustomerAddressCreateSchema, CustomerAddressUpdateSchema,
)

from .warehouse import (
    WarehouseSchema, WarehouseCreateSchema, WarehouseUpdateSchema,
    RackSchema, RackCreateSchema, RackUpdateSchema,
    RackAllocationSchema, RackAllocationCreateSchema,
)

from .contract import (
    TenderContractSchema, TenderContractCreateSchema, TenderContractUpdateSchema,
    ContractReservationSchema, ContractReservationCreateSchema, ContractReservationUpdateSchema,
)

from .sales import (
    PackingSlipSchema, PackingSlipCreateSchema, PackingSlipUpdateSchema,
    SalesOrderSchema, SalesOrderCreateSchema, SalesOrderUpdateSchema,
    SalesOrderItemSchema, SalesOrderItemCreateSchema, SalesOrderItemUpdateSchema,
    ShippingPlanSchema, ShippingPlanCreateSchema, ShippingPlanUpdateSchema,
    ShippingPlanItemSchema, ShippingPlanItemCreateSchema, ShippingPlanItemUpdateSchema,
)

from .picking import (
    PickingListSchema, PickingListCreateSchema, PickingListUpdateSchema,
    PickingListItemSchema, PickingListItemCreateSchema, PickingListItemUpdateSchema,
    PickingOrderSchema, PickingOrderCreateSchema, PickingOrderUpdateSchema,
    PickingOrderItemSchema, PickingOrderItemCreateSchema, PickingOrderItemUpdateSchema,
)

from .packing import (
    PackingOrderSchema, PackingOrderCreateSchema, PackingOrderUpdateSchema,
    PackingBoxSchema, PackingBoxCreateSchema, PackingBoxUpdateSchema,
    PackingBoxItemSchema, PackingBoxItemCreateSchema, PackingBoxItemUpdateSchema,
)

from .shipment import (
    CarrierSchema, CarrierCreateSchema, CarrierUpdateSchema,
    ShipmentSchema, ShipmentCreateSchema, ShipmentUpdateSchema,
    ShipmentDocumentSchema, ShipmentDocumentCreateSchema, ShipmentDocumentUpdateSchema,
    ShipmentTrackingSchema, ShipmentTrackingCreateSchema, ShipmentTrackingUpdateSchema,
)

from .consignment import (
    ConsignmentAgreementSchema, ConsignmentAgreementCreateSchema, ConsignmentAgreementUpdateSchema,
    ConsignmentSchema, ConsignmentCreateSchema, ConsignmentUpdateSchema,
    ConsignmentItemSchema, ConsignmentItemCreateSchema, ConsignmentItemUpdateSchema,
    ConsignmentSaleSchema, ConsignmentSaleCreateSchema, ConsignmentSaleUpdateSchema,
    ConsignmentReturnSchema, ConsignmentReturnCreateSchema, ConsignmentReturnUpdateSchema,
    ConsignmentStatementSchema, ConsignmentStatementCreateSchema, ConsignmentStatementUpdateSchema,
)

from .user import (
    UserSchema, UserCreateSchema, UserUpdateSchema, UserProfileSchema,
    PasswordChangeSchema, LoginSchema, LoginResponseSchema, TokenRefreshSchema,
    UserSessionSchema, UserSessionCreateSchema, UserSessionUpdateSchema,
    UserActivitySchema,
)

# ==================== TYPE/ENUM SCHEMAS (from individual files) ====================
from .product_type import ProductTypeSchema, ProductTypeCreateSchema, ProductTypeUpdateSchema
from .package_type import PackageTypeSchema, PackageTypeCreateSchema, PackageTypeUpdateSchema
from .temperature_type import TemperatureTypeSchema, TemperatureTypeCreateSchema, TemperatureTypeUpdateSchema
from .allocation_type import AllocationTypeSchema, AllocationTypeCreateSchema, AllocationTypeUpdateSchema
from .movement_type import MovementTypeSchema, MovementTypeCreateSchema, MovementTypeUpdateSchema
from .sector_type import SectorTypeSchema, SectorTypeCreateSchema, SectorTypeUpdateSchema
from .customer_type import CustomerTypeSchema, CustomerTypeCreateSchema, CustomerTypeUpdateSchema
from .location_type import LocationTypeSchema, LocationTypeCreateSchema, LocationTypeUpdateSchema
from .packaging_material import PackagingMaterialSchema, PackagingMaterialCreateSchema, PackagingMaterialUpdateSchema
from .carrier_type import CarrierTypeSchema, CarrierTypeCreateSchema, CarrierTypeUpdateSchema
from .document_type import DocumentTypeSchema, DocumentTypeCreateSchema, DocumentTypeUpdateSchema
from .shipping_method import ShippingMethodSchema, ShippingMethodCreateSchema, ShippingMethodUpdateSchema
from .priority_level import PriorityLevelSchema, PriorityLevelCreateSchema, PriorityLevelUpdateSchema
from .status_type import StatusTypeSchema, StatusTypeCreateSchema, StatusTypeUpdateSchema

from .helper import (
    BaseEnumSchema, BaseEnumCreateSchema, BaseEnumUpdateSchema,
    SystemConfigurationSchema, SystemConfigurationCreateSchema, SystemConfigurationUpdateSchema,
    NotificationTypeSchema, NotificationTypeCreateSchema, NotificationTypeUpdateSchema,
    NotificationLogSchema, NotificationLogCreateSchema,
    AuditLogSchema, AuditLogCreateSchema,
    SystemLogSchema, SystemLogCreateSchema,
    ErrorResponseSchema, SuccessResponseSchema, PaginatedResponseSchema,
    SearchSchema, DateRangeSchema,
)

from .validators import (
    validate_product_code, validate_customer_code, validate_batch_number,
    validate_expiry_date, validate_manufacturing_date, validate_positive_number,
    validate_non_negative_number, validate_percentage, validate_priority_level,
    validate_phone_number, validate_postal_code, validate_rack_code,
    validate_contract_number, validate_allocation_quantities, validate_so_number,
    validate_ps_number, validate_nie_number, validate_tracking_number,
)

__all__ = [
    # Base schemas
    'BaseSchema', 'PaginationSchema', 'TimestampMixin', 'StatusMixin', 
    'ERPMixin', 'AddressMixin', 'ContactMixin',
    
    # Product domain
    'ProductSchema', 'ProductCreateSchema', 'ProductUpdateSchema',
    'BatchSchema', 'BatchCreateSchema', 'BatchUpdateSchema',
    'AllocationSchema', 'AllocationCreateSchema', 'AllocationUpdateSchema',
    'StockMovementSchema', 'StockMovementCreateSchema', 'StockMovementUpdateSchema',
    
    # Customer domain
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
    'UserSessionSchema', 'UserSessionCreateSchema', 'UserSessionUpdateSchema',
    'UserActivitySchema',
    
    # Type/Enum Schemas
    'ProductTypeSchema', 'ProductTypeCreateSchema', 'ProductTypeUpdateSchema',
    'PackageTypeSchema', 'PackageTypeCreateSchema', 'PackageTypeUpdateSchema',
    'TemperatureTypeSchema', 'TemperatureTypeCreateSchema', 'TemperatureTypeUpdateSchema',
    'AllocationTypeSchema', 'AllocationTypeCreateSchema', 'AllocationTypeUpdateSchema',
    'MovementTypeSchema', 'MovementTypeCreateSchema', 'MovementTypeUpdateSchema',
    'SectorTypeSchema', 'SectorTypeCreateSchema', 'SectorTypeUpdateSchema',
    'CustomerTypeSchema', 'CustomerTypeCreateSchema', 'CustomerTypeUpdateSchema',
    'LocationTypeSchema', 'LocationTypeCreateSchema', 'LocationTypeUpdateSchema',
    'PackagingMaterialSchema', 'PackagingMaterialCreateSchema', 'PackagingMaterialUpdateSchema',
    'DeliveryMethodSchema', 'DeliveryMethodCreateSchema', 'DeliveryMethodUpdateSchema',
    'CarrierTypeSchema', 'CarrierTypeCreateSchema', 'CarrierTypeUpdateSchema',
    'DocumentTypeSchema', 'DocumentTypeCreateSchema', 'DocumentTypeUpdateSchema',
    'ShippingMethodSchema', 'ShippingMethodCreateSchema', 'ShippingMethodUpdateSchema',
    'PriorityLevelSchema', 'PriorityLevelCreateSchema', 'PriorityLevelUpdateSchema',
    'StatusTypeSchema', 'StatusTypeCreateSchema', 'StatusTypeUpdateSchema',

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
    'validate_ps_number', 'validate_nie_number', 'validate_tracking_number',
]

def init_schemas():
    """Initialize schemas package"""
    # Could be used for any schema-level initialization
    pass