"""
Centralized Dependency Injection Container for OMS Backend

This module provides a centralized way to manage all dependencies
and their lifecycle in the application.
"""

from typing import Dict, Any, Type, Optional
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.dependencies.common import get_db_session
from app.services.dependencies.audit import get_audit_repository, get_audit_service
from app.services.dependencies.users import get_user_repository, get_user_service
from app.services.dependencies.customers import get_customer_repository, get_customer_service
from app.services.dependencies.tenants import get_tenant_repository, get_tenant_service
from app.services.dependencies.addresses import get_address_repository, get_address_service
from app.services.dependencies.products import get_product_repository, get_variant_repository, get_product_service, get_variant_service
from app.services.dependencies.price_lists import get_price_list_repository, get_price_list_service, get_product_pricing_service
from app.services.dependencies.warehouses import get_warehouse_repository, get_warehouse_service
from app.services.dependencies.orders import get_order_repository, get_variant_repository as get_order_variant_repository
from app.services.dependencies.stock_docs import get_stock_doc_repository, get_stock_doc_service
from app.services.dependencies.stock_levels import get_stock_level_repository, get_stock_level_service
from app.services.dependencies.trips import get_trip_repository, get_trip_service
from app.services.dependencies.vehicles import get_vehicle_repository, get_vehicle_service
from app.services.dependencies.vehicles import get_vehicle_warehouse_repository, get_vehicle_warehouse_service


class DependencyContainer:
    """Centralized dependency injection container"""
    
    def __init__(self):
        self._dependencies: Dict[str, Any] = {}
        self._factories: Dict[str, Any] = {}
    
    def register(self, name: str, dependency: Any) -> None:
        """Register a dependency"""
        self._dependencies[name] = dependency
    
    def register_factory(self, name: str, factory: Any) -> None:
        """Register a dependency factory"""
        self._factories[name] = factory
    
    def get(self, name: str) -> Any:
        """Get a dependency by name"""
        if name in self._dependencies:
            return self._dependencies[name]
        if name in self._factories:
            return self._factories[name]
        raise KeyError(f"Dependency '{name}' not found")
    
    def get_all(self) -> Dict[str, Any]:
        """Get all registered dependencies"""
        return {**self._dependencies, **self._factories}


# Global dependency container instance
container = DependencyContainer()


# Database session dependency
def get_database_session() -> AsyncSession:
    """Get database session dependency"""
    return Depends(get_db_session)


# Repository dependencies
def get_audit_repository_dependency():
    """Get audit repository dependency"""
    return Depends(get_audit_repository)


def get_user_repository_dependency():
    """Get user repository dependency"""
    return Depends(get_user_repository)


def get_customer_repository_dependency():
    """Get customer repository dependency"""
    return Depends(get_customer_repository)


def get_tenant_repository_dependency():
    """Get tenant repository dependency"""
    return Depends(get_tenant_repository)


def get_address_repository_dependency():
    """Get address repository dependency"""
    return Depends(get_address_repository)


def get_product_repository_dependency():
    """Get product repository dependency"""
    return Depends(get_product_repository)


def get_variant_repository_dependency():
    """Get variant repository dependency"""
    return Depends(get_variant_repository)


def get_price_list_repository_dependency():
    """Get price list repository dependency"""
    return Depends(get_price_list_repository)


def get_warehouse_repository_dependency():
    """Get warehouse repository dependency"""
    return Depends(get_warehouse_repository)


def get_order_repository_dependency():
    """Get order repository dependency"""
    return Depends(get_order_repository)


def get_stock_doc_repository_dependency():
    """Get stock document repository dependency"""
    return Depends(get_stock_doc_repository)


def get_stock_level_repository_dependency():
    """Get stock level repository dependency"""
    return Depends(get_stock_level_repository)


def get_trip_repository_dependency():
    """Get trip repository dependency"""
    return Depends(get_trip_repository)


def get_vehicle_repository_dependency():
    """Get vehicle repository dependency"""
    return Depends(get_vehicle_repository)


def get_vehicle_warehouse_repository_dependency():
    """Get vehicle warehouse repository dependency"""
    return Depends(get_vehicle_warehouse_repository)


# Service dependencies
def get_audit_service_dependency():
    """Get audit service dependency"""
    return Depends(get_audit_service)


def get_user_service_dependency():
    """Get user service dependency"""
    return Depends(get_user_service)


def get_customer_service_dependency():
    """Get customer service dependency"""
    return Depends(get_customer_service)


def get_tenant_service_dependency():
    """Get tenant service dependency"""
    return Depends(get_tenant_service)


def get_address_service_dependency():
    """Get address service dependency"""
    return Depends(get_address_service)


def get_product_service_dependency():
    """Get product service dependency"""
    return Depends(get_product_service)


def get_variant_service_dependency():
    """Get variant service dependency"""
    return Depends(get_variant_service)


def get_price_list_service_dependency():
    """Get price list service dependency"""
    return Depends(get_price_list_service)


def get_product_pricing_service_dependency():
    """Get product pricing service dependency"""
    return Depends(get_product_pricing_service)


def get_warehouse_service_dependency():
    """Get warehouse service dependency"""
    return Depends(get_warehouse_service)


def get_stock_doc_service_dependency():
    """Get stock document service dependency"""
    return Depends(get_stock_doc_service)


def get_stock_level_service_dependency():
    """Get stock level service dependency"""
    return Depends(get_stock_level_service)


def get_trip_service_dependency():
    """Get trip service dependency"""
    return Depends(get_trip_service)


def get_vehicle_service_dependency():
    """Get vehicle service dependency"""
    return Depends(get_vehicle_service)


def get_vehicle_warehouse_service_dependency():
    """Get vehicle warehouse service dependency"""
    return Depends(get_vehicle_warehouse_service)


# Register all dependencies in the container
def register_all_dependencies():
    """Register all dependencies in the container"""
    
    # Database session
    container.register("database_session", get_database_session)
    
    # Repository dependencies
    container.register("audit_repository", get_audit_repository_dependency)
    container.register("user_repository", get_user_repository_dependency)
    container.register("customer_repository", get_customer_repository_dependency)
    container.register("tenant_repository", get_tenant_repository_dependency)
    container.register("address_repository", get_address_repository_dependency)
    container.register("product_repository", get_product_repository_dependency)
    container.register("variant_repository", get_variant_repository_dependency)
    container.register("price_list_repository", get_price_list_repository_dependency)
    container.register("warehouse_repository", get_warehouse_repository_dependency)
    container.register("order_repository", get_order_repository_dependency)
    container.register("stock_doc_repository", get_stock_doc_repository_dependency)
    container.register("stock_level_repository", get_stock_level_repository_dependency)
    container.register("trip_repository", get_trip_repository_dependency)
    container.register("vehicle_repository", get_vehicle_repository_dependency)
    container.register("vehicle_warehouse_repository", get_vehicle_warehouse_repository_dependency)
    
    # Service dependencies
    container.register("audit_service", get_audit_service_dependency)
    container.register("user_service", get_user_service_dependency)
    container.register("customer_service", get_customer_service_dependency)
    container.register("tenant_service", get_tenant_service_dependency)
    container.register("address_service", get_address_service_dependency)
    container.register("product_service", get_product_service_dependency)
    container.register("variant_service", get_variant_service_dependency)
    container.register("price_list_service", get_price_list_service_dependency)
    container.register("product_pricing_service", get_product_pricing_service_dependency)
    container.register("warehouse_service", get_warehouse_service_dependency)
    container.register("stock_doc_service", get_stock_doc_service_dependency)
    container.register("stock_level_service", get_stock_level_service_dependency)
    container.register("trip_service", get_trip_service_dependency)
    container.register("vehicle_service", get_vehicle_service_dependency)
    container.register("vehicle_warehouse_service", get_vehicle_warehouse_service_dependency)


# Initialize dependencies on module import
register_all_dependencies()


# Convenience functions for getting dependencies
def get_dependency(name: str):
    """Get a dependency by name"""
    return container.get(name)


def get_all_dependencies() -> Dict[str, Any]:
    """Get all registered dependencies"""
    return container.get_all()


# Export commonly used dependencies
__all__ = [
    "container",
    "get_dependency",
    "get_all_dependencies",
    "get_database_session",
    "get_audit_repository_dependency",
    "get_user_repository_dependency",
    "get_customer_repository_dependency",
    "get_tenant_repository_dependency",
    "get_address_repository_dependency",
    "get_product_repository_dependency",
    "get_variant_repository_dependency",
    "get_price_list_repository_dependency",
    "get_warehouse_repository_dependency",
    "get_order_repository_dependency",
    "get_stock_doc_repository_dependency",
    "get_stock_level_repository_dependency",
    "get_trip_repository_dependency",
    "get_vehicle_repository_dependency",
    "get_vehicle_warehouse_repository_dependency",
    "get_audit_service_dependency",
    "get_user_service_dependency",
    "get_customer_service_dependency",
    "get_tenant_service_dependency",
    "get_address_service_dependency",
    "get_product_service_dependency",
    "get_variant_service_dependency",
    "get_price_list_service_dependency",
    "get_product_pricing_service_dependency",
    "get_warehouse_service_dependency",
    "get_stock_doc_service_dependency",
    "get_stock_level_service_dependency",
    "get_trip_service_dependency",
    "get_vehicle_service_dependency",
    "get_vehicle_warehouse_service_dependency",
] 