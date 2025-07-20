from typing import Optional, List, Dict, Any, TypeVar, Generic
from abc import ABC
from app.infrastucture.database.connection import get_supabase_client, db_connection

T = TypeVar('T')


class SupabaseRepository(ABC, Generic[T]):
    """Base Supabase repository class"""
    
    def __init__(self, table_name: str, entity_class: type):
        self.table_name = table_name
        self.entity_class = entity_class
    
    async def get_by_id(self, item_id: str) -> Optional[T]:
        """Get item by ID"""
        try:
            result = await db_connection.execute_query(
                lambda client: client.table(self.table_name)
                .select("*")
                .eq("id", item_id)
                .single()
                .execute()
            )
            
            if result.data:
                return self.entity_class(**result.data)
            return None
            
        except Exception as e:
            # Log error but don't raise for not found
            return None
    
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """Get all items with pagination"""
        try:
            result = await db_connection.execute_query(
                lambda client: client.table(self.table_name)
                .select("*")
                .range(offset, offset + limit - 1)
                .execute()
            )
            
            return [self.entity_class(**item) for item in result.data]
            
        except Exception as e:
            return []
    
    async def find_by(self, filters: Dict[str, Any], limit: int = 100) -> List[T]:
        """Find items by filters"""
        try:
            query = await db_connection.execute_query(
                lambda client: client.table(self.table_name).select("*")
            )
            
            # Apply filters
            for key, value in filters.items():
                query = await db_connection.execute_query(
                    lambda client: query.eq(key, value)
                )
            
            # Apply limit
            result = await db_connection.execute_query(
                lambda client: query.limit(limit).execute()
            )
            
            return [self.entity_class(**item) for item in result.data]
            
        except Exception as e:
            return []
    
    async def create(self, data: Dict[str, Any]) -> T:
        """Create a new item"""
        try:
            result = await db_connection.execute_query(
                lambda client: client.table(self.table_name)
                .insert(data)
                .execute()
            )
            
            if result.data:
                return self.entity_class(**result.data[0])
            raise Exception("Failed to create item")
            
        except Exception as e:
            raise Exception(f"Failed to create item: {str(e)}")
    
    async def update(self, item_id: str, data: Dict[str, Any]) -> Optional[T]:
        """Update an item"""
        try:
            result = await db_connection.execute_query(
                lambda client: client.table(self.table_name)
                .update(data)
                .eq("id", item_id)
                .execute()
            )
            
            if result.data:
                return self.entity_class(**result.data[0])
            return None
            
        except Exception as e:
            return None
    
    async def delete(self, item_id: str) -> bool:
        """Delete an item"""
        try:
            result = await db_connection.execute_query(
                lambda client: client.table(self.table_name)
                .delete()
                .eq("id", item_id)
                .execute()
            )
            
            return len(result.data) > 0
            
        except Exception as e:
            return False
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count items with optional filters"""
        try:
            query = await db_connection.execute_query(
                lambda client: client.table(self.table_name).select("*", count="exact")
            )
            
            if filters:
                for key, value in filters.items():
                    query = await db_connection.execute_query(
                        lambda client: query.eq(key, value)
                    )
            
            result = await db_connection.execute_query(
                lambda client: query.execute()
            )
            
            return result.count or 0
            
        except Exception as e:
            return 0 