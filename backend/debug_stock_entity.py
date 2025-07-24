#!/usr/bin/env python3
"""
Debug the StockLevel entity to find the exact error
"""

import asyncio
from decimal import Decimal
from uuid import uuid4
from datetime import datetime

# Add the app directory to Python path
import sys
import os
sys.path.append('/home/riadsultanov/Documents/OMSProject/OMS/backend')

try:
    from app.domain.entities.stock_levels import StockLevel
    from app.domain.entities.stock_docs import StockStatus
    print("✅ Successfully imported StockLevel entity")
except ImportError as e:
    print(f"❌ Failed to import StockLevel: {e}")
    exit(1)

def test_stock_level_entity():
    """Test StockLevel entity creation and methods"""
    
    print("\n🧪 Testing StockLevel Entity Creation and Methods")
    print("=" * 55)
    
    try:
        # Test 1: Create a new StockLevel entity (simulating repository creation)
        print("\n1️⃣ Testing StockLevel creation...")
        
        stock_level = StockLevel(
            id=uuid4(),
            tenant_id=uuid4(),
            warehouse_id=uuid4(),
            variant_id=uuid4(),
            stock_status=StockStatus.ON_HAND,
            quantity=Decimal('0'),
            reserved_qty=Decimal('0'),
            available_qty=Decimal('0'),
            unit_cost=Decimal('0'),
            total_cost=Decimal('0')
        )
        
        print("✅ StockLevel created successfully")
        print(f"   Initial quantity: {stock_level.quantity}")
        print(f"   Initial unit_cost: {stock_level.unit_cost}")
        print(f"   Initial total_cost: {stock_level.total_cost}")
        
    except Exception as e:
        print(f"❌ Failed to create StockLevel: {e}")
        return False
    
    try:
        # Test 2: Test add_quantity method
        print("\n2️⃣ Testing add_quantity method...")
        
        # This simulates what happens in the repository
        stock_level.add_quantity(Decimal('15.0'), Decimal('30.0'))
        
        print("✅ add_quantity successful")
        print(f"   New quantity: {stock_level.quantity}")
        print(f"   New unit_cost: {stock_level.unit_cost}")
        print(f"   New total_cost: {stock_level.total_cost}")
        print(f"   Available qty: {stock_level.available_qty}")
        
    except Exception as e:
        print(f"❌ add_quantity failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        return False
    
    try:
        # Test 3: Test with existing stock (simulating update scenario)
        print("\n3️⃣ Testing with existing stock levels...")
        
        # Create stock level with existing data (like from the database)
        existing_stock = StockLevel(
            id=uuid4(),
            tenant_id=uuid4(),
            warehouse_id=uuid4(),
            variant_id=uuid4(),
            stock_status=StockStatus.ON_HAND,
            quantity=Decimal('100.0'),  # Current quantity from DB
            reserved_qty=Decimal('10.0'),  # Current reserved from DB
            available_qty=Decimal('90.0'),  # Current available from DB
            unit_cost=Decimal('25.5'),  # Current unit cost from DB
            total_cost=Decimal('2550.0')  # Current total cost from DB
        )
        
        print(f"   Before adjustment - Qty: {existing_stock.quantity}, Cost: {existing_stock.unit_cost}, Total: {existing_stock.total_cost}")
        
        # Add 15 units at 30.0 cost (simulating the adjustment)
        existing_stock.add_quantity(Decimal('15.0'), Decimal('30.0'))
        
        print("✅ Existing stock adjustment successful")
        print(f"   After adjustment - Qty: {existing_stock.quantity}, Cost: {existing_stock.unit_cost}, Total: {existing_stock.total_cost}")
        
    except Exception as e:
        print(f"❌ Existing stock test failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        return False
    
    try:
        # Test 4: Test edge cases
        print("\n4️⃣ Testing edge cases...")
        
        # Test with zero unit cost
        edge_stock = StockLevel(
            id=uuid4(),
            tenant_id=uuid4(),
            warehouse_id=uuid4(),
            variant_id=uuid4(),
            stock_status=StockStatus.ON_HAND,
            quantity=Decimal('0'),
            reserved_qty=Decimal('0'),
            available_qty=Decimal('0'),
            unit_cost=Decimal('0'),
            total_cost=Decimal('0')
        )
        
        # Add quantity with zero cost
        edge_stock.add_quantity(Decimal('10.0'), Decimal('0'))
        print("✅ Zero cost test passed")
        
        # Add quantity with None cost
        edge_stock.add_quantity(Decimal('5.0'), None)
        print("✅ None cost test passed")
        
    except Exception as e:
        print(f"❌ Edge case test failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        return False
    
    print(f"\n🎉 All StockLevel entity tests passed!")
    return True

if __name__ == "__main__":
    success = test_stock_level_entity()
    
    if success:
        print("\n✅ StockLevel entity is working correctly!")
        print("   The issue is likely in the repository or database layer.")
    else:
        print("\n❌ StockLevel entity has issues!")
        print("   The error is in the domain entity logic.")