"""
Example test configuration for environment variables.
Copy this to .env.test in your backend folder and configure for your test environment.
"""

# Test Environment Configuration
TEST_ENVIRONMENT_VARS = {
    # For SQLite in-memory testing (fastest)
    "TEST_DATABASE_URL": "sqlite+aiosqlite:///:memory:",
    
    # For PostgreSQL testing (more realistic, use your test database)
    # "TEST_DATABASE_URL": "postgresql+asyncpg://postgres:password@localhost:5432/test_oms",
    
    # For Supabase testing (real database - use cautiously)
    # "TEST_DATABASE_URL": "postgresql+asyncpg://postgres.gwheuhduxicqjnvfygej:CNX2023Posejdon!@aws-0-eu-central-1.pooler.supabase.com:5432/postgres",
    
    # Application Configuration for Tests
    "ENVIRONMENT": "test",
    "LOG_LEVEL": "ERROR",  # Reduce noise during testing
    
    # Supabase Configuration (for tests that need it)
    "SUPABASE_URL": "https://gwheuhduxicqjnvfygej.supabase.co",
    "SUPABASE_KEY": "your_test_key_here",
    
    # API Configuration
    "API_HOST": "127.0.0.1",
    "API_PORT": "8001",  # Different port for tests
}

# Instructions for setup:
# 1. Create .env.test file in backend folder
# 2. Copy the variables you need from above
# 3. Adjust database URL for your test environment
# 4. Run tests with: pytest tests/ -v