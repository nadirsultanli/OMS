from dataclasses import dataclass
from enum import Enum
from uuid import UUID
from datetime import datetime
from typing import List, Optional, Dict
from decimal import Decimal

class TripPlanningValidationResult(str, Enum):
    VALID = "valid"
    CAPACITY_EXCEEDED = "capacity_exceeded"
    WEIGHT_EXCEEDED = "weight_exceeded"
    VOLUME_EXCEEDED = "volume_exceeded"
    INSUFFICIENT_STOCK = "insufficient_stock"
    INVALID_ORDERS = "invalid_orders"

@dataclass
class TripPlanningLine:
    """Represents a planned product load for a trip"""
    product_id: UUID
    variant_id: UUID
    product_name: str
    variant_name: str
    ordered_qty: Decimal  # Total quantity ordered by customers
    planned_qty: Decimal  # Quantity planned to load (can be more than ordered)
    unit_weight_kg: Decimal
    unit_volume_m3: Decimal
    
    def get_total_weight(self) -> Decimal:
        """Calculate total weight for planned quantity"""
        return self.planned_qty * self.unit_weight_kg
    
    def get_total_volume(self) -> Decimal:
        """Calculate total volume for planned quantity"""
        return self.planned_qty * self.unit_volume_m3
    
    def to_dict(self) -> dict:
        return {
            "product_id": str(self.product_id),
            "variant_id": str(self.variant_id),
            "product_name": self.product_name,
            "variant_name": self.variant_name,
            "ordered_qty": float(self.ordered_qty),
            "planned_qty": float(self.planned_qty),
            "unit_weight_kg": float(self.unit_weight_kg),
            "unit_volume_m3": float(self.unit_volume_m3),
            "total_weight_kg": float(self.get_total_weight()),
            "total_volume_m3": float(self.get_total_volume())
        }

@dataclass
class TripPlan:
    """Represents a complete trip plan with orders, routing, and loading"""
    trip_id: UUID
    vehicle_id: UUID
    vehicle_capacity_kg: Decimal
    vehicle_capacity_m3: Decimal
    orders: List[UUID]  # List of order IDs in delivery sequence
    planning_lines: List[TripPlanningLine]
    total_weight_kg: Decimal
    total_volume_m3: Decimal
    validation_result: TripPlanningValidationResult
    validation_messages: List[str]
    
    @staticmethod
    def create(
        trip_id: UUID,
        vehicle_id: UUID,
        vehicle_capacity_kg: Decimal,
        vehicle_capacity_m3: Decimal = Decimal("0")
    ) -> "TripPlan":
        return TripPlan(
            trip_id=trip_id,
            vehicle_id=vehicle_id,
            vehicle_capacity_kg=vehicle_capacity_kg,
            vehicle_capacity_m3=vehicle_capacity_m3,
            orders=[],
            planning_lines=[],
            total_weight_kg=Decimal("0"),
            total_volume_m3=Decimal("0"),
            validation_result=TripPlanningValidationResult.VALID,
            validation_messages=[]
        )
    
    def add_order(self, order_id: UUID) -> None:
        """Add an order to the trip plan"""
        if order_id not in self.orders:
            self.orders.append(order_id)
    
    def remove_order(self, order_id: UUID) -> None:
        """Remove an order from the trip plan"""
        if order_id in self.orders:
            self.orders.remove(order_id)
    
    def reorder_stops(self, order_sequence: List[UUID]) -> None:
        """Reorder delivery stops"""
        # Validate all orders in sequence are in the plan
        if set(order_sequence) != set(self.orders):
            raise ValueError("Order sequence must contain exactly the same orders as the plan")
        self.orders = order_sequence
    
    def add_planning_line(self, line: TripPlanningLine) -> None:
        """Add a planning line and recalculate totals"""
        # Remove existing line for same product/variant if exists
        self.planning_lines = [
            l for l in self.planning_lines 
            if not (l.product_id == line.product_id and l.variant_id == line.variant_id)
        ]
        
        self.planning_lines.append(line)
        self._recalculate_totals()
    
    def update_planned_quantity(self, product_id: UUID, variant_id: UUID, new_qty: Decimal) -> None:
        """Update planned quantity for a specific product/variant"""
        for line in self.planning_lines:
            if line.product_id == product_id and line.variant_id == variant_id:
                line.planned_qty = new_qty
                self._recalculate_totals()
                return
        raise ValueError(f"Product {product_id} variant {variant_id} not found in planning lines")
    
    def _recalculate_totals(self) -> None:
        """Recalculate total weight and volume"""
        self.total_weight_kg = sum(line.get_total_weight() for line in self.planning_lines)
        self.total_volume_m3 = sum(line.get_total_volume() for line in self.planning_lines)
    
    def validate_plan(self) -> TripPlanningValidationResult:
        """Validate the trip plan against vehicle capacity"""
        self.validation_messages = []
        
        # Check weight capacity
        if self.total_weight_kg > self.vehicle_capacity_kg:
            self.validation_messages.append(
                f"Total weight {self.total_weight_kg}kg exceeds vehicle capacity {self.vehicle_capacity_kg}kg"
            )
            self.validation_result = TripPlanningValidationResult.WEIGHT_EXCEEDED
            return self.validation_result
        
        # Check volume capacity (if configured)
        if self.vehicle_capacity_m3 > 0 and self.total_volume_m3 > self.vehicle_capacity_m3:
            self.validation_messages.append(
                f"Total volume {self.total_volume_m3}m³ exceeds vehicle capacity {self.vehicle_capacity_m3}m³"
            )
            self.validation_result = TripPlanningValidationResult.VOLUME_EXCEEDED
            return self.validation_result
        
        # Check if planned quantities meet ordered quantities
        for line in self.planning_lines:
            if line.planned_qty < line.ordered_qty:
                self.validation_messages.append(
                    f"Planned quantity {line.planned_qty} for {line.product_name} is less than ordered {line.ordered_qty}"
                )
                self.validation_result = TripPlanningValidationResult.INSUFFICIENT_STOCK
                return self.validation_result
        
        self.validation_result = TripPlanningValidationResult.VALID
        return self.validation_result
    
    def get_utilization_percentage(self) -> Dict[str, float]:
        """Get vehicle utilization percentages"""
        weight_utilization = float((self.total_weight_kg / self.vehicle_capacity_kg) * 100) if self.vehicle_capacity_kg > 0 else 0
        volume_utilization = float((self.total_volume_m3 / self.vehicle_capacity_m3) * 100) if self.vehicle_capacity_m3 > 0 else 0
        
        return {
            "weight_utilization_pct": weight_utilization,
            "volume_utilization_pct": volume_utilization
        }
    
    def to_dict(self) -> dict:
        return {
            "trip_id": str(self.trip_id),
            "vehicle_id": str(self.vehicle_id),
            "vehicle_capacity_kg": float(self.vehicle_capacity_kg),
            "vehicle_capacity_m3": float(self.vehicle_capacity_m3),
            "orders": [str(order_id) for order_id in self.orders],
            "planning_lines": [line.to_dict() for line in self.planning_lines],
            "total_weight_kg": float(self.total_weight_kg),
            "total_volume_m3": float(self.total_volume_m3),
            "validation_result": self.validation_result.value,
            "validation_messages": self.validation_messages,
            "utilization": self.get_utilization_percentage()
        }