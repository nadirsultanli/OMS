# Railway Deployment Guide for OMS Backend

This guide walks you through deploying your FastAPI OMS Backend to Railway.

## 🚀 Quick Deploy

1. **Connect to Railway:**
   ```bash
   railway login
   railway init
   ```

2. **Set up environment variables in Railway dashboard:**
   - `DATABASE_URL` - Your PostgreSQL database URL
   - `SUPABASE_URL` - Your Supabase project URL
   - `SUPABASE_ANON_KEY` - Your Supabase anon key
   - `SUPABASE_SERVICE_ROLE_KEY` - Your Supabase service role key
   - `ENVIRONMENT` - Set to `production`
   - `LOG_LEVEL` - Set to `INFO`

3. **Deploy:**
   ```bash
   railway up
   ```

## 📁 Files Created for Railway

- **`Dockerfile`** - Container configuration
- **`railway.json`** - Railway-specific deployment config
- **`start.sh`** - Production startup script
- **`.dockerignore`** - Files to exclude from Docker build
- **`.env.example`** - Environment variables template

## 🗃️ Database Setup

### Option 1: Use Railway PostgreSQL
1. In Railway dashboard: **New** → **Database** → **PostgreSQL**
2. Copy the `DATABASE_URL` from the PostgreSQL service
3. Add it to your app's environment variables

### Option 2: Use External Database (Supabase)
1. Get your Supabase PostgreSQL URL from Settings → Database
2. Format it as: `postgresql+asyncpg://postgres:[password]@[host]:5432/postgres`
3. Add it as `DATABASE_URL` environment variable

## 🔐 Environment Variables Required

In your Railway dashboard, set these variables:

```env
# Required
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Optional
ENVIRONMENT=production
LOG_LEVEL=INFO
ALLOWED_ORIGINS=*
```

## 🌐 Domain Configuration

1. Go to Railway dashboard → Your service
2. Click **Settings** → **Domains**
3. **Generate Domain** or add custom domain

## 🔍 Health Checks

Railway will automatically health check your app at `/health`.

## 📋 Troubleshooting

### Common Issues:

1. **Port Error**: Make sure you're not hardcoding ports. Railway automatically sets `$PORT`.

2. **Database Connection**: 
   - Verify `DATABASE_URL` format: `postgresql+asyncpg://...`
   - Ensure database allows external connections

3. **Build Fails**:
   - Check Dockerfile syntax
   - Verify requirements.txt exists and is valid

4. **App Won't Start**:
   - Check Railway logs: `railway logs`
   - Verify all required environment variables are set

### Debug Commands:
```bash
# View logs
railway logs

# Connect to deployed app
railway shell

# Check status
railway status
```

## 🏗️ Custom Build Commands

If you need custom build steps, modify the `Dockerfile` or create a `railway.json` with custom commands.

## 📊 Monitoring

- Use Railway dashboard for metrics
- Check logs with `railway logs`
- Set up health checks at `/health`

## 🔄 Auto-Deploy

Railway auto-deploys on git push to your main branch. To disable:
1. Go to service settings
2. Toggle off **Auto Deploy**

## 🛡️ Security Notes

- Never commit `.env` files
- Use Railway's environment variables for secrets
- Enable HTTPS (automatic with Railway domains)
- Consider using Railway's private networking for database connections

---

Your OMS Backend should now be running on Railway! 🎉