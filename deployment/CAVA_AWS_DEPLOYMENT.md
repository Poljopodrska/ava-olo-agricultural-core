# 🏛️ CAVA AWS Deployment Guide

## ✅ Pre-Deployment Checklist

### Local Checks Completed:
- ✅ CAVA service runs successfully
- ✅ All Python dependencies installed
- ✅ PostgreSQL configuration ready
- ✅ Environment files configured
- ✅ No hardcoded secrets
- ✅ Integration tests pass
- ✅ Original registration backed up

### AWS-Specific (Configure on AWS):
- ⏳ Docker (will be installed on EC2)
- ⏳ AWS credentials (will be auto-configured via IAM role)

---

## 🚀 AWS Deployment Steps

### 1. **Infrastructure Setup**
```yaml
# AWS Resources Needed:
- EC2 Instance: t3.medium (minimum)
- Application Load Balancer
- ElastiCache Redis Cluster
- Security Groups for CAVA ports
- IAM Role for EC2
```

### 2. **Environment Variables for Production**
```bash
# On AWS EC2, set these:
export CAVA_DRY_RUN_MODE=false
export CAVA_NEO4J_URI=bolt://cava-neo4j:7687
export CAVA_REDIS_URL=redis://your-elasticache-endpoint:6379
export DATABASE_URL=postgresql://user:pass@your-rds-endpoint:5432/farmer_crm
export OPENAI_API_KEY=your-production-key
```

### 3. **Docker Setup on EC2**
```bash
# Install Docker on Amazon Linux 2
sudo yum update -y
sudo yum install docker -y
sudo service docker start
sudo usermod -a -G docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 4. **Deploy CAVA**
```bash
# Clone repository
git clone https://github.com/your-repo/ava-olo-constitutional.git
cd ava-olo-constitutional/ava-olo-agricultural-core

# Start CAVA services
docker-compose -f docker/docker-compose.cava.yml up -d

# Start CAVA API
nohup python3 implementation/cava/cava_api.py > cava.log 2>&1 &
```

### 5. **Health Check**
```bash
curl http://localhost:8001/health
```

---

## 🔒 Security Configuration

### Security Groups:
```
CAVA-SG:
- Port 8001: CAVA API (from ALB only)
- Port 7474: Neo4j Web (internal only)
- Port 7687: Neo4j Bolt (internal only)
- Port 6379: Redis (ElastiCache security group)
```

### IAM Role for EC2:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "elasticache:DescribeCacheClusters",
        "rds:DescribeDBInstances",
        "cloudwatch:PutMetricData",
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## 📊 Monitoring

### CloudWatch Metrics:
- CAVA API response time
- Error rate
- Database connection pool
- Redis memory usage

### Alarms:
- High error rate (> 5%)
- API latency (> 1000ms)
- Memory usage (> 80%)

---

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow:
```yaml
name: Deploy CAVA to AWS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Deploy to EC2
        run: |
          # Your deployment script
          ./scripts/deploy_to_aws.sh
```

---

## ✅ Post-Deployment Verification

1. **Test Registration Flow:**
```bash
curl -X POST http://your-alb-endpoint/api/v1/register \
  -H "Content-Type: application/json" \
  -d '{"farmer_id": 12345, "message": "Peter Knaflič"}'
```

2. **Check Logs:**
```bash
tail -f /var/log/cava/cava_api.log
```

3. **Monitor Health:**
```bash
watch -n 5 'curl -s http://localhost:8001/health | jq .'
```

---

## 🆘 Troubleshooting

### CAVA won't start:
- Check Docker: `docker ps`
- Check logs: `docker logs cava-neo4j`
- Verify environment variables

### Can't connect to databases:
- Check security groups
- Verify ElastiCache endpoint
- Test RDS connection

### High latency:
- Scale EC2 instance
- Check OpenAI API limits
- Review CloudWatch metrics