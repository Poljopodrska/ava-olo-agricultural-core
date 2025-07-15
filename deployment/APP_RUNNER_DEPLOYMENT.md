# 🏛️ CAVA App Runner Deployment

## 📋 Architecture

CAVA runs as part of the main ava-olo-agricultural-core App Runner service:

```
┌─────────────────────────────────────┐
│      App Runner Container           │
│                                     │
│  ┌─────────────┐  ┌──────────────┐ │
│  │  Main API   │  │  CAVA API    │ │
│  │  Port 8080  │  │  Port 8001   │ │
│  └──────┬──────┘  └──────────────┘ │
│         │                           │
│         └───── localhost:8001 ──────┘
└─────────────────────────────────────┘
```

## 🚀 How It Works

1. **Single App Runner Service** runs both APIs
2. **Main API** (port 8080) - Public facing
3. **CAVA API** (port 8001) - Internal only
4. Communication via `localhost:8001`

## 📝 Configuration

### apprunner.yaml Updates:
- Uses `start_app_runner.py` to launch both services
- CAVA environment variables added
- Single container, multiple processes

### Key Settings:
```yaml
CAVA_SERVICE_URL: "http://localhost:8001"  # Internal communication
CAVA_DRY_RUN_MODE: "false"                 # Production mode
CAVA_ENABLE_GRAPH: "false"                 # Until Neptune/ElastiCache configured
```

## 🔧 AWS Services Needed

### 1. **ElastiCache Redis** (for CAVA memory)
```bash
aws elasticache create-cache-cluster \
  --cache-cluster-id cava-redis \
  --engine redis \
  --cache-node-type cache.t3.micro \
  --num-cache-nodes 1
```

### 2. **Update Security Groups**
- Allow App Runner to access RDS
- Allow App Runner to access ElastiCache

### 3. **Secrets Manager** (for sensitive data)
```bash
# Store sensitive values
aws secretsmanager create-secret \
  --name ava-olo/db-password \
  --secret-string "your-password"
```

## 📊 Database Setup

CAVA uses a separate schema in your existing RDS:

```sql
-- Run this on your RDS instance
CREATE SCHEMA IF NOT EXISTS cava;

-- CAVA tables
CREATE TABLE cava.conversation_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    farmer_id INTEGER NOT NULL,
    conversation_type VARCHAR(50),
    total_messages INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_message_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cava.intelligence_log (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255),
    message_type VARCHAR(100),
    llm_analysis JSONB,
    llm_response TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_sessions_farmer ON cava.conversation_sessions(farmer_id);
CREATE INDEX idx_intelligence_session ON cava.intelligence_log(session_id);
```

## 🚦 Deployment Steps

1. **Commit and Push**
```bash
git add .
git commit -m "Add CAVA to App Runner"
git push
```

2. **App Runner Auto-Deploy**
- App Runner will automatically rebuild
- Both services start together

3. **Verify Deployment**
```bash
# Check main API
curl https://YOUR-APP-RUNNER-URL.awsapprunner.com/health

# Check CAVA (via main API proxy endpoint if needed)
curl https://YOUR-APP-RUNNER-URL.awsapprunner.com/cava/health
```

## 🔍 Monitoring

### CloudWatch Logs
- Main API logs: `/aws/apprunner/main-api`
- CAVA logs: Mixed in same stream (prefixed with [CAVA])

### Health Checks
App Runner will monitor port 8080 (main API). CAVA health is internal.

## ⚠️ Important Notes

1. **Single Container** - Both services run in one container
2. **Internal Communication** - CAVA not exposed externally
3. **Shared Resources** - Monitor memory usage
4. **Graceful Shutdown** - Both services stop together

## 🆘 Troubleshooting

### CAVA not responding?
- Check CloudWatch logs for [CAVA] entries
- Ensure start_app_runner.py is executable
- Verify CAVA starts before main API

### Memory issues?
- Increase App Runner instance size
- Monitor with CloudWatch metrics

### Database connection issues?
- Verify RDS security group
- Check CAVA schema exists
- Confirm DATABASE_URL is correct