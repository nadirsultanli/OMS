#!/usr/bin/env python3
"""
Improved script to update variants table with accurate weight and volume data
Based on actual cylinder sizes and capacity data
"""
import asyncio
import asyncpg
from decimal import Decimal
from decouple import config
import sys
import os
import re

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def get_database_connection():
    """Get direct PostgreSQL connection"""
    database_url = config("DATABASE_URL")
    # Convert asyncpg URL format
    if database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    
    return await asyncpg.connect(database_url)

def extract_cylinder_size(product_name, sku, capacity_kg):
    """Extract cylinder size from product name, SKU, or capacity"""
    
    # First try to extract from SKU (most reliable)
    sku_match = re.search(r'CYL(\d+)', sku.upper())
    if sku_match:
        return int(sku_match.group(1))
    
    # Try to extract from product name
    name_match = re.search(r'(\d+)kg', product_name.lower())
    if name_match:
        return int(name_match.group(1))
    
    # Fallback to capacity (if available)
    if capacity_kg:
        return int(float(capacity_kg))
    
    return None

def calculate_cylinder_properties(size_kg, state_attr):
    """Calculate realistic weight and volume for LPG cylinders"""
    
    # Standard tare weights for common cylinder sizes
    tare_weights = {
        4: 4.2,    # 4kg cylinder
        6: 5.8,    # 6kg cylinder
        9: 6.5,    # 9kg cylinder
        12: 7.8,   # 12kg cylinder
        13: 8.2,   # 13kg cylinder
        15: 9.5,   # 15kg cylinder
        18: 11.0,  # 18kg cylinder
        19: 11.5,  # 19kg cylinder
        20: 12.5,  # 20kg cylinder
        25: 15.0,  # 25kg cylinder
        30: 18.0,  # 30kg cylinder
        35: 21.0,  # 35kg cylinder
        50: 30.0,  # 50kg cylinder (industrial)
    }
    
    # Standard volumes for cylinders (approximate)
    volumes = {
        4: 0.012,   # 12 liters
        6: 0.018,   # 18 liters
        9: 0.027,   # 27 liters
        12: 0.036,  # 36 liters
        13: 0.039,  # 39 liters
        15: 0.045,  # 45 liters
        18: 0.054,  # 54 liters
        19: 0.057,  # 57 liters
        20: 0.060,  # 60 liters
        25: 0.075,  # 75 liters
        30: 0.090,  # 90 liters
        35: 0.105,  # 105 liters
        50: 0.150,  # 150 liters
    }
    
    # Get tare weight (closest size)
    tare_weight = tare_weights.get(size_kg)
    if not tare_weight:
        # Estimate based on size
        tare_weight = max(4.0, size_kg * 0.65)  # Rough estimate
    
    # Get volume (closest size)
    volume = volumes.get(size_kg)
    if not volume:
        # Estimate based on size (rough calculation)
        volume = size_kg * 0.003  # Approximate conversion
    
    # Calculate weight based on state
    if state_attr == 'EMPTY':
        unit_weight = tare_weight
    else:  # FULL or other states
        unit_weight = tare_weight + size_kg
    
    return Decimal(str(round(unit_weight, 1))), Decimal(str(round(volume, 3)))

async def update_variants_improved():
    """Update variants with improved weight and volume calculations"""
    conn = await get_database_connection()
    
    try:
        print("=== IMPROVED VARIANTS WEIGHT/VOLUME UPDATE ===")
        
        # Get all variants with product information
        query = """
        SELECT 
            v.id,
            v.sku,
            v.sku_type,
            v.state_attr,
            v.requires_exchange,
            v.tare_weight_kg,
            v.capacity_kg,
            v.gross_weight_kg,
            p.name as product_name,
            p.category,
            v.unit_weight_kg as current_weight,
            v.unit_volume_m3 as current_volume
        FROM variants v
        JOIN products p ON v.product_id = p.id
        WHERE v.deleted_at IS NULL
        ORDER BY p.name, v.sku;
        """
        
        variants = await conn.fetch(query)
        print(f"Found {len(variants)} variants to analyze")
        
        updates = []
        
        for variant in variants:
            product_name = variant['product_name']
            sku = variant['sku']
            sku_type = variant['sku_type']
            state_attr = variant['state_attr']
            capacity_kg = variant['capacity_kg']
            
            print(f"\nAnalyzing: {product_name} - {sku}")
            print(f"  SKU Type: {sku_type}, State: {state_attr}, Capacity: {capacity_kg}")
            
            unit_weight_kg = None
            unit_volume_m3 = None
            
            # Handle different SKU types
            if sku_type == 'ASSET' and 'CYL' in sku.upper():
                # This is a cylinder asset
                cylinder_size = extract_cylinder_size(product_name, sku, capacity_kg)
                
                if cylinder_size:
                    unit_weight_kg, unit_volume_m3 = calculate_cylinder_properties(cylinder_size, state_attr)
                    print(f"  → Cylinder size: {cylinder_size}kg, Weight: {unit_weight_kg}kg, Volume: {unit_volume_m3}m³")
                else:
                    # Fallback for unknown cylinder
                    if state_attr == 'EMPTY':
                        unit_weight_kg = Decimal('8.0')
                    else:
                        unit_weight_kg = Decimal('20.0')
                    unit_volume_m3 = Decimal('0.045')
                    print(f"  → Unknown cylinder size, using defaults: {unit_weight_kg}kg, {unit_volume_m3}m³")
                    
            elif sku_type == 'CONSUMABLE':
                # Gas content - no physical weight/volume for the SKU itself
                unit_weight_kg = Decimal('0.0')  # The gas weight is tracked separately
                unit_volume_m3 = Decimal('0.0')  # No physical volume for the consumable SKU
                print(f"  → Consumable gas: {unit_weight_kg}kg, {unit_volume_m3}m³")
                
            elif sku_type == 'DEPOSIT':
                # Deposit - no physical properties
                unit_weight_kg = Decimal('0.0')
                unit_volume_m3 = Decimal('0.0')
                print(f"  → Deposit: {unit_weight_kg}kg, {unit_volume_m3}m³")
                
            elif sku_type == 'BUNDLE':
                # Bundle - weight/volume would be sum of components
                # For now, estimate based on the cylinder it contains
                if 'KIT' in sku.upper():
                    kit_match = re.search(r'KIT(\d+)', sku.upper())
                    if kit_match:
                        cylinder_size = int(kit_match.group(1))
                        # Bundle includes full cylinder + accessories
                        cyl_weight, cyl_volume = calculate_cylinder_properties(cylinder_size, 'FULL')
                        unit_weight_kg = cyl_weight + Decimal('0.5')  # Add small weight for accessories
                        unit_volume_m3 = cyl_volume + Decimal('0.005')  # Add small volume for packaging
                        print(f"  → Bundle with {cylinder_size}kg cylinder: {unit_weight_kg}kg, {unit_volume_m3}m³")
                    else:
                        unit_weight_kg = Decimal('15.0')  # Default bundle weight
                        unit_volume_m3 = Decimal('0.050')  # Default bundle volume
                        print(f"  → Unknown bundle, using defaults: {unit_weight_kg}kg, {unit_volume_m3}m³")
                else:
                    unit_weight_kg = Decimal('15.0')
                    unit_volume_m3 = Decimal('0.050')
                    print(f"  → Generic bundle: {unit_weight_kg}kg, {unit_volume_m3}m³")
                    
            else:
                # Other/unknown types
                unit_weight_kg = Decimal('1.0')
                unit_volume_m3 = Decimal('0.001')
                print(f"  → Unknown type, using minimal defaults: {unit_weight_kg}kg, {unit_volume_m3}m³")
            
            if unit_weight_kg is not None and unit_volume_m3 is not None:
                updates.append({
                    'id': variant['id'],
                    'product_name': product_name,
                    'sku': sku,
                    'unit_weight_kg': unit_weight_kg,
                    'unit_volume_m3': unit_volume_m3,
                    'current_weight': variant['current_weight'],
                    'current_volume': variant['current_volume']
                })
        
        # Apply updates
        print(f"\n=== APPLYING UPDATES TO {len(updates)} VARIANTS ===")
        for update in updates:
            await conn.execute("""
                UPDATE variants 
                SET unit_weight_kg = $1, unit_volume_m3 = $2
                WHERE id = $3
            """, update['unit_weight_kg'], update['unit_volume_m3'], update['id'])
            
            current_weight = update['current_weight'] or 'None'
            current_volume = update['current_volume'] or 'None'
            
            print(f"✓ {update['product_name'][:30]:<30} - {update['sku']:<15}: "
                  f"{current_weight} → {update['unit_weight_kg']}kg, "
                  f"{current_volume} → {update['unit_volume_m3']}m³")
        
        print(f"\n✅ Successfully updated {len(updates)} variants with improved calculations!")
        
        # Final verification
        verification_query = """
        SELECT 
            COUNT(*) as total,
            AVG(unit_weight_kg) as avg_weight,
            AVG(unit_volume_m3) as avg_volume,
            MIN(unit_weight_kg) as min_weight,
            MAX(unit_weight_kg) as max_weight
        FROM variants 
        WHERE deleted_at IS NULL AND unit_weight_kg IS NOT NULL;
        """
        
        stats = await conn.fetchrow(verification_query)
        print(f"\n=== FINAL STATISTICS ===")
        print(f"Total updated variants: {stats['total']}")
        print(f"Weight range: {float(stats['min_weight']):.1f} - {float(stats['max_weight']):.1f} kg")
        print(f"Average weight: {float(stats['avg_weight']):.2f} kg")
        print(f"Average volume: {float(stats['avg_volume']):.4f} m³")
        
    finally:
        await conn.close()

async def main():
    """Main function"""
    try:
        await update_variants_improved()
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())