from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from app.domain.entities.vehicles import Vehicle
from app.domain.entities.truck_inventory import TruckInventory
from app.domain.entities.stock_docs import StockDoc, StockDocLine, StockDocType, StockStatus
from app.domain.entities.stock_levels import StockLevel
from app.services.stock_docs.stock_doc_service import StockDocService
from app.services.stock_levels.stock_level_service import StockLevelService
from app.infrastucture.logs.logger import default_logger


class VehicleWarehouseService:
    """Service for treating vehicles as mobile warehouses during trips"""
    
    def __init__(
        self, 
        stock_doc_service: StockDocService,
        stock_level_service: StockLevelService
    ):
        self.stock_doc_service = stock_doc_service
        self.stock_level_service = stock_level_service
    
    async def load_vehicle_as_warehouse(
        self,
        vehicle_id: UUID,
        trip_id: UUID,
        source_warehouse_id: UUID,
        inventory_items: List[Dict[str, Any]],
        loaded_by: UUID
    ) -> Dict[str, Any]:
        """
        Load vehicle with inventory, treating it as a mobile warehouse
        
        This creates:
        1. Stock document (TRF_TRUCK) from warehouse to vehicle
        2. Stock level records for vehicle inventory
        3. Truck inventory records for trip tracking
        """
        try:
            # Create stock document for transfer from warehouse to vehicle
            stock_doc = await self._create_warehouse_to_vehicle_transfer(
                vehicle_id=vehicle_id,
                trip_id=trip_id,
                source_warehouse_id=source_warehouse_id,
                inventory_items=inventory_items,
                created_by=loaded_by
            )
            
            # Update stock levels - decrease warehouse, increase vehicle
            await self._update_stock_levels_for_loading(
                vehicle_id=vehicle_id,
                source_warehouse_id=source_warehouse_id,
                inventory_items=inventory_items
            )
            
            # Create truck inventory records for trip tracking
            truck_inventory_records = await self._create_truck_inventory_records(
                trip_id=trip_id,
                vehicle_id=vehicle_id,
                inventory_items=inventory_items,
                created_by=loaded_by
            )
            
            default_logger.info(
                f"Vehicle loaded as warehouse",
                vehicle_id=str(vehicle_id),
                trip_id=str(trip_id),
                stock_doc_id=str(stock_doc.id),
                items_count=len(inventory_items)
            )
            
            return {
                "success": True,
                "stock_doc_id": str(stock_doc.id),
                "truck_inventory_count": len(truck_inventory_records),
                "total_weight_kg": float(sum(item.get("total_weight_kg", 0) for item in inventory_items)),
                "total_volume_m3": float(sum(item.get("total_volume_m3", 0) for item in inventory_items))
            }
            
        except Exception as e:
            default_logger.error(f"Failed to load vehicle as warehouse: {str(e)}")
            raise
    
    async def unload_vehicle_as_warehouse(
        self,
        vehicle_id: UUID,
        trip_id: UUID,
        destination_warehouse_id: UUID,
        actual_inventory: List[Dict[str, Any]],
        expected_inventory: List[Dict[str, Any]],
        unloaded_by: UUID
    ) -> Dict[str, Any]:
        """
        Unload vehicle inventory back to warehouse with variance handling
        
        This creates:
        1. Stock document (TRF_TRUCK) from vehicle to warehouse
        2. Variance adjustments if needed
        3. Updates stock levels
        """
        try:
            # Calculate variances
            variances = self._calculate_inventory_variances(
                actual_inventory=actual_inventory,
                expected_inventory=expected_inventory
            )
            
            # Create stock document for transfer from vehicle to warehouse
            stock_doc = await self._create_vehicle_to_warehouse_transfer(
                vehicle_id=vehicle_id,
                trip_id=trip_id,
                destination_warehouse_id=destination_warehouse_id,
                actual_inventory=actual_inventory,
                created_by=unloaded_by
            )
            
            # Handle variances if any
            variance_docs = []
            if variances:
                variance_docs = await self._create_variance_adjustments(
                    vehicle_id=vehicle_id,
                    trip_id=trip_id,
                    destination_warehouse_id=destination_warehouse_id,
                    variances=variances,
                    created_by=unloaded_by
                )
            
            # Update stock levels
            await self._update_stock_levels_for_unloading(
                vehicle_id=vehicle_id,
                destination_warehouse_id=destination_warehouse_id,
                actual_inventory=actual_inventory
            )
            
            default_logger.info(
                f"Vehicle unloaded as warehouse",
                vehicle_id=str(vehicle_id),
                trip_id=str(trip_id),
                stock_doc_id=str(stock_doc.id),
                variance_count=len(variance_docs)
            )
            
            return {
                "success": True,
                "stock_doc_id": str(stock_doc.id),
                "variance_docs": [str(doc.id) for doc in variance_docs],
                "variances": variances,
                "total_weight_kg": float(sum(item.get("total_weight_kg", 0) for item in actual_inventory)),
                "total_volume_m3": float(sum(item.get("total_volume_m3", 0) for item in actual_inventory))
            }
            
        except Exception as e:
            default_logger.error(f"Failed to unload vehicle as warehouse: {str(e)}")
            raise
    
    async def get_vehicle_inventory_as_warehouse(
        self,
        vehicle_id: UUID,
        trip_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """
        Get current inventory on vehicle, treating it as a warehouse
        """
        try:
            # Get stock levels for vehicle (TRUCK_STOCK status)
            stock_levels = await self.stock_level_service.get_stock_levels_by_warehouse(
                warehouse_id=vehicle_id,
                stock_status=StockStatus.TRUCK_STOCK
            )
            
            # If trip_id provided, also get trip-specific inventory
            trip_inventory = []
            if trip_id:
                # This would come from truck_inventory table
                # For now, we'll use stock levels
                pass
            
            # Combine and format inventory
            inventory = []
            for stock_level in stock_levels:
                inventory.append({
                    "product_id": str(stock_level.product_id),
                    "variant_id": str(stock_level.variant_id),
                    "quantity": float(stock_level.quantity),
                    "available_qty": float(stock_level.available_qty),
                    "reserved_qty": float(stock_level.reserved_qty),
                    "unit_cost": float(stock_level.unit_cost),
                    "total_cost": float(stock_level.total_cost),
                    "stock_status": stock_level.stock_status.value
                })
            
            return inventory
            
        except Exception as e:
            default_logger.error(f"Failed to get vehicle inventory: {str(e)}")
            raise
    
    async def validate_vehicle_capacity(
        self,
        vehicle: Vehicle,
        inventory_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate if inventory items fit within vehicle capacity
        """
        try:
            total_weight_kg = Decimal("0")
            total_volume_m3 = Decimal("0")
            
            for item in inventory_items:
                qty = Decimal(str(item.get("quantity", 0)))
                unit_weight = Decimal(str(item.get("unit_weight_kg", 0)))
                unit_volume = Decimal(str(item.get("unit_volume_m3", 0)))
                
                total_weight_kg += qty * unit_weight
                total_volume_m3 += qty * unit_volume
            
            # Check weight capacity
            weight_capacity = Decimal(str(vehicle.capacity_kg))
            weight_utilization = (total_weight_kg / weight_capacity * 100) if weight_capacity > 0 else 0
            
            # Check volume capacity (if configured)
            volume_utilization = 0
            if vehicle.capacity_m3:
                volume_capacity = Decimal(str(vehicle.capacity_m3))
                volume_utilization = (total_volume_m3 / volume_capacity * 100) if volume_capacity > 0 else 0
            
            validation = {
                "is_valid": True,
                "weight_kg": float(total_weight_kg),
                "volume_m3": float(total_volume_m3),
                "weight_capacity_kg": float(weight_capacity),
                "volume_capacity_m3": float(vehicle.capacity_m3) if vehicle.capacity_m3 else None,
                "weight_utilization_pct": float(weight_utilization),
                "volume_utilization_pct": float(volume_utilization),
                "warnings": []
            }
            
            # Check for capacity violations
            if total_weight_kg > weight_capacity:
                validation["is_valid"] = False
                validation["warnings"].append(f"Weight {total_weight_kg}kg exceeds capacity {weight_capacity}kg")
            
            if vehicle.capacity_m3 and total_volume_m3 > Decimal(str(vehicle.capacity_m3)):
                validation["is_valid"] = False
                validation["warnings"].append(f"Volume {total_volume_m3}m³ exceeds capacity {vehicle.capacity_m3}m³")
            
            # Check for high utilization warnings
            if weight_utilization > 90:
                validation["warnings"].append(f"High weight utilization: {weight_utilization:.1f}%")
            
            if vehicle.capacity_m3 and volume_utilization > 90:
                validation["warnings"].append(f"High volume utilization: {volume_utilization:.1f}%")
            
            return validation
            
        except Exception as e:
            default_logger.error(f"Failed to validate vehicle capacity: {str(e)}")
            raise
    
    async def _create_warehouse_to_vehicle_transfer(
        self,
        vehicle_id: UUID,
        trip_id: UUID,
        source_warehouse_id: UUID,
        inventory_items: List[Dict[str, Any]],
        created_by: UUID
    ) -> StockDoc:
        """Create stock document for transfer from warehouse to vehicle"""
        # Generate document number
        doc_no = f"TRF-TRUCK-LOAD-{trip_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Create stock document
        stock_doc = StockDoc.create(
            tenant_id=UUID("00000000-0000-0000-0000-000000000000"),  # Will be set from context
            doc_no=doc_no,
            doc_type=StockDocType.TRF_TRUCK,
            source_wh_id=source_warehouse_id,
            dest_wh_id=vehicle_id,  # Vehicle as destination warehouse
            ref_doc_id=trip_id,
            ref_doc_type="TRIP",
            notes=f"Load vehicle {vehicle_id} for trip {trip_id}",
            created_by=created_by
        )
        
        # Add stock document lines
        for item in inventory_items:
            line = StockDocLine.create(
                stock_doc_id=stock_doc.id,
                variant_id=UUID(item["variant_id"]),
                quantity=Decimal(str(item["quantity"])),
                unit_cost=Decimal(str(item.get("unit_cost", 0))),
                created_by=created_by
            )
            stock_doc.add_stock_doc_line(line)
        
        # Save stock document
        return await self.stock_doc_service.create_stock_doc(stock_doc)
    
    async def _create_vehicle_to_warehouse_transfer(
        self,
        vehicle_id: UUID,
        trip_id: UUID,
        destination_warehouse_id: UUID,
        actual_inventory: List[Dict[str, Any]],
        created_by: UUID
    ) -> StockDoc:
        """Create stock document for transfer from vehicle to warehouse"""
        # Generate document number
        doc_no = f"TRF-TRUCK-UNLOAD-{trip_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Create stock document
        stock_doc = StockDoc.create(
            tenant_id=UUID("00000000-0000-0000-0000-000000000000"),  # Will be set from context
            doc_no=doc_no,
            doc_type=StockDocType.TRF_TRUCK,
            source_wh_id=vehicle_id,  # Vehicle as source warehouse
            dest_wh_id=destination_warehouse_id,
            ref_doc_id=trip_id,
            ref_doc_type="TRIP",
            notes=f"Unload vehicle {vehicle_id} from trip {trip_id}",
            created_by=created_by
        )
        
        # Add stock document lines
        for item in actual_inventory:
            line = StockDocLine.create(
                stock_doc_id=stock_doc.id,
                variant_id=UUID(item["variant_id"]),
                quantity=Decimal(str(item["quantity"])),
                unit_cost=Decimal(str(item.get("unit_cost", 0))),
                created_by=created_by
            )
            stock_doc.add_stock_doc_line(line)
        
        # Save stock document
        return await self.stock_doc_service.create_stock_doc(stock_doc)
    
    async def _update_stock_levels_for_loading(
        self,
        vehicle_id: UUID,
        source_warehouse_id: UUID,
        inventory_items: List[Dict[str, Any]]
    ):
        """Update stock levels when loading vehicle"""
        for item in inventory_items:
            variant_id = UUID(item["variant_id"])
            quantity = Decimal(str(item["quantity"]))
            
            # Decrease warehouse stock (ON_HAND)
            await self.stock_level_service.adjust_stock_level(
                warehouse_id=source_warehouse_id,
                variant_id=variant_id,
                stock_status=StockStatus.ON_HAND,
                quantity_change=-quantity
            )
            
            # Increase vehicle stock (TRUCK_STOCK)
            await self.stock_level_service.adjust_stock_level(
                warehouse_id=vehicle_id,
                variant_id=variant_id,
                stock_status=StockStatus.TRUCK_STOCK,
                quantity_change=quantity
            )
    
    async def _update_stock_levels_for_unloading(
        self,
        vehicle_id: UUID,
        destination_warehouse_id: UUID,
        actual_inventory: List[Dict[str, Any]]
    ):
        """Update stock levels when unloading vehicle"""
        for item in actual_inventory:
            variant_id = UUID(item["variant_id"])
            quantity = Decimal(str(item["quantity"]))
            
            # Decrease vehicle stock (TRUCK_STOCK)
            await self.stock_level_service.adjust_stock_level(
                warehouse_id=vehicle_id,
                variant_id=variant_id,
                stock_status=StockStatus.TRUCK_STOCK,
                quantity_change=-quantity
            )
            
            # Increase warehouse stock (ON_HAND)
            await self.stock_level_service.adjust_stock_level(
                warehouse_id=destination_warehouse_id,
                variant_id=variant_id,
                stock_status=StockStatus.ON_HAND,
                quantity_change=quantity
            )
    
    async def _create_truck_inventory_records(
        self,
        trip_id: UUID,
        vehicle_id: UUID,
        inventory_items: List[Dict[str, Any]],
        created_by: UUID
    ) -> List[TruckInventory]:
        """Create truck inventory records for trip tracking"""
        truck_inventory_records = []
        
        for item in inventory_items:
            truck_inventory = TruckInventory.create(
                trip_id=trip_id,
                vehicle_id=vehicle_id,
                product_id=UUID(item["product_id"]),
                variant_id=UUID(item["variant_id"]),
                loaded_qty=Decimal(str(item["quantity"])),
                empties_expected_qty=Decimal(str(item.get("empties_expected_qty", 0))),
                created_by=created_by
            )
            truck_inventory_records.append(truck_inventory)
        
        return truck_inventory_records
    
    def _calculate_inventory_variances(
        self,
        actual_inventory: List[Dict[str, Any]],
        expected_inventory: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Calculate variances between expected and actual inventory"""
        variances = []
        
        # Create lookup dictionaries
        actual_lookup = {item["variant_id"]: item for item in actual_inventory}
        expected_lookup = {item["variant_id"]: item for item in expected_inventory}
        
        # Check all variants
        all_variants = set(actual_lookup.keys()) | set(expected_lookup.keys())
        
        for variant_id in all_variants:
            actual_qty = Decimal(str(actual_lookup.get(variant_id, {}).get("quantity", 0)))
            expected_qty = Decimal(str(expected_lookup.get(variant_id, {}).get("quantity", 0)))
            
            if actual_qty != expected_qty:
                variance = {
                    "variant_id": variant_id,
                    "expected_qty": float(expected_qty),
                    "actual_qty": float(actual_qty),
                    "variance_qty": float(actual_qty - expected_qty),
                    "variance_pct": float(((actual_qty - expected_qty) / expected_qty * 100) if expected_qty > 0 else 0)
                }
                variances.append(variance)
        
        return variances
    
    async def _create_variance_adjustments(
        self,
        vehicle_id: UUID,
        trip_id: UUID,
        destination_warehouse_id: UUID,
        variances: List[Dict[str, Any]],
        created_by: UUID
    ) -> List[StockDoc]:
        """Create variance adjustment documents"""
        variance_docs = []
        
        for variance in variances:
            if variance["variance_qty"] != 0:
                # Generate document number
                doc_no = f"ADJ-VAR-{trip_id}-{variance['variant_id']}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                
                # Create adjustment document
                stock_doc = StockDoc.create(
                    tenant_id=UUID("00000000-0000-0000-0000-000000000000"),  # Will be set from context
                    doc_no=doc_no,
                    doc_type=StockDocType.ADJ_VARIANCE,
                    dest_wh_id=destination_warehouse_id,
                    ref_doc_id=trip_id,
                    ref_doc_type="TRIP",
                    notes=f"Variance adjustment for variant {variance['variant_id']}: {variance['variance_qty']}",
                    created_by=created_by
                )
                
                # Add adjustment line
                line = StockDocLine.create(
                    stock_doc_id=stock_doc.id,
                    variant_id=UUID(variance["variant_id"]),
                    quantity=Decimal(str(abs(variance["variance_qty"]))),
                    unit_cost=Decimal("0"),  # Variance adjustments don't affect cost
                    created_by=created_by
                )
                stock_doc.add_stock_doc_line(line)
                
                # Save adjustment document
                saved_doc = await self.stock_doc_service.create_stock_doc(stock_doc)
                variance_docs.append(saved_doc)
        
        return variance_docs 