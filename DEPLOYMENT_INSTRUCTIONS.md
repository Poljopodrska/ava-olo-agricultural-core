# AVA OLO Monitoring Dashboards - Deployment Instructions

## Environment Variables Required

Set these environment variables in AWS ECS:

```bash
# Database Configuration
DB_HOST=farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com
DB_NAME=farmer_crm
DB_USER=postgres
DB_PASSWORD=<ACTUAL_RDS_PASSWORD_HERE>  # IMPORTANT: Use the actual RDS password!
DB_PORT=5432

# NOTE: The password shown in debug output (%3C~Xzntr2r~m6-7%29~4%2AMO%2...) 
# decodes to something like: <~Xzntr2r~m6-7)~4*MO*...
# This appears to be different from what was documented previously

# Google Maps API
GOOGLE_MAPS_API_KEY=AIzaSyDyFXHN3VqQ9kWvj9ihcLjkpemf1FBc3uo  # CORRECT WORKING KEY!

# OpenAI API (Optional)
OPENAI_API_KEY=your_openai_key_here
```

## Pre-Deployment Checklist

1. **Environment Variables**: Ensure all environment variables above are set in AWS ECS
2. **RDS Security Group**: Verify the RDS security group allows connections from ECS IP range (172.31.96.0/24)
3. **SSL Mode**: The application is configured to use SSL for RDS connections automatically

## Deployment Steps

1. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **AWS ECS**: The service should automatically deploy from the GitHub repository

3. **Verify Deployment**:
   - Check `/` - Home page should load
   - Check `/database-dashboard` - Should show farmers list
   - Check `/farmer-registration` - Should show registration form with working Google Maps
   - Check `/debug/database-connection` - Should show successful connection

## Known Issues and Solutions

### Issue: Database Authentication Failed
**Solution**: 
1. The password contains special characters that need URL encoding. The application handles this automatically.
2. **IMPORTANT**: If you see `%3C` in the password (which is `<`), the password might be getting HTML-encoded by AWS. 
   - Make sure to enter the password in AWS ECS exactly as: `2hpzvrg_xP~qNbz1[_NppSK$e*O1`
   - Do NOT use quotes around the password in AWS ECS environment variables
   - If the password still fails, try using the debug endpoint `/debug/test-password-encoding` to see what's being received

### Issue: Google Maps Not Loading
**Solution**: 
1. Verify GOOGLE_MAPS_API_KEY is set in environment
2. Check that the API key has Maps JavaScript API enabled in Google Cloud Console
3. The application will show a fallback message if the key is missing

### Issue: Connection Timeout to RDS
**Solution**:
1. Check RDS security group has inbound rule for ECS IP range
2. Verify RDS instance is publicly accessible if connecting from outside VPC
3. Ensure SSL mode is set to 'require' (handled automatically)

## Debug Endpoints

Once deployed, you can check these endpoints:

- `/debug/database-connection` - Shows database connection status
- `/api/debug/status` - Shows application status
- `/health/database` - Database health check

## Local Development

For local development, you cannot connect to AWS RDS from outside the VPC. Options:
1. Use SSH tunnel through a bastion host
2. Use VPN connection to AWS VPC
3. Use a local PostgreSQL instance for development

## Running Locally (with proper network access)

```bash
# Use the provided script
bash run_with_env.sh

# Or set environment variables manually
export DB_HOST="farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com"
export DB_NAME="farmer_crm"
export DB_USER="postgres"
export DB_PASSWORD='2hpzvrg_xP~qNbz1[_NppSK$e*O1'
export DB_PORT="5432"
export GOOGLE_MAPS_API_KEY="AIzaSyDyFXHN3VqQ9kWvj9ihcLjkpemf1FBc3uo"

python3 main.py
```

## Post-Deployment Testing

Run `test_deployment.py` from within the AWS environment to verify all connections:

```bash
python3 test_deployment.py
```

This will test:
- Environment variable configuration
- Database connectivity
- Google Maps API configuration

## Important Security Notes

1. Never commit credentials to version control
2. Use AWS Secrets Manager for production credentials
3. Rotate database passwords regularly
4. Monitor access logs for suspicious activity