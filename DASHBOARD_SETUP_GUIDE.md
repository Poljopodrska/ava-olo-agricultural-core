# 🌾 AVA OLO Dashboard System - Complete Setup Guide

## 🚀 Quick Start (5 Minutes)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp env_example.txt .env
# Edit .env with your PostgreSQL credentials

# 3. Set up database
createdb ava_olo
psql -d ava_olo -f create_schema.sql

# 4. Start dashboard system
python run_dashboards.py

# 5. Open dashboards in browser (auto-opens)
# Monitoring: http://localhost:8080/monitoring_dashboard.html
# Explorer: http://localhost:8080/database_explorer.html
```

## 📋 What You Get

Your complete AVA OLO Dashboard System includes:

### 🎯 **Business Monitoring Dashboard**
- **Real-time metrics**: Total farmers, fields, crops, conversations
- **Growth analytics**: Daily/weekly/monthly growth trends
- **Croatian localization**: All text in Croatian language
- **Live activity feed**: Real-time farmer interactions
- **Visual charts**: Growth trends, crop distribution
- **WebSocket updates**: Live data streaming

### 🔍 **Database Explorer**
- **Interactive data browser**: All tables with pagination
- **Search and filtering**: Find specific data quickly
- **Column statistics**: Data type analysis, null counts, samples
- **Excel/CSV export**: Download data for analysis
- **SQL query interface**: Custom queries with safety checks
- **Relationship visualization**: Foreign key mappings

### 🔌 **REST APIs**
- **Monitoring API** (Port 8000): Business intelligence endpoints
- **Explorer API** (Port 8001): Database exploration endpoints
- **Comprehensive docs**: Auto-generated API documentation

## 📁 System Architecture

```
AVA OLO Dashboard System
├── monitoring_api.py           # 🎯 Business metrics API
├── explorer_api.py             # 🔍 Database exploration API
├── monitoring_dashboard.html   # 📊 Real-time dashboard UI
├── database_explorer.html      # 🗃️ Interactive data browser
├── run_dashboards.py          # 🚀 System orchestrator
├── config.py                  # ⚙️ Enhanced configuration
├── test_apis.py               # 🧪 Comprehensive tests
├── requirements.txt           # 📦 Dependencies
└── env_example.txt           # 🔐 Environment template
```

## 🗄️ Database Integration

### Compatible Tables
Your system works with these Croatian agricultural tables:

- `ava_farmers` - Croatian farmers (OPG podaci)
- `ava_fields` - Agricultural fields (poljoprivredna gospodarstva)
- `ava_field_crops` - Crops planted (posijani usjevi)
- `ava_conversations` - Farmer chat history (razgovori)
- `farm_tasks` - Agricultural operations (poljoprivredni zadaci)
- `system_health_log` - System monitoring
- `llm_debug_log` - AI operation logs

### Croatian Data Features
- **Crop names**: Both English and Croatian (Kukuruz, Pšenica, etc.)
- **Geographic data**: Croatian cities and regions
- **Farm types**: Grain, vegetable, livestock, mixed
- **Localized metrics**: Hectares, Croatian currency

## ⚙️ Configuration

### Environment Variables (.env)

```env
# Database (Required)
DATABASE_URL=postgresql://user:pass@localhost:5432/ava_olo
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ava_olo
DB_USER=postgres
DB_PASSWORD=your_password

# API Ports (Optional)
MONITORING_API_PORT=8000
EXPLORER_API_PORT=8001
DASHBOARD_HTTP_PORT=8080

# Croatian Settings
TIMEZONE=Europe/Zagreb
LOCALE=hr_HR.UTF-8
```

### Advanced Configuration

```python
# config.py already includes:
# - Connection pooling (20 connections)
# - Croatian timezone handling
# - Logging configuration
# - Security settings
# - Performance optimization
```

## 🚀 Deployment Options

### Option 1: Local Development
```bash
python run_dashboards.py
```

### Option 2: Production with Gunicorn
```bash
# Start monitoring API
gunicorn monitoring_api:app -w 4 -b 0.0.0.0:8000

# Start explorer API  
gunicorn explorer_api:app -w 4 -b 0.0.0.0:8001

# Serve dashboard files with nginx
```

### Option 3: Docker Deployment
```dockerfile
FROM python:3.11
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["python", "run_dashboards.py"]
```

## 🧪 Testing & Validation

### Run Complete Test Suite
```bash
# Start dashboard system first
python run_dashboards.py

# In another terminal, run tests
python test_apis.py
```

### Test Categories
- ✅ Database connectivity
- ✅ Monitoring API endpoints (8 endpoints)
- ✅ Explorer API endpoints (5+ endpoints)
- ✅ Dashboard HTML files
- ✅ WebSocket real-time updates
- ✅ Excel/CSV export functionality

### Expected Results
```
📊 Overall Results: 25/25 tests passed (100.0%)
🎉 Excellent! Dashboard system is working well.
```

## 📊 API Endpoints Reference

### Monitoring API (localhost:8000)

```http
GET /api/stats/overview           # Total farmers, fields, crops
GET /api/stats/growth-trends      # Growth rates by period
GET /api/stats/activity-today     # Today's activity summary
GET /api/stats/growth-chart       # Time series data
GET /api/stats/churn-chart        # Farmer retention
GET /api/activity/live-feed       # Recent activities
GET /api/activity/recent-entries  # Database changes
WS  /ws                          # Real-time updates
```

### Explorer API (localhost:8001)

```http
GET /api/schema/tables                    # All tables with metadata
GET /api/schema/relationships            # Foreign key relationships  
GET /api/data/{table}                    # Paginated table data
GET /api/data/{table}/columns            # Column statistics
GET /api/data/{table}/export             # Excel/CSV download
GET /api/query/custom?query=SELECT...    # Safe SQL queries
```

## 🎨 Frontend Features

### Monitoring Dashboard
- **Croatian interface**: Ukupno Farmi, Aktivna Polja, etc.
- **Real-time charts**: Chart.js visualizations
- **Responsive design**: Works on mobile/desktop
- **Live updates**: WebSocket integration
- **Connection status**: Visual connection indicator

### Database Explorer
- **Table browser**: Click tables to explore data
- **Advanced search**: Filter across columns
- **Export tools**: Excel/CSV download buttons
- **SQL interface**: Safe query execution
- **Relationship viewer**: Visual foreign key mapping

## 🔧 Troubleshooting

### Common Issues

#### 1. Database Connection Failed
```bash
# Check PostgreSQL is running
sudo service postgresql start

# Verify database exists
psql -l | grep ava_olo

# Test connection
psql -h localhost -U postgres -d ava_olo
```

#### 2. Module Import Errors
```bash
# Install all dependencies
pip install -r requirements.txt

# For asyncpg issues
pip install asyncpg==0.28.0
```

#### 3. Port Already in Use
```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>

# Or change ports in .env
MONITORING_API_PORT=8010
```

#### 4. CORS Issues
```bash
# Update CORS origins in .env
CORS_ORIGINS=http://localhost:8080,http://your-domain.com
```

### Performance Issues

#### Slow Queries
```sql
-- Add indexes for performance
CREATE INDEX idx_conversations_date ON ava_conversations(created_at);
CREATE INDEX idx_farmers_city ON ava_farmers(city);
```

#### High Memory Usage
```env
# Reduce connection pool size
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=15
```

## 🎯 Production Checklist

### Security
- [ ] Change default passwords
- [ ] Set strong API_SECRET_KEY
- [ ] Enable HTTPS_ONLY=True
- [ ] Configure firewall rules
- [ ] Set up SSL certificates

### Performance
- [ ] Set up database indexes
- [ ] Configure Redis caching
- [ ] Enable gzip compression
- [ ] Set up CDN for static files
- [ ] Monitor database performance

### Monitoring
- [ ] Set up log rotation
- [ ] Configure error alerting
- [ ] Monitor disk space
- [ ] Set up backup procedures
- [ ] Health check endpoints

## 🎨 Customization

### Adding New Metrics
```python
# In monitoring_api.py
@app.get("/api/stats/custom-metric")
async def get_custom_metric():
    # Your custom SQL queries here
    return {"custom_value": 123}
```

### Croatian Translations
```javascript
// In dashboard HTML
const translations = {
    'total_farmers': 'Ukupno Farmi',
    'active_fields': 'Aktivna Polja',
    // Add your translations
};
```

### Custom Styling
```css
/* Modify dashboard CSS */
.metric-card {
    background: your-custom-gradient;
}
```

## 📈 Next Steps

### Phase 1 Complete ✅
- [x] Real-time monitoring dashboard
- [x] Interactive database explorer  
- [x] Croatian agricultural data support
- [x] Excel/CSV export
- [x] WebSocket live updates

### Phase 2 Suggestions
- [ ] Email/SMS alerts for critical metrics
- [ ] Advanced analytics (trend predictions)
- [ ] Mobile app integration
- [ ] Multi-tenant support
- [ ] Advanced reporting tools

### Phase 3 Ideas
- [ ] Machine learning insights
- [ ] IoT sensor integration
- [ ] Weather data correlation
- [ ] Market price integration
- [ ] Drone/satellite imagery

## 🆘 Support

### Documentation
- API docs: `http://localhost:8000/docs`
- Explorer docs: `http://localhost:8001/docs`
- This guide: Complete reference

### Common Commands
```bash
# Quick restart
pkill -f "python.*run_dashboards" && python run_dashboards.py

# Check logs
tail -f ava_dashboard.log

# Database backup
pg_dump ava_olo > backup.sql

# Test individual APIs
curl http://localhost:8000/api/stats/overview
```

---

## 🎉 Success!

Your **AVA OLO Dashboard System** is now complete with:

✅ **Real-time monitoring** of Croatian farmers and fields  
✅ **Interactive database exploration** with Excel export  
✅ **Production-ready APIs** with comprehensive documentation  
✅ **Croatian localization** for agricultural terminology  
✅ **WebSocket live updates** for real-time data  
✅ **Comprehensive testing** with automated validation  

**🌾 Enjoy your Croatian Agricultural Virtual Assistant Dashboard! 🌾**