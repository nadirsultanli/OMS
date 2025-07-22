# Railway Deployment Guide for OMS Backend

## 🚀 Quick Start

### 1. Prerequisites
- Railway account (https://railway.app)
- GitHub repository with your code
- Supabase project (for development/testing)

### 2. Deploy to Railway

#### Option A: Deploy via Railway Dashboard
1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Railway will automatically detect the Python project and deploy

#### Option B: Deploy via Railway CLI
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize Railway project
railway init

# Deploy
railway up
```

### 3. Environment Variables Setup

Set these environment variables in Railway Dashboard:

#### Required Variables:
```bash
# Application
ENVIRONMENT=production
LOG_LEVEL=INFO
PORT=8000

# Database (Railway PostgreSQL)
DATABASE_URL=postgresql+asyncpg://username:password@host:port/database

# Supabase (for auth)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# CORS
ALLOWED_ORIGINS=https://your-frontend-domain.com
```

#### Optional Variables:
```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

### 4. Database Setup

#### Option A: Use Railway PostgreSQL
1. Add PostgreSQL service in Railway
2. Copy the connection string to `DATABASE_URL`
3. Run migrations manually or via Railway CLI

#### Option B: Use External Database
- Set `DATABASE_URL` to your external PostgreSQL connection string

### 5. Run Database Migrations

```bash
# Via Railway CLI
railway run python -c "
from app.infrastucture.database.connection import init_database
import asyncio
asyncio.run(init_database())
"
```

## 🔧 Configuration Files

### railway.toml
- Build configuration using Nixpacks
- Health check settings
- Restart policies

### nixpacks.toml
- Python 3.11 setup
- PostgreSQL client installation
- Build and start commands

### Procfile
- Web process definition for Railway

## 📊 Monitoring & Health Checks

### Health Check Endpoint
- URL: `https://your-app.railway.app/health`
- Returns: `{"status": "healthy"}`

### Logs
```bash
# View logs via Railway CLI
railway logs

# View logs in Railway Dashboard
# Go to your project → Deployments → View logs
```

### Metrics
- Railway provides built-in metrics
- Monitor CPU, memory, and network usage
- Set up alerts for resource usage

## 🔒 Security Considerations

### Environment Variables
- Never commit `.env` files
- Use Railway's environment variable management
- Rotate secrets regularly

### CORS Configuration
```python
# Update in main.py for production
ALLOWED_ORIGINS = config("ALLOWED_ORIGINS", default="*").split(",")
```

### Database Security
- Use Railway's managed PostgreSQL
- Enable SSL connections
- Restrict database access

## 🚀 Deployment Workflow

### 1. Development
```bash
# Local development
python -m uvicorn app.cmd.main:app --reload
```

### 2. Testing
```bash
# Run tests
pytest

# Test deployment locally
docker build -t oms-backend .
docker run -p 8000:8000 oms-backend
```

### 3. Deployment
```bash
# Push to GitHub
git push origin main

# Railway automatically deploys on push
# Or manually deploy
railway up
```

### 4. Post-Deployment
```bash
# Check health
curl https://your-app.railway.app/health

# Run migrations
railway run python -c "from app.infrastucture.database.connection import init_database; import asyncio; asyncio.run(init_database())"

# Test API
curl https://your-app.railway.app/
```

## 🔄 CI/CD Integration

### GitHub Actions (Optional)
```yaml
name: Deploy to Railway
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: railway/cli@v1
        with:
          railway_token: ${{ secrets.RAILWAY_TOKEN }}
          service: oms-backend
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Build Failures
```bash
# Check build logs
railway logs

# Common fixes:
# - Update requirements.txt
# - Check Python version compatibility
# - Verify file paths
```

#### 2. Database Connection Issues
```bash
# Test database connection
railway run python -c "
from app.infrastucture.database.connection import get_supabase_client
import asyncio
client = asyncio.run(get_supabase_client())
print('Database connection successful')
"
```

#### 3. Health Check Failures
```bash
# Check application logs
railway logs

# Verify environment variables
railway variables
```

#### 4. Port Issues
- Railway automatically sets `$PORT`
- Ensure your app uses `$PORT` environment variable
- Check `uvicorn` command in start script

### Debug Commands
```bash
# SSH into Railway container
railway shell

# Run commands in Railway environment
railway run python -c "print('Hello from Railway')"

# Check environment variables
railway run env | grep -E "(DATABASE|SUPABASE|ENVIRONMENT)"
```

## 📈 Scaling

### Auto-scaling
- Railway automatically scales based on traffic
- Configure scaling rules in Railway Dashboard

### Manual Scaling
```bash
# Scale via CLI
railway scale web=2

# Scale via Dashboard
# Go to your service → Settings → Scale
```

## 💰 Cost Optimization

### Resource Management
- Monitor resource usage in Railway Dashboard
- Optimize container size
- Use appropriate instance types

### Database Optimization
- Use connection pooling
- Optimize queries
- Monitor database performance

## 🔗 Useful Links

- [Railway Documentation](https://docs.railway.app/)
- [Nixpacks Documentation](https://nixpacks.com/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Supabase Documentation](https://supabase.com/docs)

## 📞 Support

- Railway Support: [support@railway.app](mailto:support@railway.app)
- Railway Discord: [discord.gg/railway](https://discord.gg/railway)
- Railway Status: [status.railway.app](https://status.railway.app) 