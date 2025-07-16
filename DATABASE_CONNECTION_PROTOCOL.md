# 🗄️ AVA OLO Database Connection Protocol
## Systematic Solution for All Database Connection Issues

Based on analysis of both the **monitoring dashboards** and **agricultural core** services, here's the definitive protocol for database connections.

---

## 🎯 **Current Problem Analysis**

### **Issue 1: Authentication Failures**
```
FATAL: password authentication failed for user "postgres"
FATAL: no pg_hba.conf entry for host "172.31.96.165", user "postgres", database "farmer_crm"
```

### **Issue 2: Connection Pattern Inconsistencies**
- **Monitoring Dashboards**: Uses direct SQLAlchemy with hardcoded SQL
- **Agricultural Core**: Uses LLM-first approach with constitutional compliance
- **Different**: Connection pooling, SSL handling, error management

---

## 📋 **DEFINITIVE CONNECTION PROTOCOL**

### **Step 1: Environment Variable Configuration**
```bash
# Required AWS App Runner Environment Variables
DATABASE_URL=postgresql://username:password@hostname:5432/database_name
DB_HOST=farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com
DB_NAME=farmer_crm
DB_USER=postgres
DB_PASSWORD=your_secure_password
DB_PORT=5432

# SSL Configuration (REQUIRED for AWS RDS)
DB_SSL_MODE=require
DB_SSL_CERT_PATH=/opt/rds-ca-2019-root.pem
```

### **Step 2: Standard Connection Class**
```python
class StandardDatabaseConnection:
    """Unified database connection for all AVA OLO services"""
    
    def __init__(self, connection_string: str = None):
        self.connection_string = self._build_connection_string(connection_string)
        self.engine = self._create_engine()
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def _build_connection_string(self, connection_string: str = None) -> str:
        """Build and validate connection string"""
        if connection_string:
            return connection_string.strip()
        
        # Build from environment variables
        db_host = os.getenv('DB_HOST', '').strip().replace(" ", "")
        db_name = os.getenv('DB_NAME', 'farmer_crm')
        db_user = os.getenv('DB_USER', 'postgres')
        db_password = os.getenv('DB_PASSWORD', '')
        db_port = os.getenv('DB_PORT', '5432')
        
        if not all([db_host, db_password]):
            raise ValueError("Missing required database credentials")
        
        connection_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        
        # Validate format
        if not connection_string.startswith("postgresql://"):
            raise ValueError("Invalid connection string format")
        
        return connection_string
    
    def _create_engine(self):
        """Create SQLAlchemy engine with proper AWS RDS configuration"""
        engine_kwargs = {
            "pool_size": 20,
            "max_overflow": 30,
            "pool_pre_ping": True,
            "pool_recycle": 300,
            "echo": False
        }
        
        # AWS RDS SSL requirement
        if ".amazonaws.com" in self.connection_string:
            engine_kwargs["connect_args"] = {
                "sslmode": "require",
                "sslcert": None,
                "sslkey": None,
                "sslrootcert": None
            }
        
        return create_engine(self.connection_string, **engine_kwargs)
    
    def get_session(self) -> Session:
        """Get database session with proper error handling"""
        return self.SessionLocal()
    
    async def health_check(self) -> bool:
        """Test database connectivity"""
        try:
            with self.get_session() as session:
                result = session.execute(text("SELECT 1")).scalar()
                return result == 1
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
```

### **Step 3: Query Execution Patterns**

#### **A. Dashboard Queries (Monitoring Service)**
```python
async def get_dashboard_data(self) -> Dict[str, Any]:
    """Standard dashboard query pattern"""
    try:
        with self.db.get_session() as session:
            # Use parameterized queries
            result = session.execute(
                text("SELECT COUNT(*) FROM farmers WHERE is_active = :active"),
                {"active": True}
            )
            count = result.scalar()
            
            session.commit()  # Always commit
            return {"success": True, "count": count}
            
    except Exception as e:
        logger.error(f"Query failed: {e}")
        return {"success": False, "error": str(e)}
```

#### **B. Registration Operations (Core Service)**
```python
async def register_farmer(self, farmer_data: Dict[str, Any]) -> Dict[str, Any]:
    """Standard registration pattern"""
    try:
        with self.db.get_session() as session:
            # Insert farmer
            farmer_result = session.execute(
                text("""
                INSERT INTO farmers (farm_name, manager_name, email, phone)
                VALUES (:farm_name, :manager_name, :email, :phone)
                RETURNING id
                """),
                farmer_data
            )
            farmer_id = farmer_result.scalar()
            
            # Insert related data
            for field in farmer_data.get("fields", []):
                session.execute(
                    text("""
                    INSERT INTO fields (farmer_id, field_name, area_hectares)
                    VALUES (:farmer_id, :field_name, :area_hectares)
                    """),
                    {
                        "farmer_id": farmer_id,
                        "field_name": field["name"],
                        "area_hectares": field["size"]
                    }
                )
            
            session.commit()
            return {"success": True, "farmer_id": farmer_id}
            
    except Exception as e:
        session.rollback()
        logger.error(f"Registration failed: {e}")
        return {"success": False, "error": str(e)}
```

---

## 🔧 **IMMEDIATE FIXES NEEDED**

### **1. AWS RDS Security Group Configuration**
```bash
# Add your App Runner IP range to RDS security group
# IP range: 172.31.96.0/24 (or your specific App Runner IPs)
aws ec2 authorize-security-group-ingress \
  --group-id sg-your-rds-security-group \
  --protocol tcp \
  --port 5432 \
  --cidr 172.31.96.0/24
```

### **2. Database User Permissions**
```sql
-- Connect to RDS as master user and run:
GRANT ALL PRIVILEGES ON DATABASE farmer_crm TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
```

### **3. SSL Certificate Configuration**
```bash
# Download RDS CA certificate
wget https://s3.amazonaws.com/rds-downloads/rds-ca-2019-root.pem -O /opt/rds-ca-2019-root.pem

# Set environment variable
export DB_SSL_CERT_PATH=/opt/rds-ca-2019-root.pem
```

---

## 🚀 **IMPLEMENTATION CHECKLIST**

### **Phase 1: Fix Current Issues**
- [ ] Update RDS security group rules
- [ ] Verify database user permissions
- [ ] Add SSL certificate configuration
- [ ] Test connection from App Runner

### **Phase 2: Standardize Connection Code**
- [ ] Implement `StandardDatabaseConnection` class
- [ ] Update monitoring dashboards to use standard connection
- [ ] Update agricultural core to use standard connection
- [ ] Add comprehensive error handling

### **Phase 3: Deployment Protocol**
- [ ] Create deployment health check
- [ ] Add connection monitoring
- [ ] Implement automatic retry logic
- [ ] Add performance monitoring

---

## 🔍 **TROUBLESHOOTING GUIDE**

### **Common Error Patterns**

#### **Error: "password authentication failed"**
```bash
# Check:
1. DB_PASSWORD environment variable is set correctly
2. Database user exists: SELECT usename FROM pg_user WHERE usename = 'postgres';
3. Password is correct in AWS RDS
```

#### **Error: "no pg_hba.conf entry"**
```bash
# Check:
1. RDS security group allows App Runner IP range
2. SSL mode is set to 'require'
3. Connection is coming from expected IP range
```

#### **Error: "could not translate host name"**
```bash
# Check:
1. DB_HOST has no spaces: 'farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com'
2. RDS instance is running
3. DNS resolution works from App Runner
```

---

## 📊 **MONITORING & HEALTH CHECKS**

### **Connection Health Endpoint**
```python
@app.get("/health/database")
async def database_health_check():
    """Standard database health check"""
    db = StandardDatabaseConnection()
    is_healthy = await db.health_check()
    
    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "farmer_crm",
        "connection_pool": {
            "size": 20,
            "overflow": 30
        }
    }
```

### **Performance Monitoring**
```python
async def monitor_query_performance(query_name: str, query_function):
    """Monitor database query performance"""
    start_time = time.time()
    try:
        result = await query_function()
        duration = time.time() - start_time
        
        logger.info(f"Query '{query_name}' completed in {duration:.2f}s")
        return result
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Query '{query_name}' failed after {duration:.2f}s: {e}")
        raise
```

---

## 📝 **NEXT STEPS**

1. **Fix AWS RDS Security Group** - Add App Runner IP range
2. **Verify Database Permissions** - Ensure postgres user has access
3. **Implement Standard Connection** - Use unified connection class
4. **Add SSL Configuration** - Proper SSL certificate handling
5. **Test Both Services** - Verify monitoring dashboards and core service
6. **Monitor Performance** - Add health checks and monitoring

This protocol should resolve all database connection issues systematically and prevent future problems.