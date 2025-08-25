"""
WMS Services Module
===================

Complete services layer untuk WMS application
Menggunakan dependency injection pattern untuk service management
"""

from .base import BaseService, CRUDService, transactional, audit_log
from .exceptions import *

# Product Domain
from .product import (
    ProductService, BatchService, AllocationService, StockMovementService
)

# Customer Domain  
from .customer import (
    CustomerService, CustomerAddressService
)

# Warehouse Domain
from .warehouse import (
    WarehouseService, RackService, InventoryService
)

# Contract Domain
from .contract import (
    TenderContractService, ContractReservationService
)

# Sales Domain
from .sales import (
    SalesOrderService, ShippingPlanService, PackingSlipService
)

# Warehouse Operations Domain
from .warehouse_ops import (
    PickingListService, PickingOrderService, PackingOrderService, PackingBoxService
)

# Shipping Domain
from .shipping import (
    ShipmentService, CarrierService, ShipmentTrackingService
)

# Consignment Domain
from .consignment import (
    ConsignmentService, ConsignmentAgreementService, ConsignmentSalesService,
    ConsignmentReturnService, ConsignmentStatementService
)

# Auth Domain
from .auth import (
    AuthService, UserService, UserSessionService
)

# Integration Domain
from .integration import (
    ERPService, NotificationService
)

# Reporting Domain
from .reporting import (
    InventoryReportService, SalesReportService, AuditService
)

__all__ = [
    # Base Classes
    'BaseService', 'CRUDService', 'transactional', 'audit_log',
    
    # Product Domain
    'ProductService', 'BatchService', 'AllocationService', 'StockMovementService',
    
    # Customer Domain
    'CustomerService', 'CustomerAddressService',
    
    # Warehouse Domain
    'WarehouseService', 'RackService', 'InventoryService',
    
    # Contract Domain
    'TenderContractService', 'ContractReservationService',
    
    # Sales Domain
    'SalesOrderService', 'ShippingPlanService', 'PackingSlipService',
    
    # Warehouse Operations Domain
    'PickingListService', 'PickingOrderService', 'PackingOrderService', 'PackingBoxService',
    
    # Shipping Domain
    'ShipmentService', 'CarrierService', 'ShipmentTrackingService',
    
    # Consignment Domain
    'ConsignmentService', 'ConsignmentAgreementService', 'ConsignmentSalesService',
    'ConsignmentReturnService', 'ConsignmentStatementService',
    
    # Auth Domain
    'AuthService', 'UserService', 'UserSessionService',
    
    # Integration Domain
    'ERPService', 'NotificationService',
    
    # Reporting Domain
    'InventoryReportService', 'SalesReportService', 'AuditService'
]


class ServiceRegistry:
    """
    Service Registry untuk dependency injection
    Mengelola lifecycle dan dependencies antar services
    """
    
    def __init__(self, db_session, config: dict, current_user: str = None):
        self.db_session = db_session
        self.config = config
        self.current_user = current_user
        self._services = {}
        
        # Initialize core services first
        self._init_core_services()
        
        # Initialize domain services
        self._init_domain_services()
    
    def _init_core_services(self):
        """Initialize core services yang diperlukan services lain"""
        
        # Audit Service (needed by almost all services)
        self._services['audit'] = AuditService(
            db_session=self.db_session,
            current_user=self.current_user
        )
        
        # Notification Service
        self._services['notification'] = NotificationService(
            db_session=self.db_session,
            email_config=self.config.get('email', {}),
            current_user=self.current_user,
            audit_service=self._services['audit']
        )
        
        # ERP Service
        self._services['erp'] = ERPService(
            db_session=self.db_session,
            erp_base_url=self.config.get('erp_base_url', ''),
            api_key=self.config.get('erp_api_key', ''),
            current_user=self.current_user,
            audit_service=self._services['audit'],
            notification_service=self._services['notification']
        )
    
    def _init_domain_services(self):
        """Initialize domain services dengan dependencies"""
        
        # Product Domain
        self._services['stock_movement'] = StockMovementService(
            db_session=self.db_session,
            current_user=self.current_user,
            audit_service=self._services['audit'],
            notification_service=self._services['notification']
        )
        
        self._services['allocation'] = AllocationService(
            db_session=self.db_session,
            current_user=self.current_user,
            audit_service=self._services['audit'],
            notification_service=self._services['notification'],
            movement_service=self._services['stock_movement']
        )
        
        self._services['batch'] = BatchService(
            db_session=self.db_session,
            current_user=self.current_user,
            audit_service=self._services['audit'],
            notification_service=self._services['notification'],
            allocation_service=self._services['allocation']
        )
        
        self._services['product'] = ProductService(
            db_session=self.db_session,
            current_user=self.current_user,
            audit_service=self._services['audit'],
            notification_service=self._services['notification']
        )
        
        # Customer Domain
        self._services['customer_address'] = CustomerAddressService(
            db_session=self.db_session,
            current_user=self.current_user,
            audit_service=self._services['audit'],
            notification_service=self._services['notification']
        )
        
        self._services['customer'] = CustomerService(
            db_session=self.db_session,
            current_user=self.current_user,
            audit_service=self._services['audit'],
            notification_service=self._services['notification']
        )
        
        # Warehouse Domain
        self._services['rack'] = RackService(
            db_session=self.db_session,
            current_user=self.current_user,
            audit_service=self._services['audit'],
            notification_service=self._services['notification']
        )
        
        self._services['warehouse'] = WarehouseService(
            db_session=self.db_session,
            current_user=self.current_user,
            audit_service=self._services['audit'],
            notification_service=self._services['notification']
        )
        
        self._services['inventory'] = InventoryService(
            db_session=self.db_session,
            current_user=self.current_user,
            audit_service=self._services['audit'],
            notification_service=self._services['notification']
        )
        
        # Contract Domain
        self._services['contract_reservation'] = ContractReservationService(
            db_session=self.db_session,
            current_user=self.current_user,
            audit_service=self._services['audit'],
            notification_service=self._services['notification'],
            allocation_service=self._services['allocation']
        )
        
        self._services['tender_contract'] = TenderContractService(
            db_session=self.db_session,
            current_user=self.current_user,
            audit_service=self._services['audit'],
            notification_service=self._services['notification'],
            allocation_service=self._services['allocation'],
            reservation_service=self._services['contract_reservation']
        )
        
        # Sales Domain
        self._services['packing_slip'] = PackingSlipService(
            db_session=self.db_session,
            current_user=self.current_user,
            audit_service=self._services['audit'],
            notification_service=self._services['notification']
        )
        
        self._services['shipping_plan'] = ShippingPlanService(
            db_session=self.db_session,
            current_user=self.current_user,
            audit_service=self._services['audit'],
            notification_service=self._services['notification'],
            allocation_service=self._services['allocation']
        )
        
        self._services['sales_order'] = SalesOrderService(
            db_session=self.db_session,
            current_user=self.current_user,
            audit_service=self._services['audit'],
            notification_service=self._services['notification'],
            allocation_service=self._services['allocation'],
            shipping_plan_service=self._services['shipping_plan']
        )
        
        # Shipping Domain
        self._services['shipment_tracking'] = ShipmentTrackingService(
            db_session=self.db_session,
            current_user=self.current_user,
            audit_service=self._services['audit'],
            notification_service=self._services['notification']
        )
        
        self._services['carrier'] = CarrierService(
            db_session=self.db_session,
            current_user=self.current_user,
            audit_service=self._services['audit'],
            notification_service=self._services['notification']
        )
        
        self._services['shipment'] = ShipmentService(
            db_session=self.db_session,
            current_user=self.current_user,
            audit_service=self._services['audit'],
            notification_service=self._services['notification'],
            tracking_service=self._services['shipment_tracking']
        )
        
        # Warehouse Operations Domain
        self._services['packing_box'] = PackingBoxService(
            db_session=self.db_session,
            current_user=self.current_user,
            audit_service=self._services['audit'],
            notification_service=self._services['notification']
        )
        
        self._services['packing_order'] = PackingOrderService(
            db_session=self.db_session,
            current_user=self.current_user,
            audit_service=self._services['audit'],
            notification_service=self._services['notification'],
            allocation_service=self._services['allocation'],
            movement_service=self._services['stock_movement']
        )
        
        self._services['picking_order'] = PickingOrderService(
            db_session=self.db_session,
            current_user=self.current_user,
            audit_service=self._services['audit'],
            notification_service=self._services['notification'],
            movement_service=self._services['stock_movement']
        )
        
        self._services['picking_list'] = PickingListService(
            db_session=self.db_session,
            current_user=self.current_user,
            audit_service=self._services['audit'],
            notification_service=self._services['notification'],
            allocation_service=self._services['allocation'],
            movement_service=self._services['stock_movement']
        )
        
        # Consignment Domain
        self._services['consignment_statement'] = ConsignmentStatementService(
            db_session=self.db_session,
            current_user=self.current_user,
            audit_service=self._services['audit'],
            notification_service=self._services['notification']
        )
        
        self._services['consignment_return'] = ConsignmentReturnService(
            db_session=self.db_session,
            current_user=self.current_user,
            audit_service=self._services['audit'],
            notification_service=self._services['notification']
        )
        
        self._services['consignment_sales'] = ConsignmentSalesService(
            db_session=self.db_session,
            current_user=self.current_user,
            audit_service=self._services['audit'],
            notification_service=self._services['notification']
        )
        
        self._services['consignment_agreement'] = ConsignmentAgreementService(
            db_session=self.db_session,
            current_user=self.current_user,
            audit_service=self._services['audit'],
            notification_service=self._services['notification']
        )
        
        self._services['consignment'] = ConsignmentService(
            db_session=self.db_session,
            current_user=self.current_user,
            audit_service=self._services['audit'],
            notification_service=self._services['notification'],
            allocation_service=self._services['allocation'],
            shipment_service=self._services['shipment']
        )
        
        # Auth Domain
        self._services['user_session'] = UserSessionService(
            db_session=self.db_session,
            current_user=self.current_user,
            audit_service=self._services['audit'],
            notification_service=self._services['notification']
        )
        
        self._services['user'] = UserService(
            db_session=self.db_session,
            current_user=self.current_user,
            audit_service=self._services['audit'],
            notification_service=self._services['notification']
        )
        
        self._services['auth'] = AuthService(
            db_session=self.db_session,
            secret_key=self.config.get('secret_key', 'default-secret'),
            audit_service=self._services['audit'],
            notification_service=self._services['notification']
        )
        
        # Reporting Domain
        self._services['inventory_reports'] = InventoryReportService(
            db_session=self.db_session,
            current_user=self.current_user,
            audit_service=self._services['audit']
        )
        
        self._services['sales_reports'] = SalesReportService(
            db_session=self.db_session,
            current_user=self.current_user,
            audit_service=self._services['audit']
        )
    
    def get_service(self, service_name: str):
        """Get service by name"""
        if service_name not in self._services:
            raise ValueError(f"Service '{service_name}' not found")
        return self._services[service_name]
    
    def get_all_services(self) -> dict:
        """Get all registered services"""
        return self._services.copy()
    
    # Convenience methods untuk frequently used services
    @property
    def allocation_service(self) -> AllocationService:
        """Get AllocationService - Most critical service"""
        return self._services['allocation']
    
    @property
    def sales_order_service(self) -> SalesOrderService:
        """Get SalesOrderService"""
        return self._services['sales_order']
    
    @property
    def picking_service(self) -> PickingListService:
        """Get PickingListService"""
        return self._services['picking_list']
    
    @property
    def shipment_service(self) -> ShipmentService:
        """Get ShipmentService"""
        return self._services['shipment']
    
    @property
    def auth_service(self) -> AuthService:
        """Get AuthService"""
        return self._services['auth']

    @property
    def user_service(self) -> UserService:
        """Get UserService"""
        return self._services['user']
    
    @property
    def erp_service(self) -> ERPService:
        """Get ERPService"""
        return self._services['erp']
    
    @property
    def audit_service(self) -> AuditService:
        """Get AuditService"""
        return self._services['audit']


# Factory function untuk easy service registry creation
def create_service_registry(db_session, config: dict, current_user: str = None) -> ServiceRegistry:
    """Factory function untuk membuat ServiceRegistry"""
    return ServiceRegistry(db_session, config, current_user)