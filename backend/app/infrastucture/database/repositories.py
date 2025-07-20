from typing import List, Optional, Any, Dict
from supabase import Client
from pydantic import BaseModel

from app.domain.repositories.base import BaseRepository
from app.infrastucture.database.connection import get_database
from app.infrastucture.logs.logger import default_logger


class SupabaseRepository(BaseRepository):
    """Supabase implementation of base repository"""
    
    def __init__(self, table_name: str, model_class: type[BaseModel]):
        super().__init__(table_name)
        self.model_class = model_class
        self._client: Optional[Client] = None
    
    def _get_client(self) -> Client:
        """Get Supabase client"""
        if not self._client:
            self._client = get_database()
        return self._client
    
    async def create(self, data: Dict[str, Any]) -> BaseModel:
        """Create a new record"""
        try:
            client = self._get_client()
            result = client.table(self.table_name).insert(data).execute()
            
            if result.data:
                default_logger.info(f"Created record in {self.table_name}", record_id=result.data[0].get('id'))
                return self.model_class(**result.data[0])
            else:
                raise ValueError("No data returned from insert operation")
                
        except Exception as e:
            default_logger.error(f"Failed to create record in {self.table_name}: {str(e)}")
            raise
    
    async def get_by_id(self, id: str) -> Optional[BaseModel]:
        """Get record by ID"""
        try:
            client = self._get_client()
            result = client.table(self.table_name).select("*").eq("id", id).execute()
            
            if result.data:
                return self.model_class(**result.data[0])
            return None
            
        except Exception as e:
            default_logger.error(f"Failed to get record by ID from {self.table_name}: {str(e)}")
            raise
    
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[BaseModel]:
        """Get all records with pagination"""
        try:
            client = self._get_client()
            result = client.table(self.table_name).select("*").range(offset, offset + limit - 1).execute()
            
            return [self.model_class(**item) for item in result.data]
            
        except Exception as e:
            default_logger.error(f"Failed to get records from {self.table_name}: {str(e)}")
            raise
    
    async def update(self, id: str, data: Dict[str, Any]) -> Optional[BaseModel]:
        """Update record by ID"""
        try:
            client = self._get_client()
            result = client.table(self.table_name).update(data).eq("id", id).execute()
            
            if result.data:
                default_logger.info(f"Updated record in {self.table_name}", record_id=id)
                return self.model_class(**result.data[0])
            return None
            
        except Exception as e:
            default_logger.error(f"Failed to update record in {self.table_name}: {str(e)}")
            raise
    
    async def delete(self, id: str) -> bool:
        """Delete record by ID"""
        try:
            client = self._get_client()
            result = client.table(self.table_name).delete().eq("id", id).execute()
            
            success = len(result.data) > 0
            if success:
                default_logger.info(f"Deleted record from {self.table_name}", record_id=id)
            else:
                default_logger.warning(f"No record found to delete in {self.table_name}", record_id=id)
            
            return success
            
        except Exception as e:
            default_logger.error(f"Failed to delete record from {self.table_name}: {str(e)}")
            raise
    
    async def find_by(self, filters: Dict[str, Any], limit: int = 100) -> List[BaseModel]:
        """Find records by filters"""
        try:
            client = self._get_client()
            query = client.table(self.table_name).select("*")
            
            # Apply filters
            for key, value in filters.items():
                query = query.eq(key, value)
            
            result = query.limit(limit).execute()
            
            return [self.model_class(**item) for item in result.data]
            
        except Exception as e:
            default_logger.error(f"Failed to find records in {self.table_name}: {str(e)}")
            raise
    
    async def execute_raw_query(self, query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute raw SQL query"""
        try:
            client = self._get_client()
            result = client.rpc('exec_sql', {'query': query, 'params': params or {}}).execute()
            
            return result.data
            
        except Exception as e:
            default_logger.error(f"Failed to execute raw query: {str(e)}")
            raise 