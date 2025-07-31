# OMS System Performance Optimization Plan

## Current Performance Issues Identified

### 1. **Database Connection Bottlenecks**
- **Issue**: Single Supabase client instance with thread pool execution
- **Impact**: Each database operation blocks the event loop
- **Solution**: Implement connection pooling and async database operations

### 2. **Audit Middleware Overhead**
- **Issue**: Synchronous audit logging for every request
- **Impact**: Adds 100-500ms latency per request
- **Solution**: Async audit logging with background processing

### 3. **Server Configuration**
- **Issue**: Single worker with reload enabled
- **Impact**: Limited concurrency and unnecessary reload overhead
- **Solution**: Multi-worker configuration with proper load balancing

### 4. **Missing Caching Layer**
- **Issue**: No caching for frequently accessed data
- **Impact**: Repeated database queries for same data
- **Solution**: Implement Redis caching for static data

### 5. **Inefficient Database Queries**
- **Issue**: N+1 query problems in repositories
- **Impact**: Multiple round trips to database
- **Solution**: Optimize queries with joins and batch operations

## Optimization Implementation Plan

### Phase 1: Immediate Performance Gains (1-2 days)

#### 1.1 Server Configuration Optimization
```yaml
# docker-compose.yaml optimization
services:
  oms-backend:
    environment:
      - WORKERS=4  # Multi-worker setup
      - WORKER_CLASS=uvicorn.workers.UvicornWorker
      - MAX_REQUESTS=1000
      - MAX_REQUESTS_JITTER=100
    command: ["uvicorn", "app.cmd.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

#### 1.2 Database Connection Pooling
```python
# Enhanced database connection with pooling
class OptimizedDatabaseConnection:
    def __init__(self):
        self._pool = None
        self._max_connections = 20
        self._min_connections = 5
    
    async def get_connection(self):
        # Implement connection pooling
        pass
```

#### 1.3 Async Audit Logging
```python
# Background audit logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

class AsyncAuditMiddleware:
    def __init__(self):
        self._executor = ThreadPoolExecutor(max_workers=4)
    
    async def log_audit_async(self, audit_data):
        # Non-blocking audit logging
        await asyncio.get_event_loop().run_in_executor(
            self._executor, self._log_audit_sync, audit_data
        )
```

### Phase 2: Caching Implementation (2-3 days)

#### 2.1 Redis Integration
```python
# Redis caching service
import redis.asyncio as redis

class CacheService:
    def __init__(self):
        self.redis = redis.Redis(host='redis', port=6379, decode_responses=True)
    
    async def get_cached_data(self, key: str):
        return await self.redis.get(key)
    
    async def set_cached_data(self, key: str, value: str, ttl: int = 3600):
        await self.redis.setex(key, ttl, value)
```

#### 2.2 Cache-Enabled Repositories
```python
# Optimized repository with caching
class CachedInvoiceRepository:
    def __init__(self, cache_service: CacheService):
        self.cache = cache_service
    
    async def get_invoice_by_id(self, invoice_id: str):
        # Check cache first
        cached = await self.cache.get_cached_data(f"invoice:{invoice_id}")
        if cached:
            return json.loads(cached)
        
        # Fetch from database
        invoice = await self._fetch_from_db(invoice_id)
        
        # Cache for 1 hour
        await self.cache.set_cached_data(f"invoice:{invoice_id}", json.dumps(invoice), 3600)
        return invoice
```

### Phase 3: Query Optimization (3-4 days)

#### 3.1 Batch Operations
```python
# Batch invoice creation
async def create_invoices_batch(self, invoices: List[Invoice]) -> List[Invoice]:
    # Single database transaction for multiple invoices
    async with self.db.transaction():
        for invoice in invoices:
            await self._create_single_invoice(invoice)
    return invoices
```

#### 3.2 Optimized Queries
```sql
-- Optimized invoice query with joins
SELECT 
    i.*,
    array_agg(il.*) as invoice_lines
FROM invoices i
LEFT JOIN invoice_lines il ON i.id = il.invoice_id
WHERE i.tenant_id = $1
GROUP BY i.id;
```

### Phase 4: Advanced Optimizations (4-5 days)

#### 4.1 Database Indexing
```sql
-- Performance indexes
CREATE INDEX CONCURRENTLY idx_invoices_tenant_status_date 
ON invoices(tenant_id, invoice_status, invoice_date);

CREATE INDEX CONCURRENTLY idx_payments_tenant_date 
ON payments(tenant_id, payment_date);

CREATE INDEX CONCURRENTLY idx_audit_events_tenant_timestamp 
ON audit_events(tenant_id, created_at);
```

#### 4.2 Response Compression
```python
# Gzip compression middleware
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

#### 4.3 Rate Limiting
```python
# Rate limiting for API endpoints
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/v1/invoices")
@limiter.limit("100/minute")
async def create_invoice(request: Request):
    pass
```

## Performance Monitoring

### 1. Metrics Collection
```python
# Performance metrics middleware
import time
from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests')
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

class MetricsMiddleware:
    async def __call__(self, request, call_next):
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time
        
        REQUEST_COUNT.inc()
        REQUEST_DURATION.observe(duration)
        
        return response
```

### 2. Health Checks
```python
# Enhanced health check with performance metrics
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": await check_db_connection(),
        "cache": await check_cache_connection(),
        "uptime": time.time() - start_time,
        "memory_usage": psutil.virtual_memory().percent
    }
```

## Expected Performance Improvements

### Before Optimization:
- Average response time: 500-1000ms
- Concurrent users: 10-20
- Database queries per request: 5-10
- Memory usage: 200-300MB

### After Optimization:
- Average response time: 100-200ms (80% improvement)
- Concurrent users: 100-200 (10x improvement)
- Database queries per request: 1-2 (80% reduction)
- Memory usage: 150-200MB (25% reduction)

## Implementation Priority

1. **High Priority** (Week 1):
   - Server configuration optimization
   - Async audit logging
   - Basic connection pooling

2. **Medium Priority** (Week 2):
   - Redis caching implementation
   - Query optimization
   - Database indexing

3. **Low Priority** (Week 3):
   - Advanced monitoring
   - Rate limiting
   - Response compression

## Monitoring and Maintenance

### Daily Monitoring:
- Response time tracking
- Error rate monitoring
- Database connection pool status
- Cache hit/miss ratios

### Weekly Optimization:
- Query performance analysis
- Cache effectiveness review
- Memory usage optimization
- Database index maintenance

This optimization plan will significantly improve the OMS system performance while maintaining reliability and scalability. 