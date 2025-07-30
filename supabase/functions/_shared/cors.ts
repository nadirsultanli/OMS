/**
 * Shared CORS configuration for all Edge Functions
 */

export const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type, x-tenant-id, x-user-id',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
  'Access-Control-Max-Age': '86400', // 24 hours
}

/**
 * Handle CORS preflight requests
 */
export function handleCors(req: Request): Response | null {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { 
      headers: corsHeaders,
      status: 200 
    })
  }
  return null
}

/**
 * Create a response with CORS headers
 */
export function createCorsResponse(
  body: string | null, 
  init: ResponseInit = {}
): Response {
  const headers = {
    ...corsHeaders,
    'Content-Type': 'application/json',
    ...init.headers
  }
  
  return new Response(body, {
    ...init,
    headers
  })
}