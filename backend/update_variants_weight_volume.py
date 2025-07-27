#!/usr/bin/env python3
"""
Script to examine and update variants table with weight and volume data
"""
import asyncio
import asyncpg
from decimal import Decimal
from decouple import config
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def get_database_connection():
    """Get direct PostgreSQL connection"""
    database_url = config("DATABASE_URL")
    # Convert asyncpg URL format
    if database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    
    return await asyncpg.connect(database_url)

async def examine_variants_table():
    """Examine the current variants table structure and data"""
    conn = await get_database_connection()
    
    try:
        print("=== EXAMINING VARIANTS TABLE STRUCTURE ===")
        
        # Get table schema
        columns_query = """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_name = 'variants' 
        ORDER BY ordinal_position;
        """
        
        columns = await conn.fetch(columns_query)
        print("\nTable Columns:")
        for col in columns:
            print(f"  {col['column_name']}: {col['data_type']} ({'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'})")
        
        # Check if weight and volume columns exist
        weight_col_exists = any(col['column_name'] == 'unit_weight_kg' for col in columns)
        volume_col_exists = any(col['column_name'] == 'unit_volume_m3' for col in columns)
        
        print(f"\nunit_weight_kg column exists: {weight_col_exists}")
        print(f"unit_volume_m3 column exists: {volume_col_exists}")
        
        # First check products table structure
        products_columns_query = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'products' 
        ORDER BY ordinal_position;
        """
        
        products_columns = await conn.fetch(products_columns_query)
        print("\nProducts table columns:")
        for col in products_columns:
            print(f"  {col['column_name']}")
        
        # Build query based on available columns
        base_query = """
        SELECT 
            v.id,
            v.sku,
            v.sku_type,
            v.state_attr,
            v.requires_exchange,
            v.tare_weight_kg,
            v.capacity_kg,
            v.gross_weight_kg,
            p.name as product_name
        """
        
        if weight_col_exists:
            base_query += ", v.unit_weight_kg"
        else:
            base_query += ", NULL as unit_weight_kg"
            
        if volume_col_exists:
            base_query += ", v.unit_volume_m3"
        else:
            base_query += ", NULL as unit_volume_m3"
            
        variants_query = base_query + """
        FROM variants v
        JOIN products p ON v.product_id = p.id
        WHERE v.deleted_at IS NULL
        ORDER BY p.name, v.sku;
        """
        
        variants = await conn.fetch(variants_query)
        
        print(f"\n=== CURRENT VARIANTS DATA ({len(variants)} records) ===")
        for variant in variants:
            print(f"\nProduct: {variant['product_name']}")
            print(f"  SKU: {variant['sku']}")
            print(f"  SKU Type: {variant['sku_type']}")
            print(f"  State: {variant['state_attr']}")
            print(f"  Requires Exchange: {variant['requires_exchange']}")
            print(f"  Tare Weight: {variant['tare_weight_kg']} kg")
            print(f"  Capacity: {variant['capacity_kg']} kg")
            print(f"  Gross Weight: {variant['gross_weight_kg']} kg")
            if weight_col_exists:
                print(f"  Unit Weight: {variant['unit_weight_kg']} kg")
            if volume_col_exists:
                print(f"  Unit Volume: {variant['unit_volume_m3']} m³")
        
        return variants, weight_col_exists, volume_col_exists
        
    finally:
        await conn.close()

async def add_weight_volume_columns():
    """Add unit_weight_kg and unit_volume_m3 columns if they don't exist"""
    conn = await get_database_connection()
    
    try:
        print("\n=== ADDING WEIGHT AND VOLUME COLUMNS ===")
        
        # Add unit_weight_kg column
        await conn.execute("""
            ALTER TABLE variants 
            ADD COLUMN IF NOT EXISTS unit_weight_kg NUMERIC;
        """)
        print("✓ Added unit_weight_kg column")
        
        # Add unit_volume_m3 column
        await conn.execute("""
            ALTER TABLE variants 
            ADD COLUMN IF NOT EXISTS unit_volume_m3 NUMERIC;
        """)
        print("✓ Added unit_volume_m3 column")
        
    finally:
        await conn.close()

async def update_variant_weights_volumes(variants):
    """Update variants with realistic weight and volume data based on their names/types"""
    conn = await get_database_connection()
    
    try:
        print("\n=== UPDATING WEIGHT AND VOLUME DATA ===")
        
        updates = []
        
        for variant in variants:
            product_name = variant['product_name'].lower()
            sku = variant['sku'].lower()
            sku_type = variant['sku_type']
            state_attr = variant['state_attr']
            requires_exchange = variant['requires_exchange']
            
            # Determine weight and volume based on product type and variant characteristics
            unit_weight_kg = None
            unit_volume_m3 = None
            
            # LPG Cylinder logic
            if any(keyword in product_name for keyword in ['lpg', 'gas', 'cylinder', 'propane', 'butane']):
                # Determine size from product name or SKU
                if any(size in product_name or size in sku for size in ['6kg', '6 kg']):
                    # 6kg cylinder
                    if state_attr == 'EMPTY' or 'empty' in sku:
                        unit_weight_kg = Decimal('9.5')  # Empty 6kg cylinder
                    else:
                        unit_weight_kg = Decimal('15.5')  # Full 6kg cylinder (9.5 + 6)
                    unit_volume_m3 = Decimal('0.025')  # ~25 liters
                    
                elif any(size in product_name or size in sku for size in ['9kg', '9 kg']):
                    # 9kg cylinder
                    if state_attr == 'EMPTY' or 'empty' in sku:
                        unit_weight_kg = Decimal('10.5')  # Empty 9kg cylinder
                    else:
                        unit_weight_kg = Decimal('19.5')  # Full 9kg cylinder (10.5 + 9)
                    unit_volume_m3 = Decimal('0.035')  # ~35 liters
                    
                elif any(size in product_name or size in sku for size in ['12kg', '12 kg']):
                    # 12kg cylinder
                    if state_attr == 'EMPTY' or 'empty' in sku:
                        unit_weight_kg = Decimal('12.0')  # Empty 12kg cylinder
                    else:
                        unit_weight_kg = Decimal('24.0')  # Full 12kg cylinder (12 + 12)
                    unit_volume_m3 = Decimal('0.045')  # ~45 liters
                    
                elif any(size in product_name or size in sku for size in ['15kg', '15 kg']):
                    # 15kg cylinder
                    if state_attr == 'EMPTY' or 'empty' in sku:
                        unit_weight_kg = Decimal('13.5')  # Empty 15kg cylinder
                    else:
                        unit_weight_kg = Decimal('28.5')  # Full 15kg cylinder (13.5 + 15)
                    unit_volume_m3 = Decimal('0.055')  # ~55 liters
                    
                elif any(size in product_name or size in sku for size in ['20kg', '20 kg']):
                    # 20kg cylinder
                    if state_attr == 'EMPTY' or 'empty' in sku:
                        unit_weight_kg = Decimal('15.0')  # Empty 20kg cylinder
                    else:
                        unit_weight_kg = Decimal('35.0')  # Full 20kg cylinder (15 + 20)
                    unit_volume_m3 = Decimal('0.065')  # ~65 liters
                    
                else:
                    # Default medium cylinder (assume 12kg)
                    if state_attr == 'EMPTY' or 'empty' in sku:
                        unit_weight_kg = Decimal('12.0')  # Empty cylinder
                    else:
                        unit_weight_kg = Decimal('24.0')  # Full cylinder
                    unit_volume_m3 = Decimal('0.045')  # ~45 liters
            
            # Other product types (accessories, valves, etc.)
            elif any(keyword in product_name for keyword in ['valve', 'regulator']):
                unit_weight_kg = Decimal('0.5')  # Light accessories
                unit_volume_m3 = Decimal('0.001')  # Very small volume
                
            elif any(keyword in product_name for keyword in ['hose', 'pipe']):
                unit_weight_kg = Decimal('1.0')  # Medium weight accessories
                unit_volume_m3 = Decimal('0.005')  # Small volume
                
            elif any(keyword in product_name for keyword in ['adapter', 'fitting']):
                unit_weight_kg = Decimal('0.2')  # Very light accessories
                unit_volume_m3 = Decimal('0.0005')  # Tiny volume
                
            else:
                # Unknown product type - use defaults
                unit_weight_kg = Decimal('5.0')  # Default weight
                unit_volume_m3 = Decimal('0.01')  # Default volume
            
            if unit_weight_kg is not None and unit_volume_m3 is not None:
                updates.append({
                    'id': variant['id'],
                    'product_name': variant['product_name'],
                    'sku': variant['sku'],
                    'unit_weight_kg': unit_weight_kg,
                    'unit_volume_m3': unit_volume_m3
                })
        
        # Execute updates
        for update in updates:
            await conn.execute("""
                UPDATE variants 
                SET unit_weight_kg = $1, unit_volume_m3 = $2
                WHERE id = $3
            """, update['unit_weight_kg'], update['unit_volume_m3'], update['id'])
            
            print(f"✓ Updated {update['product_name']} - {update['sku']}: "
                  f"{update['unit_weight_kg']}kg, {update['unit_volume_m3']}m³")
        
        print(f"\n✓ Successfully updated {len(updates)} variants")
        
    finally:
        await conn.close()

async def verify_updates():
    """Verify the updates were applied correctly"""
    conn = await get_database_connection()
    
    try:
        print("\n=== VERIFICATION OF UPDATES ===")
        
        verification_query = """
        SELECT 
            p.name as product_name,
            v.sku,
            v.unit_weight_kg,
            v.unit_volume_m3,
            v.state_attr
        FROM variants v
        JOIN products p ON v.product_id = p.id
        WHERE v.deleted_at IS NULL
        AND (v.unit_weight_kg IS NOT NULL OR v.unit_volume_m3 IS NOT NULL)
        ORDER BY p.name, v.sku;
        """
        
        results = await conn.fetch(verification_query)
        
        print(f"\nUpdated variants ({len(results)} records):")
        for result in results:
            print(f"  {result['product_name']} - {result['sku']} ({result['state_attr']}): "
                  f"{result['unit_weight_kg']}kg, {result['unit_volume_m3']}m³")
        
        # Summary statistics
        stats_query = """
        SELECT 
            COUNT(*) as total_variants,
            COUNT(unit_weight_kg) as variants_with_weight,
            COUNT(unit_volume_m3) as variants_with_volume,
            AVG(unit_weight_kg) as avg_weight,
            AVG(unit_volume_m3) as avg_volume
        FROM variants 
        WHERE deleted_at IS NULL;
        """
        
        stats = await conn.fetchrow(stats_query)
        
        print(f"\n=== SUMMARY STATISTICS ===")
        print(f"Total variants: {stats['total_variants']}")
        print(f"Variants with weight data: {stats['variants_with_weight']}")
        print(f"Variants with volume data: {stats['variants_with_volume']}")
        print(f"Average weight: {stats['avg_weight']:.2f} kg")
        print(f"Average volume: {stats['avg_volume']:.4f} m³")
        
    finally:
        await conn.close()

async def main():
    """Main function to examine and update variants table"""
    try:
        print("Starting variants weight/volume update process...")
        
        # Step 1: Examine current table structure and data
        variants, weight_col_exists, volume_col_exists = await examine_variants_table()
        
        # Step 2: Add columns if they don't exist
        if not weight_col_exists or not volume_col_exists:
            await add_weight_volume_columns()
        
        # Step 3: Update weight and volume data
        if variants:
            await update_variant_weights_volumes(variants)
        else:
            print("No variants found to update")
        
        # Step 4: Verify updates
        await verify_updates()
        
        print("\n✅ Variants weight/volume update process completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during update process: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())