# 🚀 AVA OLO Dashboard Deployment Guide

## Overview
This guide explains how to deploy the AVA OLO dashboard system with proper routing for the front page and individual dashboards.

## Architecture

```
User → AWS App Runner → Main App (Port 8080)
                         ├── / (Front Page)
                         ├── /database-dashboard
                         └── /api/* endpoints
                         
                      → Business Dashboard App (Port 8004)
                         └── /business-dashboard (via proxy)
```

## Deployment Options

### Option 1: Single App Runner Service (Recommended for AWS)

Since AWS App Runner doesn't support multiple apps on different ports, we'll modify the main app to include all functionality:

1. **Update main.py** to include business dashboard routes
2. **Deploy as single service** to App Runner
3. **All dashboards accessible** from one URL

### Option 2: Multiple Services with Load Balancer

For more complex deployments:

1. **Deploy main app** (front page + database dashboard)
2. **Deploy business dashboard** separately
3. **Use Application Load Balancer** to route traffic

### Option 3: Local Development

Run both services locally:

```bash
# Terminal 1 - Main app with front page
python main.py  # Runs on port 8080

# Terminal 2 - Business dashboard
python run_business_dashboard.py  # Runs on port 8004
```

## Quick Deployment to AWS App Runner

### 1. Prepare Environment Variables

Set these in AWS App Runner configuration:

```
DB_HOST=your-rds-endpoint
DB_NAME=farmer_crm
DB_USER=postgres
DB_PASSWORD=your-password
DB_PORT=5432
OPENAI_API_KEY=sk-your-key
```

### 2. Update main.py for Single Service

The main.py already includes:
- Front page at `/`
- Database dashboard at `/database-dashboard`
- All API endpoints

### 3. Deploy to App Runner

1. Push code to GitHub
2. In AWS Console → App Runner:
   - Source: GitHub repository
   - Branch: main
   - Deployment trigger: Automatic
   - Build settings: Use apprunner.yaml
   - Service settings:
     - Port: 8080
     - Start command: `python main.py`

### 4. Access Your Dashboards

After deployment:
- Front page: `https://your-app.awsapprunner.com/`
- Database Dashboard: `https://your-app.awsapprunner.com/database-dashboard`

## Adding Business Dashboard to Main App

To include business dashboard in the main app:

1. Copy business analytics functions to main.py
2. Add business dashboard routes
3. Include Chart.js in the HTML templates

Example route addition:

```python
@app.get("/business-dashboard", response_class=HTMLResponse)
async def business_dashboard_page():
    # Fetch metrics
    overview = await get_database_overview()
    trends = await get_growth_trends()
    
    # Return HTML with embedded data
    return HTMLResponse(content=BUSINESS_DASHBOARD_HTML)
```

## Environment-Specific Configuration

### Development
```bash
# .env file
DB_HOST=localhost
DB_NAME=farmer_crm_dev
OPENAI_API_KEY=sk-dev-key
```

### Production
```bash
# AWS App Runner Environment
DB_HOST=your-rds.region.rds.amazonaws.com
DB_NAME=farmer_crm
OPENAI_API_KEY=sk-prod-key
```

## Monitoring

1. **Health Check**: `/health` endpoint
2. **AWS CloudWatch**: Automatic logging
3. **Error Tracking**: Check App Runner logs

## Troubleshooting

### Database Connection Issues
- Verify RDS security group allows App Runner
- Check VPC configuration
- Ensure DB credentials are correct

### OpenAI API Issues
- Verify API key is set correctly
- Check for rate limits
- Ensure VPC has NAT Gateway for external API calls

### Missing Data
- Run migrations: `python run_migration.py`
- Initialize standard queries: POST to `/api/initialize-standard-queries`
- Add timestamps: `python run_business_migrations.py`

## Security Considerations

1. **Never commit** `.env` files
2. **Use AWS Secrets Manager** for production
3. **Enable HTTPS** (automatic with App Runner)
4. **Restrict database access** to App Runner only

## Scaling

AWS App Runner automatically scales based on:
- Request volume
- CPU/Memory usage
- Configured limits

## Cost Optimization

1. **Use minimum instances**: 0.25 vCPU for low traffic
2. **Set max concurrency**: 100 requests per instance
3. **Enable auto-pause**: For development environments

## Next Steps

1. Set up CI/CD pipeline
2. Add monitoring dashboards
3. Implement caching for better performance
4. Add user authentication if needed