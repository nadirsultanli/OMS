from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timezone
from decimal import Decimal
from app.domain.entities.vehicles import Vehicle
from app.domain.entities.truck_inventory import TruckInventory
from app.domain.entities.stock_docs import StockDoc, StockDocLine, StockDocType, StockStatus
from app.domain.entities.stock_levels import StockLevel
from app.domain.entities.users import User
from app.services.stock_docs.stock_doc_service import StockDocService
from app.services.stock_levels.stock_level_service import StockLevelService
from app.infrastucture.logs.logger import default_logger


class VehicleWarehouseService:
    """Service for treating vehicles as mobile warehouses during trips"""
    
    def __init__(
        self, 
        stock_doc_service: StockDocService,
        stock_level_service: StockLevelService,
        vehicle_service=None,
        variant_service=None,
        truck_inventory_repository=None
    ):
        self.stock_doc_service = stock_doc_service
        self.stock_level_service = stock_level_service
        self.vehicle_service = vehicle_service
        self.variant_service = variant_service
        self.truck_inventory_repository = truck_inventory_repository
    
    async def load_vehicle_as_warehouse(
        self,
        vehicle_id: UUID,
        trip_id: UUID,
        source_warehouse_id: UUID,
        inventory_items: List[Any],  # Can be List[Dict] or List[InventoryItem]
        loaded_by: UUID,
        user: Optional[User] = None
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
                created_by=loaded_by,
                user=user
            )
            
            # Note: We don't create stock levels for vehicles since they're not warehouses
            # Vehicle inventory is tracked in the truck_inventory table
            # The stock document will handle the transfer from warehouse ON_HAND to TRUCK_STOCK
            
            # Create truck inventory records for trip tracking
            truck_inventory_records = await self._create_truck_inventory_records(
                trip_id=trip_id,
                vehicle_id=vehicle_id,
                inventory_items=inventory_items,
                created_by=loaded_by
            )
            
            # Save truck inventory records to database
            if self.truck_inventory_repository:
                new_records_count = 0
                updated_records_count = 0
                
                for record in truck_inventory_records:
                    # Check if this is a new record (no ID) or existing record (has ID)
                    if not record.id:
                        # New record - create it
                        await self.truck_inventory_repository.create_truck_inventory(record)
                        new_records_count += 1
                    else:
                        # Existing record - update it
                        await self.truck_inventory_repository.update_truck_inventory(record.id, record)
                        updated_records_count += 1
                
                default_logger.info(f"Saved {new_records_count} new and updated {updated_records_count} existing truck inventory records to database")
            else:
                default_logger.warning("TruckInventoryRepository not available, records not saved")
                for record in truck_inventory_records:
                    default_logger.info(f"Truck inventory record: {record.to_dict()}")
            
            default_logger.info(
                f"Vehicle loaded as warehouse",
                vehicle_id=str(vehicle_id),
                trip_id=str(trip_id),
                stock_doc_id=str(stock_doc.id),
                items_count=len(inventory_items)
            )
            
            # Calculate totals safely
            total_weight_kg = 0.0
            total_volume_m3 = 0.0
            
            for item in inventory_items:
                # Handle both dict and Pydantic model
                if hasattr(item, 'quantity') and hasattr(item, 'unit_weight_kg') and hasattr(item, 'unit_volume_m3'):
                    # Pydantic model
                    qty = float(item.quantity)
                    unit_weight = float(item.unit_weight_kg)
                    unit_volume = float(item.unit_volume_m3)
                else:
                    # Dict
                    qty = float(item.get("quantity", 0))
                    unit_weight = float(item.get("unit_weight_kg", 0))
                    unit_volume = float(item.get("unit_volume_m3", 0))
                
                total_weight_kg += qty * unit_weight
                total_volume_m3 += qty * unit_volume
            
            return {
                "success": True,
                "stock_doc_id": str(stock_doc.id),
                "truck_inventory_count": len(truck_inventory_records),
                "total_weight_kg": total_weight_kg,
                "total_volume_m3": total_volume_m3
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
        unloaded_by: UUID,
        user: User
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
                    created_by=unloaded_by,
                    user=user
                )
            
            # Update stock levels
            await self._update_stock_levels_for_unloading(
                vehicle_id=vehicle_id,
                destination_warehouse_id=destination_warehouse_id,
                actual_inventory=actual_inventory,
                user=user
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
                "total_weight_kg": float(sum(getattr(item, "total_weight_kg", 0) if hasattr(item, "total_weight_kg") else item.get("total_weight_kg", 0) for item in actual_inventory)),
                "total_volume_m3": float(sum(getattr(item, "total_volume_m3", 0) if hasattr(item, "total_volume_m3") else item.get("total_volume_m3", 0) for item in actual_inventory))
            }
            
        except Exception as e:
            default_logger.error(f"Failed to unload vehicle as warehouse: {str(e)}")
            raise
    
    async def get_vehicle_inventory_as_warehouse(
        self,
        vehicle_id: UUID,
        trip_id: Optional[UUID] = None,
        user: Optional[User] = None
    ) -> Dict[str, Any]:
        """
        Get current inventory on vehicle using stock_levels (vehicle as warehouse)
        """
        try:
            default_logger.info(f"Getting vehicle inventory for vehicle {vehicle_id}, trip {trip_id}")
            
            # Get vehicle inventory from truck_inventory table
            # Vehicles are not warehouses, so we don't query stock_levels
            truck_inventory_items = []
            total_weight_kg = 0.0
            total_volume_m3 = 0.0
            
            # Import the database session and models to query truck_inventory with product/variant details
            from app.infrastucture.database.connection import direct_db_connection
            from app.infrastucture.database.models.truck_inventory import TruckInventoryModel
            from app.infrastucture.database.models.products import Product
            from app.infrastucture.database.models.variants import Variant
            from sqlalchemy import select, and_, join
            from sqlalchemy.orm import selectinload
            
            # Get tenant ID from user context or fallback to a default
            if user and user.tenant_id:
                tenant_id = user.tenant_id
            else:
                # Fallback: could also be passed as parameter or retrieved from context
                tenant_id = UUID("332072c1-5405-4f09-a56f-a631defa911b")
            
            # Get database session using the direct connection
            async for session in direct_db_connection.get_session():
                # Get truck inventory with product and variant details using JOIN
                truck_inventory_query = select(
                    TruckInventoryModel,
                    Product.name.label('product_name'),
                    Variant.sku.label('variant_name'),
                    Variant.unit_weight_kg,
                    Variant.unit_volume_m3,
                    Variant.default_price.label('unit_cost')
                ).join(
                    Variant, TruckInventoryModel.variant_id == Variant.id
                ).join(
                    Product, Variant.product_id == Product.id
                ).where(
                    and_(
                        TruckInventoryModel.vehicle_id == vehicle_id,
                        TruckInventoryModel.trip_id == trip_id if trip_id else True
                    )
                )
                
                result = await session.execute(truck_inventory_query)
                truck_inventory_records = result.all()
                
                default_logger.info(f"Found {len(truck_inventory_records)} truck inventory records for vehicle {vehicle_id}")
                
                # Fallback weights and costs for variants without database details
                default_weight_kg = 27.0  # Default cylinder weight
                default_volume_m3 = 0.036  # Default cylinder volume
                default_cost = 0.0  # Default cost
                
                # Convert truck inventory records to inventory format
                for record in truck_inventory_records:
                    # Extract data from the joined result
                    truck_inv = record[0]  # TruckInventoryModel
                    product_name = record[1] or "Unknown Product"  # Product.name
                    variant_name = record[2] or "Unknown Variant"  # Variant.sku
                    unit_weight_kg = float(record[3]) if record[3] is not None else default_weight_kg
                    unit_volume_m3 = float(record[4]) if record[4] is not None else default_volume_m3
                    unit_cost = float(record[5]) if record[5] is not None else default_cost
                    
                    remaining_qty = float(truck_inv.loaded_qty - truck_inv.delivered_qty)
                    item_weight = unit_weight_kg * remaining_qty
                    item_volume = unit_volume_m3 * remaining_qty
                    total_cost = unit_cost * remaining_qty
                    
                    total_weight_kg += item_weight
                    total_volume_m3 += item_volume
                    
                    truck_inventory_items.append({
                        "product_id": str(truck_inv.product_id),
                        "variant_id": str(truck_inv.variant_id),
                        "product_name": product_name,
                        "variant_name": variant_name,
                        "loaded_qty": float(truck_inv.loaded_qty),
                        "delivered_qty": float(truck_inv.delivered_qty),
                        "remaining_qty": remaining_qty,
                        "empties_expected_qty": float(truck_inv.empties_expected_qty),
                        "empties_collected_qty": float(truck_inv.empties_collected_qty),
                        "unit_weight_kg": unit_weight_kg,
                        "unit_volume_m3": unit_volume_m3,
                        "unit_cost": unit_cost,
                        "total_cost": total_cost,
                        "total_weight_kg": item_weight,
                        "total_volume_m3": item_volume
                    })
            
            # Convert to inventory format for API
            # Note: Vehicles are not warehouses, so we don't create stock level entries
            inventory_items = []
            for item in truck_inventory_items:
                inventory_items.append({
                    "warehouse_id": None,  # Vehicle is not a warehouse
                    "variant_id": item["variant_id"],
                    "product_id": item["product_id"],
                    "product_name": item["product_name"],
                    "variant_name": item["variant_name"],
                    "stock_status": "TRUCK_STOCK",
                    "quantity": item["remaining_qty"],
                    "reserved_qty": 0.0,  # No reservations on vehicle
                    "available_qty": item["remaining_qty"],
                    "unit_cost": item["unit_cost"],
                    "total_cost": item["total_cost"],
                    "unit_weight_kg": item["unit_weight_kg"],
                    "unit_volume_m3": item["unit_volume_m3"],
                    "total_weight_kg": item["total_weight_kg"],
                    "total_volume_m3": item["total_volume_m3"],
                    "last_transaction_date": None
                })
            
            # Get vehicle details from database if service is available
            vehicle_details = {}
            if self.vehicle_service:
                try:
                    vehicle = await self.vehicle_service.get_vehicle_by_id(vehicle_id)
                    if vehicle:
                        vehicle_details = {
                            "id": str(vehicle_id),
                            "plate": getattr(vehicle, 'plate', f"VEH-{str(vehicle_id)[:8]}"),
                            "vehicle_type": getattr(vehicle, 'vehicle_type', "TRUCK"),
                            "capacity_kg": float(getattr(vehicle, 'capacity_kg', 2000)),
                            "capacity_m3": float(getattr(vehicle, 'capacity_m3', 20)) if getattr(vehicle, 'capacity_m3', None) else 20.0,
                            "current_load_kg": total_weight_kg,
                            "current_volume_m3": total_volume_m3
                        }
                except Exception as e:
                    default_logger.warning(f"Failed to fetch vehicle details for {vehicle_id}: {e}")
            
            # Fallback vehicle details if service is not available or fails
            if not vehicle_details:
                vehicle_details = {
                    "id": str(vehicle_id),
                    "plate": f"VEH-{str(vehicle_id)[:8]}",
                    "vehicle_type": "TRUCK",
                    "capacity_kg": 2000.0,  # Default capacity
                    "capacity_m3": 20.0,    # Default capacity
                    "current_load_kg": total_weight_kg,
                    "current_volume_m3": total_volume_m3
                }
            
            # Return structured data with both stock levels and truck inventory
            vehicle_data = {
                "vehicle": vehicle_details,
                "inventory": inventory_items,
                "truck_inventory": truck_inventory_items
            }
            
            default_logger.info(f"Found {len(inventory_items)} inventory items and {len(truck_inventory_items)} truck inventory items for vehicle {vehicle_id}. Total weight: {total_weight_kg}kg, Total volume: {total_volume_m3}m³")
            
            return vehicle_data
            
        except Exception as e:
            default_logger.error(f"Failed to get vehicle inventory: {str(e)}")
            raise
    
    async def validate_vehicle_capacity(
        self,
        vehicle: Vehicle,
        inventory_items: List[Any]  # Can be List[Dict] or List[InventoryItem]
    ) -> Dict[str, Any]:
        """
        Validate if inventory items fit within vehicle capacity
        """
        try:
            total_weight_kg = Decimal("0")
            total_volume_m3 = Decimal("0")
            
            for item in inventory_items:
                # Handle both dict and Pydantic model
                if hasattr(item, 'quantity'):
                    # Pydantic model
                    qty = Decimal(str(item.quantity))
                    unit_weight = Decimal(str(item.unit_weight_kg))
                    unit_volume = Decimal(str(item.unit_volume_m3))
                else:
                    # Dict
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
        inventory_items: List[Any],  # Can be List[Dict] or List[InventoryItem]
        created_by: UUID,
        user: Optional[User] = None
    ) -> StockDoc:
        """Create stock document for transfer from warehouse to vehicle"""
        # Generate document number
        doc_no = f"TRF-TRUCK-LOAD-{trip_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Convert inventory items to stock doc lines format
        stock_doc_lines = []
        for item in inventory_items:
            # Handle both dict and Pydantic model
            if hasattr(item, 'variant_id'):
                # Pydantic model
                variant_id = item.variant_id
                quantity = item.quantity
                unit_cost = getattr(item, 'unit_cost', 0)
            else:
                # Dict
                variant_id = item["variant_id"]
                quantity = item["quantity"]
                unit_cost = item.get("unit_cost", 0)
            
            stock_doc_lines.append({
                'variant_id': UUID(variant_id),
                'quantity': Decimal(str(quantity)),
                'unit_cost': Decimal(str(unit_cost))
            })
        
        # Create stock document using the service
        if user is None:
            raise ValueError("User context is required for stock document creation. Please provide a valid user.")
        
        # For vehicle loading, we create a transfer from source warehouse to vehicle's depot
        # The stock document service will handle the transfer from ON_HAND to TRUCK_STOCK
        stock_doc = await self.stock_doc_service.create_stock_doc(
            user=user,
            doc_type=StockDocType.TRF_TRUCK,
            source_wh_id=source_warehouse_id,
            dest_wh_id=None,  # No destination warehouse - this triggers ON_HAND to TRUCK_STOCK transfer
            ref_doc_id=trip_id,
            ref_doc_type="TRIP",
            notes=f"Load vehicle {vehicle_id} for trip {trip_id}",
            stock_doc_lines=stock_doc_lines
        )
        
        # Post the stock document to trigger stock level updates
        await self.stock_doc_service.post_stock_document(user, str(stock_doc.id))
        
        # Now manually transfer stock from ON_HAND to TRUCK_STOCK for each item
        from app.services.stock_levels.stock_level_service import StockLevelService
        from app.services.dependencies.stock_levels import get_stock_level_service
        
        # Update stock levels to reflect transfer from ON_HAND to TRUCK_STOCK
        for item in inventory_items:
            # Handle both dict and Pydantic model
            if hasattr(item, 'variant_id'):
                variant_id = UUID(item.variant_id)
                quantity = Decimal(str(item.quantity))
            else:
                variant_id = UUID(item["variant_id"])
                quantity = Decimal(str(item["quantity"]))
            
            # Issue from ON_HAND in source warehouse
            await self.stock_level_service.issue_stock(
                user=user,
                warehouse_id=source_warehouse_id,
                variant_id=variant_id,
                quantity=quantity,
                stock_status=StockStatus.ON_HAND,
                allow_negative=False
            )
            
            # Receive into TRUCK_STOCK in source warehouse (vehicle inventory is tracked in source warehouse with TRUCK_STOCK status)
            await self.stock_level_service.receive_stock(
                user=user,
                warehouse_id=source_warehouse_id,
                variant_id=variant_id,
                quantity=quantity,
                stock_status=StockStatus.TRUCK_STOCK
            )
        
        return stock_doc
    
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
        
        # Convert inventory items to stock doc lines format
        stock_doc_lines = []
        for item in actual_inventory:
            # Handle both dict and Pydantic model
            if hasattr(item, 'variant_id'):
                # Pydantic model
                variant_id = item.variant_id
                quantity = item.quantity
                unit_cost = getattr(item, 'unit_cost', 0)
            else:
                # Dict
                variant_id = item["variant_id"]
                quantity = item["quantity"]
                unit_cost = item.get("unit_cost", 0)
            
            stock_doc_lines.append({
                'variant_id': UUID(variant_id),
                'quantity': Decimal(str(quantity)),
                'unit_cost': Decimal(str(unit_cost))
            })
        
        # Create stock document using the service
        # Note: This method should be updated to accept and require a user parameter
        from app.domain.entities.users import User
        mock_user = User(
            id=created_by,
            tenant_id=UUID("00000000-0000-0000-0000-000000000000"),  # TODO: Pass tenant_id from context
            auth_id=UUID("00000000-0000-0000-0000-000000000000"),
            email="system@oms.com",
            first_name="System",
            last_name="User",
            role="ADMIN",
            active=True
        )
        
        return await self.stock_doc_service.create_stock_doc(
            user=mock_user,
            doc_type=StockDocType.TRF_TRUCK,
            source_wh_id=vehicle_id,  # Vehicle as source warehouse
            dest_wh_id=destination_warehouse_id,
            ref_doc_id=trip_id,
            ref_doc_type="TRIP",
            notes=f"Unload vehicle {vehicle_id} from trip {trip_id}",
            stock_doc_lines=stock_doc_lines
        )
    
    async def _update_stock_levels_for_loading(
        self,
        vehicle_id: UUID,
        source_warehouse_id: UUID,
        inventory_items: List[Any],  # Can be List[Dict] or List[InventoryItem]
        user: Optional[User] = None
    ):
        """Update stock levels when loading vehicle"""
        for item in inventory_items:
            # Handle both dict and Pydantic model
            if hasattr(item, 'variant_id'):
                # Pydantic model
                variant_id = UUID(item.variant_id)
                quantity = Decimal(str(item.quantity))
            else:
                # Dict
                variant_id = UUID(item["variant_id"])
                quantity = Decimal(str(item["quantity"]))
            
            # Decrease warehouse stock (ON_HAND) - items are being loaded onto vehicle
            # User is required for the stock level service
            if user is None:
                raise ValueError("User context is required for stock level operations. Please provide a valid user.")
            
            await self.stock_level_service.issue_stock(
                user=user,
                warehouse_id=source_warehouse_id,
                variant_id=variant_id,
                quantity=quantity,
                stock_status=StockStatus.ON_HAND,
                allow_negative=False
            )
            
            # Note: Vehicle inventory is tracked separately in truck_inventory table
            # We don't create stock levels for vehicles since they're not warehouses
            # The truck_inventory table handles the vehicle inventory tracking
    
    async def _update_stock_levels_for_unloading(
        self,
        vehicle_id: UUID,
        destination_warehouse_id: UUID,
        actual_inventory: List[Dict[str, Any]],
        user: Optional[User] = None
    ):
        """Update stock levels when unloading vehicle"""
        # User is required for stock level operations
        if user is None:
            raise ValueError("User context is required for stock level operations. Please provide a valid user.")
        
        for item in actual_inventory:
            variant_id = UUID(item["variant_id"])
            quantity = Decimal(str(item["quantity"]))
            
            # Note: We don't track vehicle stock levels since vehicles aren't warehouses
            # The truck_inventory table handles vehicle inventory tracking
            
            # Increase warehouse stock (ON_HAND) - items being unloaded to warehouse
            await self.stock_level_service.receive_stock(
                user=user,
                warehouse_id=destination_warehouse_id,
                variant_id=variant_id,
                quantity=quantity,
                stock_status=StockStatus.ON_HAND
            )
    
    async def _create_truck_inventory_records(
        self,
        trip_id: UUID,
        vehicle_id: UUID,
        inventory_items: List[Any],  # Can be List[Dict] or List[InventoryItem]
        created_by: UUID
    ) -> List[TruckInventory]:
        """Create truck inventory records for trip tracking"""
        truck_inventory_records = []
        
        # Import the database session to check for existing records
        from app.infrastucture.database.connection import direct_db_connection
        from app.infrastucture.database.models.truck_inventory import TruckInventoryModel
        from sqlalchemy import select, and_
        
        async for session in direct_db_connection.get_session():
            for item in inventory_items:
                # Handle both dict and Pydantic model
                if hasattr(item, 'product_id'):
                    # Pydantic model
                    product_id = UUID(item.product_id)
                    variant_id = UUID(item.variant_id)
                    quantity = Decimal(str(item.quantity))
                    empties_expected_qty = Decimal(str(getattr(item, 'empties_expected_qty', 0)))
                else:
                    # Dict
                    product_id = UUID(item["product_id"])
                    variant_id = UUID(item["variant_id"])
                    quantity = Decimal(str(item["quantity"]))
                    empties_expected_qty = Decimal(str(item.get("empties_expected_qty", 0)))
                
                # Check if record already exists
                existing_query = select(TruckInventoryModel).where(
                    and_(
                        TruckInventoryModel.trip_id == trip_id,
                        TruckInventoryModel.vehicle_id == vehicle_id,
                        TruckInventoryModel.product_id == product_id,
                        TruckInventoryModel.variant_id == variant_id
                    )
                )
                
                result = await session.execute(existing_query)
                existing_record = result.scalar_one_or_none()
                
                if existing_record:
                    # Update existing record by adding to loaded_qty
                    existing_record.loaded_qty += quantity
                    existing_record.empties_expected_qty += empties_expected_qty
                    existing_record.updated_by = created_by
                    existing_record.updated_at = datetime.now(timezone.utc)
                    
                    # Convert to domain entity for return
                    truck_inventory = TruckInventory(
                        id=existing_record.id,
                        trip_id=existing_record.trip_id,
                        vehicle_id=existing_record.vehicle_id,
                        product_id=existing_record.product_id,
                        variant_id=existing_record.variant_id,
                        loaded_qty=existing_record.loaded_qty,
                        delivered_qty=existing_record.delivered_qty,
                        empties_collected_qty=existing_record.empties_collected_qty,
                        empties_expected_qty=existing_record.empties_expected_qty,
                        created_at=existing_record.created_at,
                        created_by=existing_record.created_by,
                        updated_at=existing_record.updated_at,
                        updated_by=existing_record.updated_by
                    )
                    truck_inventory_records.append(truck_inventory)
                    
                    default_logger.info(f"Updated existing truck inventory record for variant {variant_id}")
                else:
                    # Create new record
                    truck_inventory = TruckInventory.create(
                        trip_id=trip_id,
                        vehicle_id=vehicle_id,
                        product_id=product_id,
                        variant_id=variant_id,
                        loaded_qty=quantity,
                        empties_expected_qty=empties_expected_qty,
                        created_by=created_by
                    )
                    truck_inventory_records.append(truck_inventory)
                    
                    default_logger.info(f"Created new truck inventory record for variant {variant_id}")
            
            break  # Exit the async for loop after first iteration
        
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
        created_by: UUID,
        user: Optional[User] = None
    ) -> List[StockDoc]:
        """Create variance adjustment documents"""
        variance_docs = []
        
        for variance in variances:
            if variance["variance_qty"] != 0:
                # Generate document number
                doc_no = f"ADJ-VAR-{trip_id}-{variance['variant_id']}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                
                # Create adjustment document
                if user is None:
                    raise ValueError("User context is required for variance adjustment creation.")
                
                stock_doc = StockDoc.create(
                    tenant_id=user.tenant_id,
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