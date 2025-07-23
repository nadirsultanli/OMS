from typing import Dict, Any, List, Optional
from uuid import UUID
from decimal import Decimal
from app.domain.entities.users import User, UserRoleType
from app.domain.entities.orders import Order, OrderStatus
from app.domain.entities.customers import Customer
from app.domain.entities.products import Product
from app.domain.entities.variants import Variant
from app.infrastucture.logs.logger import default_logger

class DriverPermissionsService:
    """Service for managing driver permissions and limitations during trip execution"""
    
    def __init__(self):
        pass
    
    def validate_driver_can_create_order(self, driver: User, customer: Customer) -> Dict[str, Any]:
        """Validate if driver can create new orders for a customer"""
        validation = {
            "can_create_order": False,
            "reasons": [],
            "restrictions": {}
        }
        
        # Check if user is a driver
        if driver.role != UserRoleType.DRIVER:
            validation["reasons"].append("Only drivers can create orders during delivery")
            return validation
        
        # Driver can only create orders for cash customers
        if customer.customer_type.lower() != "cash":
            validation["reasons"].append("Drivers can only create orders for cash customers")
            validation["restrictions"]["customer_type"] = "cash_only"
            return validation
        
        # Driver can only create orders for customers in same tenant
        if customer.tenant_id != driver.tenant_id:
            validation["reasons"].append("Driver can only create orders for customers in same tenant")
            return validation
        
        validation["can_create_order"] = True
        validation["restrictions"] = {
            "customer_type": "cash_only",
            "payment_method": "cash_only",
            "pricing": "standard_pricing_only",
            "credit_terms": "none"
        }
        
        return validation
    
    def validate_driver_can_modify_quantities(
        self, 
        driver: User, 
        original_qty: Decimal, 
        new_qty: Decimal,
        product: Product,
        available_on_truck: Decimal
    ) -> Dict[str, Any]:
        """Validate if driver can modify delivery quantities"""
        validation = {
            "can_modify": False,
            "reasons": [],
            "limits": {}
        }
        
        # Check if user is a driver
        if driver.role != UserRoleType.DRIVER:
            validation["reasons"].append("Only drivers can modify delivery quantities")
            return validation
        
        # Driver can deliver more than ordered (upselling)
        if new_qty > original_qty:
            if new_qty > available_on_truck:
                validation["reasons"].append(
                    f"Cannot deliver {new_qty}, only {available_on_truck} available on truck"
                )
                validation["limits"]["max_quantity"] = float(available_on_truck)
                return validation
        
        # Driver can deliver less than ordered (customer doesn't want all)
        if new_qty < original_qty:
            if new_qty < 0:
                validation["reasons"].append("Delivered quantity cannot be negative")
                validation["limits"]["min_quantity"] = 0
                return validation
        
        validation["can_modify"] = True
        validation["limits"] = {
            "min_quantity": 0,
            "max_quantity": float(available_on_truck),
            "can_upsell": True,
            "can_partial_deliver": True
        }
        
        return validation
    
    def validate_driver_can_access_pricing(self, driver: User, customer: Customer) -> Dict[str, Any]:
        """Validate if driver can access or modify pricing"""
        validation = {
            "can_view_pricing": False,
            "can_modify_pricing": False,
            "pricing_restrictions": {}
        }
        
        # Check if user is a driver
        if driver.role != UserRoleType.DRIVER:
            return validation
        
        # Drivers can view standard pricing
        validation["can_view_pricing"] = True
        
        # Drivers CANNOT modify pricing
        validation["can_modify_pricing"] = False
        validation["pricing_restrictions"] = {
            "reason": "Drivers must use standard price list",
            "allowed_pricing": "standard_only",
            "discount_authority": "none",
            "special_pricing": "not_allowed"
        }
        
        return validation
    
    def validate_driver_can_create_customer(self, driver: User) -> Dict[str, Any]:
        """Validate if driver can create new customers"""
        validation = {
            "can_create_customer": False,
            "reasons": [],
            "required_approval": True
        }
        
        # Check if user is a driver
        if driver.role != UserRoleType.DRIVER:
            validation["reasons"].append("Only drivers can attempt customer creation")
            return validation
        
        # Drivers CANNOT create customers - requires office approval
        validation["reasons"].append("Customer creation requires office approval and documentation")
        validation["reasons"].append("Drivers can only serve existing customers")
        
        return validation
    
    def validate_driver_can_sell_product(
        self, 
        driver: User, 
        product: Product, 
        variant: Variant,
        truck_inventory: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate if driver can sell a specific product/variant"""
        validation = {
            "can_sell": False,
            "reasons": [],
            "available_quantity": 0
        }
        
        # Check if user is a driver
        if driver.role != UserRoleType.DRIVER:
            validation["reasons"].append("Only drivers can sell products")
            return validation
        
        # Check if product is available on truck
        product_key = f"{product.id}_{variant.id}"
        if product_key not in truck_inventory:
            validation["reasons"].append("Product not loaded on truck")
            return validation
        
        # Check available quantity
        truck_item = truck_inventory[product_key]
        remaining_qty = truck_item.get("remaining_qty", 0)
        
        if remaining_qty <= 0:
            validation["reasons"].append("No remaining quantity on truck")
            validation["available_quantity"] = 0
            return validation
        
        validation["can_sell"] = True
        validation["available_quantity"] = remaining_qty
        
        return validation
    
    def validate_driver_can_collect_payment(self, driver: User, customer: Customer, amount: Decimal) -> Dict[str, Any]:
        """Validate if driver can collect payment"""
        validation = {
            "can_collect": False,
            "reasons": [],
            "payment_restrictions": {}
        }
        
        # Check if user is a driver
        if driver.role != UserRoleType.DRIVER:
            validation["reasons"].append("Only drivers can collect payment")
            return validation
        
        # Check customer type
        if customer.customer_type.lower() != "cash":
            validation["reasons"].append("Drivers can only collect cash payments from cash customers")
            validation["payment_restrictions"]["customer_type"] = "cash_only"
            return validation
        
        # Check amount is positive
        if amount <= 0:
            validation["reasons"].append("Payment amount must be positive")
            validation["payment_restrictions"]["min_amount"] = 0.01
            return validation
        
        validation["can_collect"] = True
        validation["payment_restrictions"] = {
            "payment_method": "cash_only",
            "requires_receipt": True,
            "daily_limit": None,  # Could implement daily cash collection limits
            "reconciliation_required": True
        }
        
        return validation
    
    def get_driver_operation_summary(self, driver: User) -> Dict[str, Any]:
        """Get comprehensive summary of driver permissions and limitations"""
        return {
            "driver_id": str(driver.id),
            "driver_name": driver.full_name,
            "role": driver.role.value,
            "permissions": {
                "can_create_orders": True,
                "can_modify_quantities": True,
                "can_view_pricing": True,
                "can_modify_pricing": False,
                "can_create_customers": False,
                "can_collect_payment": True,
                "can_sell_truck_inventory": True
            },
            "restrictions": {
                "customer_types": ["cash_only"],
                "payment_methods": ["cash"],
                "pricing_authority": "standard_only",
                "inventory_scope": "truck_only",
                "geographic_scope": "assigned_route_only"
            },
            "requirements": {
                "customer_creation": "office_approval_required",
                "special_pricing": "office_approval_required",
                "credit_sales": "not_permitted",
                "cash_handling": "reconciliation_required",
                "proof_of_delivery": "signature_and_photos_required"
            },
            "business_rules": [
                "Can only sell products currently on truck",
                "Must use standard price list",
                "Can adjust quantities based on customer needs",
                "Must collect proof of delivery for all transactions",
                "Cash customers only - no credit arrangements",
                "Cannot create new customers without office approval"
            ]
        }
    
    def validate_driver_order_creation_request(
        self, 
        driver: User, 
        order_request: Dict[str, Any],
        truck_inventory: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Comprehensive validation for driver creating a new order"""
        validation = {
            "is_valid": True,
            "can_create": False,
            "validation_errors": [],
            "warnings": [],
            "order_restrictions": {}
        }
        
        try:
            # Basic driver permission check
            if driver.role != UserRoleType.DRIVER:
                validation["is_valid"] = False
                validation["validation_errors"].append("Only drivers can create orders")
                return validation
            
            # Validate customer type (would need actual customer data)
            customer_id = order_request.get("customer_id")
            if not customer_id:
                validation["is_valid"] = False
                validation["validation_errors"].append("Customer ID is required")
                return validation
            
            # Validate order lines
            order_lines = order_request.get("lines", [])
            if not order_lines:
                validation["is_valid"] = False
                validation["validation_errors"].append("Order must have at least one line item")
                return validation
            
            # Validate each line against truck inventory
            for line in order_lines:
                product_id = line.get("product_id")
                variant_id = line.get("variant_id")
                quantity = Decimal(str(line.get("quantity", 0)))
                
                # Check if product is on truck
                product_key = f"{product_id}_{variant_id}"
                if product_key not in truck_inventory:
                    validation["validation_errors"].append(
                        f"Product {product_id} variant {variant_id} not available on truck"
                    )
                    validation["is_valid"] = False
                    continue
                
                # Check quantity availability
                truck_item = truck_inventory[product_key]
                available_qty = truck_item.get("remaining_qty", 0)
                
                if quantity > available_qty:
                    validation["validation_errors"].append(
                        f"Requested quantity {quantity} exceeds available {available_qty} for product {product_id}"
                    )
                    validation["is_valid"] = False
                
                # Check pricing (driver must use standard pricing)
                if "custom_price" in line:
                    validation["warnings"].append(
                        f"Custom pricing ignored for product {product_id} - using standard price"
                    )
            
            # Set final validation result
            if validation["is_valid"]:
                validation["can_create"] = True
                validation["order_restrictions"] = {
                    "customer_type": "cash_only",
                    "payment_terms": "cash_on_delivery",
                    "pricing": "standard_only",
                    "delivery_date": "immediate"
                }
            
            return validation
            
        except Exception as e:
            default_logger.error(f"Error validating driver order creation: {str(e)}")
            validation["is_valid"] = False
            validation["validation_errors"].append("Validation error occurred")
            return validation