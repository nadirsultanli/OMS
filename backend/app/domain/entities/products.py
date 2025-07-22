from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from ..entities.variants import Variant


@dataclass
class Product:
    """
    Product domain entity representing a product in the LPG Cylinder business.
    
    Products represent the base product (e.g., "13kg LPG Cylinder") while variants
    represent specific SKUs (e.g., "CYL13-FULL", "CYL13-EMPTY", "GAS13", "DEP13").
    """
    id: UUID
    tenant_id: UUID
    name: str
    created_at: datetime
    updated_at: datetime
    category: Optional[str] = None
    unit_of_measure: str = "PCS"
    min_price: Decimal = Decimal("0")
    taxable: bool = True
    density_kg_per_l: Optional[Decimal] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UUID] = None
    
    # Relationship fields
    variants: List[Variant] = field(default_factory=list)
    
    @classmethod
    def create(
        cls,
        tenant_id: UUID,
        name: str,
        category: Optional[str] = None,
        unit_of_measure: str = "PCS",
        min_price: Decimal = Decimal("0"),
        taxable: bool = True,
        density_kg_per_l: Optional[Decimal] = None,
        created_by: Optional[UUID] = None,
    ) -> "Product":
        """Create a new Product instance"""
        from uuid import uuid4
        from datetime import datetime
        
        now = datetime.utcnow()
        
        return cls(
            id=uuid4(),
            tenant_id=tenant_id,
            name=name,
            category=category,
            unit_of_measure=unit_of_measure,
            min_price=min_price,
            taxable=taxable,
            density_kg_per_l=density_kg_per_l,
            created_at=now,
            created_by=created_by,
            updated_at=now,
        )
    
    def add_variant(self, variant: Variant) -> None:
        """Add a variant to this product"""
        if variant.product_id != self.id:
            raise ValueError("Variant must belong to this product")
        self.variants.append(variant)
    
    def get_variant_by_sku(self, sku: str) -> Optional[Variant]:
        """Get a variant by its SKU"""
        for variant in self.variants:
            if variant.sku == sku:
                return variant
        return None
    
    def get_active_variants(self) -> List[Variant]:
        """Get all active variants for this product"""
        return [v for v in self.variants if v.active]
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation"""
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "name": self.name,
            "category": self.category,
            "unit_of_measure": self.unit_of_measure,
            "min_price": float(self.min_price),
            "taxable": self.taxable,
            "density_kg_per_l": float(self.density_kg_per_l) if self.density_kg_per_l else None,
            "created_at": self.created_at.isoformat(),
            "created_by": str(self.created_by) if self.created_by else None,
            "updated_at": self.updated_at.isoformat(),
            "updated_by": str(self.updated_by) if self.updated_by else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "deleted_by": str(self.deleted_by) if self.deleted_by else None,
            "variants": [variant.to_dict() for variant in self.variants],
        } 