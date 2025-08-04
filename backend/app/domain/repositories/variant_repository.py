from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities.variants import Variant, ProductStatus, ProductScenario


class VariantRepository(ABC):
    """Abstract interface for Variant repository operations"""
    
    @abstractmethod
    async def create_variant(self, variant: Variant) -> Variant:
        """Create a new variant"""
        pass
    
    @abstractmethod
    async def get_variant_by_id(self, variant_id: UUID) -> Optional[Variant]:
        """Get a variant by its ID"""
        pass
    
    @abstractmethod
    async def get_variant_by_sku(self, tenant_id: UUID, sku: str) -> Optional[Variant]:
        """Get a variant by SKU within a tenant"""
        pass
    
    @abstractmethod
    async def get_variants_by_product(self, product_id: UUID, limit: int = 100, offset: int = 0) -> List[Variant]:
        """Get all variants for a specific product with pagination"""
        pass
    
    @abstractmethod
    async def get_all_variants(self, tenant_id: UUID, limit: int = 100, offset: int = 0) -> List[Variant]:
        """Get all variants for a tenant with pagination"""
        pass
    
    @abstractmethod
    async def update_variant(self, variant: Variant) -> Variant:
        """Update an existing variant"""
        pass
    
    @abstractmethod
    async def delete_variant(self, variant_id: UUID, deleted_by: UUID) -> bool:
        """Soft delete a variant"""
        pass
    
    @abstractmethod
    async def get_variants_by_status(self, tenant_id: UUID, status: ProductStatus, limit: int = 100, offset: int = 0) -> List[Variant]:
        """Get variants by status within a tenant with pagination"""
        pass
    
    @abstractmethod
    async def get_variants_by_scenario(self, tenant_id: UUID, scenario: ProductScenario, limit: int = 100, offset: int = 0) -> List[Variant]:
        """Get variants by scenario within a tenant with pagination"""
        pass
    
    @abstractmethod
    async def get_active_variants(self, tenant_id: UUID, limit: int = 100, offset: int = 0) -> List[Variant]:
        """Get all active variants for a tenant with pagination"""
        pass
    
    @abstractmethod
    async def get_physical_variants(self, tenant_id: UUID, limit: int = 100, offset: int = 0) -> List[Variant]:
        """Get all physical variants (CYL*) for a tenant with pagination"""
        pass
    
    @abstractmethod
    async def get_gas_services(self, tenant_id: UUID, limit: int = 100, offset: int = 0) -> List[Variant]:
        """Get all gas service variants (GAS*) for a tenant with pagination"""
        pass
    
    @abstractmethod
    async def get_deposit_variants(self, tenant_id: UUID, limit: int = 100, offset: int = 0) -> List[Variant]:
        """Get all deposit variants (DEP*) for a tenant with pagination"""
        pass
    
    @abstractmethod
    async def get_bundle_variants(self, tenant_id: UUID, limit: int = 100, offset: int = 0) -> List[Variant]:
        """Get all bundle variants (KIT*) for a tenant with pagination"""
        pass
    
    @abstractmethod
    async def get_variants_requiring_exchange(self, tenant_id: UUID) -> List[Variant]:
        """Get variants that require cylinder exchange (gas services with XCH scenario)"""
        pass
    
    @abstractmethod
    async def get_bundle_components(self, tenant_id: UUID, bundle_sku: str) -> List[Variant]:
        """Get component variants for a bundle SKU"""
        pass
    
    @abstractmethod
    async def get_related_variants(self, tenant_id: UUID, base_sku: str) -> List[Variant]:
        """Get all related variants for a given SKU (same size, different types)"""
        pass
    
    @abstractmethod
    async def validate_exchange_inventory(self, tenant_id: UUID, gas_sku: str, quantity: int) -> dict:
        """
        Validate if there's sufficient inventory for a gas exchange order.
        
        Checks:
        - Sufficient full cylinders for delivery
        - Capacity for empty cylinders being returned
        """
        pass
    
    @abstractmethod
    async def get_variants_by_size(self, tenant_id: UUID, size: str) -> List[Variant]:
        """Get all variants for a specific cylinder size (e.g., '13' for 13kg)"""
        pass
    
    @abstractmethod
    async def get_customer_deposit_summary(self, tenant_id: UUID, customer_id: UUID) -> dict:
        """
        Get customer's deposit summary.
        
        Returns:
        - Total deposits paid
        - Total deposits refunded  
        - Current deposit balance
        - Cylinders owned by customer
        """
        pass 