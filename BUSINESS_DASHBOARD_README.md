# AVA OLO Business Dashboard

## Overview

The AVA OLO Business Dashboard provides comprehensive analytics and business intelligence for the Croatian agricultural virtual assistant platform. It offers insights into system usage, performance metrics, business growth, and user engagement patterns.

## Architecture

The business dashboard follows the modular "Mango in Bulgaria" architecture principle - completely independent and scalable without hardcoded patterns.

### Key Components

1. **BusinessDashboard Class** (`monitoring/business_dashboard.py`)
   - Core analytics engine
   - Database query abstraction
   - Metric calculation logic

2. **API Router** (`monitoring/business_dashboard.py`)
   - RESTful API endpoints
   - Error handling and response formatting
   - Query parameter validation

3. **Database Schema** (`create_schema.sql`)
   - Dedicated monitoring tables
   - Performance indexes
   - Croatian-specific data structures

## Features

### 1. Usage Metrics
- **Total Queries**: Number of farmer queries processed
- **Unique Users**: Active farmers using the system
- **Daily Active Users**: Farmers active in last 24 hours
- **Growth Rate**: Period-over-period growth comparison
- **Top Features**: Most used query types and topics

### 2. System Performance
- **Uptime Percentage**: System availability metrics
- **Response Times**: Average API response latency
- **Error Rates**: Failed operations tracking
- **Peak Usage Hours**: High-traffic time identification
- **System Load**: Resource utilization monitoring

### 3. Business Insights
- **Farmer Adoption Rate**: Percentage of registered farmers actively using the system
- **Geographic Distribution**: Usage patterns across Croatian regions
- **Crop Coverage**: Popular crops and farming practices
- **Seasonal Trends**: Monthly activity patterns
- **User Satisfaction**: Confidence scores and feedback analysis

### 4. Growth Projections
- **Trend Analysis**: Linear growth projections based on historical data
- **Farmer Growth**: Projected active user growth
- **Query Volume**: Expected system load projections
- **Confidence Levels**: Reliability indicators for projections

## API Endpoints

### Base URL: `/api/v1/business/`

#### GET `/usage`
**Description**: Get usage and engagement metrics
**Parameters**: 
- `days` (optional): Number of days to analyze (default: 30)

**Response**:
```json
{
  "total_queries": 1250,
  "unique_users": 85,
  "daily_active_users": 12,
  "average_session_length": 0.0,
  "top_features": [
    {
      "feature": "pest_control",
      "usage_count": 450,
      "percentage": 36.0
    }
  ],
  "growth_rate": 15.2
}
```

#### GET `/system`
**Description**: Get system performance metrics
**Parameters**: 
- `days` (optional): Number of days to analyze (default: 7)

**Response**:
```json
{
  "uptime_percentage": 99.2,
  "average_response_time": 156.7,
  "error_rate": 2.1,
  "api_calls_per_day": 87,
  "peak_usage_hours": [9, 14, 16, 20, 10],
  "system_load": {
    "cpu": 0.0,
    "memory": 0.0,
    "storage": 0.0
  }
}
```

#### GET `/insights`
**Description**: Get business intelligence insights

**Response**:
```json
{
  "farmer_adoption_rate": 68.5,
  "geographic_distribution": {
    "Zagreb": 25,
    "Osijek": 18,
    "Split": 12
  },
  "crop_coverage": {
    "Corn": 45,
    "Wheat": 32,
    "Sunflower": 28
  },
  "seasonal_trends": {
    "monthly_activity": [45, 52, 78, 123, 145, 167, 134, 98, 87, 76, 54, 43]
  },
  "user_satisfaction": 87.3
}
```

#### GET `/projections`
**Description**: Get growth projections
**Parameters**: 
- `months` (optional): Projection period in months (default: 6)

**Response**:
```json
{
  "projection_period_months": 6,
  "projected_active_farmers": 145,
  "projected_monthly_queries": 1850,
  "confidence": "medium",
  "historical_data": [
    {
      "month": "2024-01-01T00:00:00",
      "active_farmers": 65,
      "total_queries": 892
    }
  ]
}
```

#### GET `/summary`
**Description**: Get complete business dashboard summary

**Response**: Combined data from all endpoints with additional summary metrics.

## Database Schema

### Key Tables

1. **ava_conversations**
   - Farmer query history
   - Topics and confidence scores
   - Language and timestamp data

2. **ava_farmers**
   - Farmer registration data
   - Geographic information
   - Farm characteristics

3. **system_health_log**
   - Component status tracking
   - Response time monitoring
   - Error logging

4. **llm_debug_log**
   - AI operation logging
   - Performance metrics
   - Success/failure tracking

## Integration

### With Main API Gateway

```python
from monitoring.business_dashboard import router as business_router

app.include_router(business_router, prefix="", tags=["business-dashboard"])
```

### Error Handling

All endpoints implement comprehensive error handling:
- Database connection failures
- Invalid parameter validation
- Graceful degradation with default values
- Detailed error logging

## Testing

### Run Integration Tests

```bash
cd /mnt/c/Users/HP/ava_olo_project
python test_business_dashboard.py
```

### Manual API Testing

```bash
# Start the API server
python interfaces/api_gateway.py

# Test endpoints
curl http://localhost:8000/api/v1/business/usage
curl http://localhost:8000/api/v1/business/system
curl http://localhost:8000/api/v1/business/insights
curl http://localhost:8000/api/v1/business/projections
curl http://localhost:8000/api/v1/business/summary
```

## Monitoring and Alerting

### Health Checks

The system includes automated health monitoring:
- Database connectivity
- Query performance
- Error rate thresholds
- Response time monitoring

### Metrics Collection

All operations are logged for:
- Performance analysis
- Usage pattern identification
- Error tracking
- Business intelligence

## Security

### Data Protection

- No sensitive farmer data exposed in logs
- Aggregated metrics only
- Secure database connections
- Input validation on all endpoints

### Access Control

- API rate limiting (recommended)
- Authentication integration points
- Role-based access control ready

## Deployment

### Requirements

- Python 3.8+
- PostgreSQL database
- FastAPI framework
- SQLAlchemy ORM

### Environment Variables

```bash
DATABASE_URL=postgresql://user:pass@localhost/ava_olo
LOG_LEVEL=INFO
```

### Production Considerations

1. **Database Optimization**
   - Regular index maintenance
   - Query performance monitoring
   - Connection pooling

2. **Caching**
   - Redis for frequently accessed metrics
   - Cache invalidation strategies

3. **Monitoring**
   - Prometheus metrics integration
   - Grafana dashboards
   - Alert configuration

## Roadmap

### Phase 1 (Current)
- ✅ Core analytics engine
- ✅ REST API endpoints
- ✅ Database schema
- ✅ Integration tests

### Phase 2 (Next)
- [ ] Frontend dashboard components
- [ ] Real-time metric updates
- [ ] Advanced visualizations
- [ ] Email/SMS alerts

### Phase 3 (Future)
- [ ] Machine learning predictions
- [ ] Comparative analytics
- [ ] Export capabilities
- [ ] Custom report builder

## Support

For issues and questions:
1. Check the integration tests
2. Review API documentation
3. Examine database logs
4. Verify module independence

## License

Part of the AVA OLO Croatian Agricultural Assistant project.