import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID

from app.domain.entities.orders import Order, OrderLine
from app.domain.entities.customers import Customer
from app.domain.entities.variants import Variant
from app.domain.repositories.order_repository import OrderRepository
from app.domain.repositories.customer_repository import CustomerRepository
from app.domain.repositories.variant_repository import VariantRepository
from app.services.deliveries.delivery_service import DeliveryService
from app.infrastucture.logs.logger import get_logger

logger = get_logger(__name__)

class LostEmptyProcessor:
    """Background processor for automatically handling lost empty cylinders"""
    
    def __init__(
        self,
        delivery_service: DeliveryService,
        order_repo: OrderRepository,
        customer_repo: CustomerRepository,
        variant_repo: VariantRepository
    ):
        self.delivery_service = delivery_service
        self.order_repo = order_repo
        self.customer_repo = customer_repo
        self.variant_repo = variant_repo
        self.is_running = False
        self.default_days_overdue = 30

    async def start_processing(self, interval_minutes: int = 60) -> None:
        """Start the background processing loop"""
        if self.is_running:
            logger.warning("Lost empty processor is already running")
            return
            
        self.is_running = True
        logger.info(f"Starting lost empty processor with {interval_minutes} minute interval")
        
        try:
            while self.is_running:
                await self.process_lost_empties()
                await asyncio.sleep(interval_minutes * 60)  # Convert to seconds
        except Exception as e:
            logger.error(f"Error in lost empty processor: {str(e)}")
            self.is_running = False
            raise

    async def stop_processing(self) -> None:
        """Stop the background processing loop"""
        self.is_running = False
        logger.info("Stopping lost empty processor")

    async def process_lost_empties(self) -> None:
        """Process all overdue empty returns"""
        try:
            logger.info("Starting lost empty processing cycle")
            
            # Get all customers with active orders
            customers = await self.customer_repo.get_all_active()
            
            total_processed = 0
            total_converted = 0
            
            for customer in customers:
                try:
                    customer_converted = await self._process_customer_lost_empties(customer)
                    if customer_converted > 0:
                        total_converted += customer_converted
                    total_processed += 1
                except Exception as e:
                    logger.error(f"Error processing customer {customer.id}: {str(e)}")
                    continue
            
            logger.info(f"Lost empty processing complete: {total_processed} customers processed, {total_converted} conversions")
            
        except Exception as e:
            logger.error(f"Error in process_lost_empties: {str(e)}")
            raise

    async def _process_customer_lost_empties(self, customer: Customer) -> int:
        """Process lost empties for a specific customer"""
        try:
            # Get customer's orders with EMPTY_RETURN lines
            customer_orders = await self.order_repo.get_by_customer_id(customer.id)
            
            converted_count = 0
            
            for order in customer_orders:
                # Check if order is old enough for lost empty processing
                if not self._is_order_eligible_for_lost_empty(order):
                    continue
                
                order_lines = await self.order_repo.get_lines_by_order_id(order.id)
                
                for line in order_lines:
                    if (line.component_type == 'EMPTY_RETURN' and 
                        line.qty_delivered > 0 and
                        line.variant_id):
                        
                        # Check if this empty return is overdue
                        if self._is_empty_return_overdue(order, self.default_days_overdue):
                            try:
                                converted = await self.delivery_service.handle_lost_empty_cylinder(
                                    customer_id=customer.id,
                                    variant_id=line.variant_id,
                                    days_overdue=self.default_days_overdue,
                                    actor_id=None  # System action
                                )
                                
                                if converted:
                                    converted_count += 1
                                    logger.info(f"Converted lost empty for customer {customer.id}, variant {line.variant_id}")
                                    
                            except Exception as e:
                                logger.error(f"Error converting lost empty for customer {customer.id}, variant {line.variant_id}: {str(e)}")
                                continue
            
            return converted_count
            
        except Exception as e:
            logger.error(f"Error processing customer {customer.id} lost empties: {str(e)}")
            raise

    def _is_order_eligible_for_lost_empty(self, order: Order) -> bool:
        """Check if order is eligible for lost empty processing"""
        # Only process orders that are at least 30 days old
        min_age_days = 30
        order_age = (datetime.now() - order.created_at).days
        return order_age >= min_age_days

    def _is_empty_return_overdue(self, order: Order, days_overdue: int) -> bool:
        """Check if empty return from this order is overdue"""
        order_age = (datetime.now() - order.created_at).days
        return order_age >= days_overdue

    async def process_specific_customer(
        self,
        customer_id: UUID,
        days_overdue: Optional[int] = None
    ) -> Dict[str, Any]:
        """Process lost empties for a specific customer (manual trigger)"""
        try:
            customer = await self.customer_repo.get_by_id(customer_id)
            if not customer:
                raise ValueError(f"Customer {customer_id} not found")
            
            if days_overdue is None:
                days_overdue = self.default_days_overdue
            
            converted_count = await self._process_customer_lost_empties(customer)
            
            return {
                "success": True,
                "customer_id": str(customer_id),
                "converted_count": converted_count,
                "days_overdue": days_overdue,
                "message": f"Processed {converted_count} lost empty conversions"
            }
            
        except Exception as e:
            logger.error(f"Error processing specific customer {customer_id}: {str(e)}")
            return {
                "success": False,
                "customer_id": str(customer_id),
                "error": str(e)
            }

    async def get_lost_empty_summary(self) -> Dict[str, Any]:
        """Get summary of potential lost empty cylinders"""
        try:
            # Get all customers with potential lost empties
            customers = await self.customer_repo.get_all_active()
            
            summary = {
                "total_customers": len(customers),
                "customers_with_overdue_empties": 0,
                "total_overdue_empties": 0,
                "potential_conversions": 0
            }
            
            for customer in customers:
                try:
                    customer_summary = await self._get_customer_lost_empty_summary(customer)
                    if customer_summary["overdue_empties"] > 0:
                        summary["customers_with_overdue_empties"] += 1
                        summary["total_overdue_empties"] += customer_summary["overdue_empties"]
                        summary["potential_conversions"] += customer_summary["potential_conversions"]
                except Exception as e:
                    logger.error(f"Error getting summary for customer {customer.id}: {str(e)}")
                    continue
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting lost empty summary: {str(e)}")
            raise

    async def _get_customer_lost_empty_summary(self, customer: Customer) -> Dict[str, Any]:
        """Get lost empty summary for a specific customer"""
        try:
            customer_orders = await self.order_repo.get_by_customer_id(customer.id)
            
            overdue_empties = 0
            potential_conversions = 0
            
            for order in customer_orders:
                if not self._is_order_eligible_for_lost_empty(order):
                    continue
                
                order_lines = await self.order_repo.get_lines_by_order_id(order.id)
                
                for line in order_lines:
                    if (line.component_type == 'EMPTY_RETURN' and 
                        line.qty_delivered > 0 and
                        line.variant_id):
                        
                        if self._is_empty_return_overdue(order, self.default_days_overdue):
                            overdue_empties += 1
                            potential_conversions += 1
            
            return {
                "customer_id": str(customer.id),
                "customer_name": customer.name,
                "overdue_empties": overdue_empties,
                "potential_conversions": potential_conversions
            }
            
        except Exception as e:
            logger.error(f"Error getting customer summary for {customer.id}: {str(e)}")
            raise 