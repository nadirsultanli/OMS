import asyncio
import httpx
from typing import List, Dict, Any, Optional
from uuid import UUID
from decouple import config
from app.infrastucture.logs.logger import get_logger
from app.domain.entities.audit_events import AuditEvent, AuditActorType, AuditObjectType, AuditEventType

logger = get_logger("edge_audit_service")


class EdgeAuditService:
    """
    High-performance audit service using Supabase Edge Functions
    for fire-and-forget logging at >1k TPS
    """
    
    def __init__(self):
        self.supabase_url = config("SUPABASE_URL", default=None)
        self.anon_key = config("SUPABASE_ANON_KEY", default=None) or config("SUPABASE_KEY", default=None)
        
        if not self.supabase_url or not self.anon_key:
            logger.warning("Supabase configuration not found - Edge audit logging disabled")
            self.enabled = False
            return
            
        self.edge_function_url = f"{self.supabase_url}/functions/v1/audit-logger"
        self.headers = {
            'Authorization': f'Bearer {self.anon_key}',
            'Content-Type': 'application/json',
            'x-client-info': 'oms-backend/1.0.0'
        }
        self.enabled = True
        
        logger.info(f"Edge audit service initialized - URL: {self.edge_function_url}")
    
    async def log_events_fire_and_forget(
        self, 
        events: List[Dict[str, Any]], 
        timeout: float = 2.0
    ) -> bool:
        """
        Fire-and-forget audit logging for high-volume scenarios
        Returns immediately without waiting for response
        """
        if not self.enabled:
            logger.debug("Edge audit service disabled - skipping logging")
            return False
            
        if not events:
            return True
            
        try:
            # Create async task that doesn't block
            task = asyncio.create_task(
                self._send_events_async(events, timeout)
            )
            
            # Don't await the task - fire and forget
            logger.debug(f"Queued {len(events)} events for edge function logging")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to queue events for edge logging: {str(e)}")
            return False
    
    async def log_events_with_response(
        self, 
        events: List[Dict[str, Any]], 
        timeout: float = 10.0
    ) -> Dict[str, Any]:
        """
        Log events and wait for response (for non-critical path operations)
        """
        if not self.enabled:
            return {
                "success": False,
                "error": "Edge audit service not configured",
                "created_count": 0
            }
            
        if not events:
            return {
                "success": True,
                "created_count": 0,
                "message": "No events to log"
            }
        
        try:
            return await self._send_events_async(events, timeout)
        except Exception as e:
            logger.error(f"Edge function audit logging failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "created_count": 0
            }
    
    async def _send_events_async(
        self, 
        events: List[Dict[str, Any]], 
        timeout: float
    ) -> Dict[str, Any]:
        """Internal method to send events to edge function"""
        try:
            # Validate and prepare events
            prepared_events = []
            for event in events:
                prepared_event = self._prepare_event(event)
                if prepared_event:
                    prepared_events.append(prepared_event)
            
            if not prepared_events:
                return {
                    "success": False,
                    "error": "No valid events to send",
                    "created_count": 0
                }
            
            # Split into batches if too large (edge function limit: 1000)
            batches = [
                prepared_events[i:i + 1000] 
                for i in range(0, len(prepared_events), 1000)
            ]
            
            total_created = 0
            all_successful = True
            errors = []
            
            async with httpx.AsyncClient() as client:
                for batch in batches:
                    try:
                        response = await client.post(
                            self.edge_function_url,
                            json={'events': batch},
                            headers=self.headers,
                            timeout=timeout
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            total_created += result.get('created_count', 0)
                            logger.debug(f"Successfully logged {result.get('created_count', 0)} events via edge function")
                        else:
                            all_successful = False
                            error_msg = f"HTTP {response.status_code}: {response.text}"
                            errors.append(error_msg)
                            logger.warning(f"Edge function returned error: {error_msg}")
                            
                    except Exception as batch_error:
                        all_successful = False
                        error_msg = f"Batch error: {str(batch_error)}"
                        errors.append(error_msg)
                        logger.warning(f"Failed to send batch: {error_msg}")
            
            return {
                "success": all_successful,
                "created_count": total_created,
                "total_events": len(prepared_events),
                "batch_count": len(batches),
                "errors": errors if errors else None,
                "message": f"Processed {len(batches)} batches, created {total_created} events"
            }
            
        except Exception as e:
            logger.error(f"Edge function communication error: {str(e)}")
            raise
    
    def _prepare_event(self, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Prepare and validate event data for edge function"""
        try:
            # Required fields
            if not event_data.get('tenant_id'):
                logger.warning("Skipping event without tenant_id")
                return None
                
            prepared = {
                'tenant_id': str(event_data['tenant_id']),
                'actor_type': event_data.get('actor_type', 'SYSTEM'),
                'object_type': event_data.get('object_type', 'OTHER'),
                'event_type': event_data.get('event_type', 'OTHER')
            }
            
            # Optional fields
            optional_fields = [
                'actor_id', 'object_id', 'field_name', 
                'old_value', 'new_value', 'ip_address', 
                'device_id', 'session_id'
            ]
            
            for field in optional_fields:
                if event_data.get(field) is not None:
                    prepared[field] = str(event_data[field])
            
            # Context as dict
            if event_data.get('context'):
                prepared['context'] = event_data['context']
            
            return prepared
            
        except Exception as e:
            logger.warning(f"Failed to prepare event: {str(e)}")
            return None
    
    async def log_audit_event_async(
        self,
        tenant_id: UUID,
        actor_id: Optional[UUID],
        actor_type: AuditActorType,
        object_type: AuditObjectType,
        object_id: Optional[UUID],
        event_type: AuditEventType,
        field_name: Optional[str] = None,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        device_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> bool:
        """
        Convenience method to log a single audit event asynchronously
        """
        event_data = {
            'tenant_id': tenant_id,
            'actor_id': actor_id,
            'actor_type': actor_type.value if isinstance(actor_type, AuditActorType) else actor_type,
            'object_type': object_type.value if isinstance(object_type, AuditObjectType) else object_type,
            'object_id': object_id,
            'event_type': event_type.value if isinstance(event_type, AuditEventType) else event_type,
            'field_name': field_name,
            'old_value': old_value,
            'new_value': new_value,
            'context': context,
            'ip_address': ip_address,
            'device_id': device_id,
            'session_id': session_id
        }
        
        return await self.log_events_fire_and_forget([event_data])
    
    def is_enabled(self) -> bool:
        """Check if edge audit service is properly configured"""
        return self.enabled


# Global instance
edge_audit_service = EdgeAuditService()