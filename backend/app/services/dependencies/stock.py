from fastapi import Depends
from app.services.stock_levels.stock_level_service import StockLevelService
from app.services.dependencies.stock_levels import get_stock_level_service

# For now, we'll use the existing stock level service as the stock service
# In a more complex implementation, you might have a separate StockService
# that coordinates between stock levels, movements, and other stock-related operations

def get_stock_service(
    stock_level_service: StockLevelService = Depends(get_stock_level_service)
) -> StockLevelService:
    """Get the stock service (currently using stock level service)"""
    return stock_level_service