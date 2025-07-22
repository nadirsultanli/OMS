# CI/CD Setup Guide

## 🚀 **CI/CD Options Available**

### **Option 1: Railway Auto-Deploy (Simplest)**
Railway automatically deploys when you push to your main branch.

**Setup:**
1. Connect your GitHub repo to Railway
2. Enable auto-deploy in Railway dashboard
3. Push to main branch = automatic deployment

### **Option 2: GitHub Actions (Recommended)**
Full CI/CD pipeline with testing, linting, and deployment.

**Setup:**
1. Add GitHub Secrets:
   - `RAILWAY_TOKEN` - Your Railway API token
   - `RAILWAY_URL` - Your Railway app URL

2. The workflow will:
   - ✅ Run tests
   - ✅ Check code quality (linting)
   - ✅ Deploy to Railway
   - ✅ Health check after deployment

### **Option 3: Manual Deployment**
Use the provided scripts for manual deployments.

## 🔧 **GitHub Actions Setup**

### **Required Secrets:**
```bash
# Get Railway token
railway login
railway whoami

# Add to GitHub Secrets:
RAILWAY_TOKEN=your_railway_token_here
RAILWAY_URL=https://your-app.railway.app
```

### **Workflow Features:**
- **Triggers**: Push to main/master, Pull Requests
- **Testing**: Runs all tests before deployment
- **Linting**: Code quality checks (flake8, black, isort)
- **Deployment**: Automatic Railway deployment
- **Health Check**: Verifies deployment success

## 📋 **CI/CD Pipeline Steps**

### **Test Job:**
1. **Setup**: Python 3.11, cache dependencies
2. **Install**: Production and dev dependencies
3. **Lint**: Code quality checks
4. **Test**: Run pytest suite
5. **Verify**: Import and health endpoint tests

### **Deploy Job:**
1. **Deploy**: Push to Railway
2. **Health Check**: Verify deployment success

## 🎯 **Usage**

### **Automatic Deployment:**
```bash
# Just push to main branch
git push origin main
# GitHub Actions will handle the rest!
```

### **Manual Trigger:**
```bash
# Go to GitHub Actions tab
# Click "Run workflow" on the CI/CD pipeline
```

### **Check Status:**
```bash
# View Railway deployment
railway logs

# Check GitHub Actions
# Go to Actions tab in your repo
```

## 🔍 **Monitoring**

### **GitHub Actions:**
- View workflow runs in Actions tab
- Check test results and deployment status
- Debug failed deployments

### **Railway:**
- Monitor deployment logs
- Check application health
- View resource usage

## 🛠 **Troubleshooting**

### **Common Issues:**

1. **Tests Fail:**
   ```bash
   # Run tests locally first
   python -m pytest tests/ -v
   ```

2. **Deployment Fails:**
   ```bash
   # Check Railway logs
   railway logs
   
   # Verify environment variables
   railway variables
   ```

3. **Health Check Fails:**
   ```bash
   # Check if app starts locally
   uvicorn app.cmd.main:app --host 0.0.0.0 --port 8000
   ```

## 📊 **Benefits**

- ✅ **Automated Testing**: Every push is tested
- ✅ **Code Quality**: Linting ensures consistent code
- ✅ **Zero Downtime**: Automatic deployments
- ✅ **Rollback**: Easy to revert deployments
- ✅ **Monitoring**: Health checks and logging
- ✅ **Security**: Secrets management

## 🎉 **Ready to Deploy!**

Your CI/CD pipeline is now set up! Just:

1. Add the required GitHub secrets
2. Push to main branch
3. Watch the magic happen! ✨ 