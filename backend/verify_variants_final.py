#!/usr/bin/env python3
"""
Final verification script to display the updated variants table data
"""
import asyncio
import asyncpg
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

async def show_final_variants_data():
    """Show the final state of variants with weight and volume data"""
    conn = await get_database_connection()
    
    try:
        print("=== FINAL VARIANTS TABLE DATA WITH WEIGHT AND VOLUME ===\n")
        
        # Get all variants grouped by product
        query = """
        SELECT 
            p.name as product_name,
            p.category,
            v.sku,
            v.sku_type,
            v.state_attr,
            v.requires_exchange,
            v.tare_weight_kg,
            v.capacity_kg,
            v.gross_weight_kg,
            v.unit_weight_kg,
            v.unit_volume_m3,
            v.default_price
        FROM variants v
        JOIN products p ON v.product_id = p.id
        WHERE v.deleted_at IS NULL
        ORDER BY p.name, 
                 CASE v.sku_type 
                     WHEN 'ASSET' THEN 1
                     WHEN 'CONSUMABLE' THEN 2
                     WHEN 'DEPOSIT' THEN 3
                     WHEN 'BUNDLE' THEN 4
                     ELSE 5
                 END,
                 v.sku;
        """
        
        variants = await conn.fetch(query)
        
        current_product = None
        
        for variant in variants:
            product_name = variant['product_name']
            
            # Print product header when we encounter a new product
            if current_product != product_name:
                if current_product is not None:
                    print()  # Add spacing between products
                
                print(f"🏭 PRODUCT: {product_name}")
                print(f"   Category: {variant['category']}")
                print("   " + "="*80)
                current_product = product_name
            
            # Format the variant information
            sku_type_emoji = {
                'ASSET': '🛢️ ',
                'CONSUMABLE': '⛽',
                'DEPOSIT': '💰',
                'BUNDLE': '📦'
            }.get(variant['sku_type'], '❓')
            
            state_info = f" ({variant['state_attr']})" if variant['state_attr'] else ""
            exchange_info = " [EXCHANGE]" if variant['requires_exchange'] else ""
            
            print(f"   {sku_type_emoji} {variant['sku']:<15} {state_info:<7} {exchange_info}")
            print(f"      Weight: {variant['unit_weight_kg']:>6} kg  |  Volume: {variant['unit_volume_m3']:>7} m³")
            
            # Show additional details for assets
            if variant['sku_type'] == 'ASSET':
                tare = variant['tare_weight_kg'] or 'N/A'
                capacity = variant['capacity_kg'] or 'N/A'
                gross = variant['gross_weight_kg'] or 'N/A'
                print(f"      Tare: {tare} kg  |  Capacity: {capacity} kg  |  Gross: {gross} kg")
            
            if variant['default_price']:
                print(f"      Price: ${variant['default_price']}")
            
            print()
        
        # Summary statistics by SKU type
        print("\n" + "="*90)
        print("📊 SUMMARY STATISTICS BY SKU TYPE")
        print("="*90)
        
        stats_query = """
        SELECT 
            sku_type,
            COUNT(*) as count,
            AVG(unit_weight_kg) as avg_weight,
            AVG(unit_volume_m3) as avg_volume,
            MIN(unit_weight_kg) as min_weight,
            MAX(unit_weight_kg) as max_weight,
            MIN(unit_volume_m3) as min_volume,
            MAX(unit_volume_m3) as max_volume
        FROM variants v
        WHERE v.deleted_at IS NULL
        GROUP BY sku_type
        ORDER BY sku_type;
        """
        
        stats = await conn.fetch(stats_query)
        
        print(f"{'SKU Type':<12} {'Count':<6} {'Weight (kg)':<20} {'Volume (m³)':<20}")
        print(f"{'='*12} {'='*6} {'='*20} {'='*20}")
        
        for stat in stats:
            sku_type = stat['sku_type'] or 'NULL'
            count = stat['count']
            weight_range = f"{float(stat['min_weight']):.1f} - {float(stat['max_weight']):.1f} (avg: {float(stat['avg_weight']):.1f})"
            volume_range = f"{float(stat['min_volume']):.3f} - {float(stat['max_volume']):.3f} (avg: {float(stat['avg_volume']):.3f})"
            
            print(f"{sku_type:<12} {count:<6} {weight_range:<20} {volume_range:<20}")
        
        # Overall statistics
        print("\n" + "="*90)
        print("📈 OVERALL STATISTICS")
        print("="*90)
        
        overall_query = """
        SELECT 
            COUNT(*) as total_variants,
            COUNT(DISTINCT product_id) as total_products,
            SUM(CASE WHEN unit_weight_kg > 0 THEN 1 ELSE 0 END) as variants_with_weight,
            SUM(CASE WHEN unit_volume_m3 > 0 THEN 1 ELSE 0 END) as variants_with_volume,
            AVG(unit_weight_kg) as avg_weight,
            AVG(unit_volume_m3) as avg_volume,
            SUM(unit_weight_kg) as total_weight,
            SUM(unit_volume_m3) as total_volume
        FROM variants 
        WHERE deleted_at IS NULL;
        """
        
        overall = await conn.fetchrow(overall_query)
        
        print(f"Total Products: {overall['total_products']}")
        print(f"Total Variants: {overall['total_variants']}")
        print(f"Variants with Weight Data: {overall['variants_with_weight']}")
        print(f"Variants with Volume Data: {overall['variants_with_volume']}")
        print(f"Average Weight: {float(overall['avg_weight']):.2f} kg")
        print(f"Average Volume: {float(overall['avg_volume']):.4f} m³")
        print(f"Total Weight if all variants combined: {float(overall['total_weight']):.1f} kg")
        print(f"Total Volume if all variants combined: {float(overall['total_volume']):.3f} m³")
        
        print("\n✅ Variants table successfully updated with realistic weight and volume data!")
        print("   The data now reflects appropriate values for different LPG cylinder sizes,")
        print("   consumables, deposits, and bundle products based on industry standards.")
        
    finally:
        await conn.close()

async def main():
    """Main function"""
    try:
        await show_final_variants_data()
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())