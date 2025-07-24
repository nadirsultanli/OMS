#!/usr/bin/env python3
"""
Debug the repository layer to find the exact error
"""

import asyncio
from decimal import Decimal
from uuid import UUID
import sys
import os

# Add the app directory to Python path
sys.path.append('/home/riadsultanov/Documents/OMSProject/OMS/backend')

try:
    from app.domain.entities.stock_levels import StockLevel
    from app.domain.entities.stock_docs import StockStatus
    print("✅ Successfully imported domain entities")
except ImportError as e:
    print(f"❌ Failed to import entities: {e}")
    exit(1)

async def test_repository_layer():
    """Test repository layer methods"""
    
    print("\n🔧 Testing Repository Layer")
    print("=" * 40)
    
    # Real data from user's system
    WAREHOUSE_ID = UUID("5bde8036-01d3-46dd-a150-ccb2951463ce")
    VARIANT_ID = UUID("726900a1-c5b3-469e-b30a-79a0a87f69fc")
    TENANT_ID = UUID("332072c1-5405-4f09-a56f-a631defa911b")
    
    try:
        # Import database dependencies
        from app.infrastucture.database.repositories.stock_level_repository import StockLevelRepository
        from app.infrastucture.database.core import get_session
        
        print("✅ Successfully imported repository")
        
        # Get database session
        session = get_session()
        repository = StockLevelRepository(session)
        
        print("✅ Database session created")
        
    except ImportError as e:
        print(f"❌ Failed to import repository: {e}")
        return False
    except Exception as e:
        print(f"❌ Failed to create session: {e}")
        return False
    
    try:
        # Test 1: Get existing stock level
        print(f"\n1️⃣ Testing get_stock_level...")
        
        existing_stock = await repository.get_stock_level(
            TENANT_ID, WAREHOUSE_ID, VARIANT_ID, StockStatus.ON_HAND
        )
        
        if existing_stock:
            print("✅ Found existing stock level")
            print(f"   Quantity: {existing_stock.quantity}")
            print(f"   Unit cost: {existing_stock.unit_cost}")
            print(f"   Total cost: {existing_stock.total_cost}")
        else:
            print("   No existing stock level found")
            
    except Exception as e:
        print(f"❌ get_stock_level failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        return False
    
    try:
        # Test 2: Test update_stock_quantity method directly
        print(f"\n2️⃣ Testing update_stock_quantity...")
        
        updated_stock = await repository.update_stock_quantity(
            tenant_id=TENANT_ID,
            warehouse_id=WAREHOUSE_ID,
            variant_id=VARIANT_ID,
            stock_status=StockStatus.ON_HAND,
            quantity_change=Decimal('1.0'),  # Small test change
            unit_cost=Decimal('30.0')
        )
        
        print("✅ update_stock_quantity successful")
        print(f"   New quantity: {updated_stock.quantity}")
        print(f"   New unit cost: {updated_stock.unit_cost}")
        print(f"   New total cost: {updated_stock.total_cost}")
        
    except Exception as e:
        print(f"❌ update_stock_quantity failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error details: {str(e)}")
        
        # Try to get more details about the error
        if hasattr(e, 'orig'):
            print(f"   Original error: {e.orig}")
        if hasattr(e, 'statement'):
            print(f"   SQL statement: {e.statement}")
        if hasattr(e, 'params'):
            print(f"   Parameters: {e.params}")
            
        return False
    
    finally:
        # Clean up session
        try:
            await session.close()
            print("✅ Database session closed")
        except:
            pass
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_repository_layer())
    
    if success:
        print("\n✅ Repository layer is working correctly!")
    else:
        print("\n❌ Repository layer has issues!")