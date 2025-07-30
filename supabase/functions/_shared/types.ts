/**
 * Shared type definitions for Edge Functions
 */

export type AuditActorType = 'USER' | 'SYSTEM' | 'API' | 'SCHEDULER'

export type AuditObjectType = 
  | 'USER' 
  | 'CUSTOMER' 
  | 'ORDER' 
  | 'PRODUCT' 
  | 'VARIANT' 
  | 'WAREHOUSE' 
  | 'TRIP' 
  | 'VEHICLE' 
  | 'STOCK_LEVEL' 
  | 'PRICE_LIST' 
  | 'STOCK_DOC' 
  | 'OTHER'

export type AuditEventType = 
  | 'CREATE' 
  | 'UPDATE' 
  | 'DELETE' 
  | 'LOGIN' 
  | 'LOGOUT' 
  | 'STATUS_CHANGE' 
  | 'FIELD_CHANGE' 
  | 'BUSINESS_EVENT' 
  | 'SECURITY_EVENT' 
  | 'OTHER'

export interface AuditEvent {
  tenant_id: string
  actor_id?: string | null
  actor_type: AuditActorType
  object_type: AuditObjectType
  object_id?: string | null
  event_type: AuditEventType
  field_name?: string | null
  old_value?: string | null
  new_value?: string | null
  context?: Record<string, any> | null
  ip_address?: string | null
  device_id?: string | null
  session_id?: string | null
}

export interface BulkAuditRequest {
  events: AuditEvent[]
}

export interface AuditResponse {
  success: boolean
  created_count?: number
  failed_count?: number
  message: string
  timestamp: string
  errors?: string[]
  created_event_ids?: number[]
  performance?: {
    batch_size: number
    processing_time_ms: number
  }
}

export interface ErrorResponse {
  success: false
  error: string
  message?: string
  code?: string
  details?: any
}