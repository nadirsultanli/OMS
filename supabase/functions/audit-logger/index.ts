import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type, x-tenant-id',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
}

interface AuditEvent {
  tenant_id: string
  actor_id?: string
  actor_type: 'USER' | 'SYSTEM' | 'API' | 'SCHEDULER'
  object_type: 'USER' | 'CUSTOMER' | 'ORDER' | 'PRODUCT' | 'VARIANT' | 'WAREHOUSE' | 'TRIP' | 'VEHICLE' | 'STOCK_LEVEL' | 'PRICE_LIST' | 'STOCK_DOC' | 'OTHER'
  object_id?: string
  event_type: 'CREATE' | 'UPDATE' | 'DELETE' | 'LOGIN' | 'LOGOUT' | 'STATUS_CHANGE' | 'FIELD_CHANGE' | 'BUSINESS_EVENT' | 'SECURITY_EVENT' | 'OTHER'
  field_name?: string
  old_value?: string
  new_value?: string
  context?: Record<string, any>
  ip_address?: string
  device_id?: string
  session_id?: string
}

interface BulkAuditRequest {
  events: AuditEvent[]
}

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  // Only allow POST requests
  if (req.method !== 'POST') {
    return new Response(
      JSON.stringify({ error: 'Method not allowed' }),
      { 
        status: 405, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    )
  }

  try {
    // Get request data
    const requestData: BulkAuditRequest = await req.json()
    
    // Validate request
    if (!requestData.events || !Array.isArray(requestData.events)) {
      return new Response(
        JSON.stringify({ 
          error: 'Invalid request format', 
          message: 'events array is required' 
        }),
        { 
          status: 400, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // Limit batch size for performance (up to 1000 events per request)
    if (requestData.events.length > 1000) {
      return new Response(
        JSON.stringify({ 
          error: 'Batch too large', 
          message: 'Maximum 1000 events per request' 
        }),
        { 
          status: 400, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // Initialize Supabase client with service role key for direct database access
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    
    const supabase = createClient(supabaseUrl, supabaseServiceKey, {
      auth: {
        autoRefreshToken: false,
        persistSession: false
      }
    })

    // Prepare audit events for insertion
    const auditEvents = requestData.events.map(event => ({
      tenant_id: event.tenant_id,
      event_time: new Date().toISOString(),
      actor_id: event.actor_id || null,
      actor_type: event.actor_type,
      object_type: event.object_type,
      object_id: event.object_id || null,
      event_type: event.event_type,
      field_name: event.field_name || null,
      old_value: event.old_value ? JSON.stringify({ field: event.old_value }) : null,
      new_value: event.new_value ? JSON.stringify({ field: event.new_value }) : null,
      ip_address: event.ip_address || null,
      device_id: event.device_id || null,
      context: event.context ? JSON.stringify({
        session_id: event.session_id,
        ...event.context
      }) : null,
      deleted_at: null,
      deleted_by: null
    }))

    // Perform bulk insert with optimized performance
    const { data, error } = await supabase
      .from('audit_events')
      .insert(auditEvents)
      .select('id')

    if (error) {
      console.error('Database insert error:', error)
      
      // Return detailed error for debugging
      return new Response(
        JSON.stringify({ 
          success: false,
          error: 'Database insert failed',
          details: error.message,
          code: error.code
        }),
        { 
          status: 500, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      )
    }

    // Success response with performance metrics
    const responseData = {
      success: true,
      created_count: data?.length || requestData.events.length,
      message: `Successfully logged ${data?.length || requestData.events.length} audit events`,
      timestamp: new Date().toISOString(),
      performance: {
        batch_size: requestData.events.length,
        processing_time_ms: Date.now() - performance.now()
      }
    }

    // Add created IDs if available
    if (data && data.length > 0) {
      responseData.created_event_ids = data.map(item => item.id)
    }

    return new Response(
      JSON.stringify(responseData),
      { 
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    )

  } catch (parseError) {
    console.error('Request parsing error:', parseError)
    
    return new Response(
      JSON.stringify({ 
        success: false,
        error: 'Invalid JSON payload',
        message: parseError.message 
      }),
      { 
        status: 400, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    )
  }
})

/* Edge Function Usage Examples:

1. High-Volume Fire-and-Forget Logging:
POST /functions/v1/audit-logger
{
  "events": [
    {
      "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
      "actor_id": "user-123",
      "actor_type": "USER",
      "object_type": "ORDER",
      "object_id": "order-456",
      "event_type": "CREATE",
      "context": { "order_total": 150.00 },
      "ip_address": "192.168.1.1",
      "device_id": "Mozilla/5.0..."
    }
  ]
}

2. Batch Processing (up to 1000 events):
POST /functions/v1/audit-logger
{
  "events": [
    // ... up to 1000 audit events
  ]
}

Performance Benefits:
- Direct database access (no API overhead)
- Optimized batch inserts (up to 1000 events)
- Fire-and-forget pattern (no waiting for response)
- Automatic scaling with Supabase Edge Runtime
- Global edge deployment for low latency
- Built-in error handling and logging

*/