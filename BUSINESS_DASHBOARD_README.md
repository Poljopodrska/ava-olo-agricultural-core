# 📊 AVA OLO Business Dashboard

## Overview
The Business Dashboard provides real-time KPIs and metrics for the agricultural database system. It displays key business metrics, growth trends, and activity streams.

## Features

### 1. **Database Overview**
- Total number of farmers
- Total hectares under management
- Hectare breakdown by crop type:
  - 🌾 Herbal/Arable Crops (wheat, corn, barley, etc.)
  - 🍇 Vineyards (grapes, wine varieties)
  - 🍎 Orchards (apples, pears, cherries, etc.)
  - 🌱 Others (uncategorized crops)

### 2. **Growth Trends**
Tracks metrics over three time periods:
- Last 24 hours
- Last 7 days
- Last 30 days

Metrics tracked:
- New farmers added
- Farmers unsubscribed (if status tracking enabled)
- New hectares added

### 3. **Farmer Growth Chart**
Interactive line chart showing:
- Cumulative farmer count over time
- Daily net acquisition (new farmers - unsubscribed)
- Selectable time periods: 24h, 7d, 30d

### 4. **Activity Stream**
Live feed from `incoming_messages` table showing:
- Recent farmer conversations
- Anonymized farmer names (e.g., "JS." for privacy)
- Message previews (first 50 characters)
- Timestamps

### 5. **Recent Database Changes**
Tracks recent additions and changes:
- New farmers registered
- New tasks created
- Field updates
- Other database activity

## Setup Instructions

### 1. Database Preparation

First, check if you need to add timestamp columns:

```bash
# Run the migration to add created_at columns
psql -U postgres -d farmer_crm -f migrations/add_timestamp_columns.sql
```

### 2. Environment Variables

Ensure these are set (same as main dashboard):
```bash
DB_HOST=your_host
DB_NAME=farmer_crm
DB_USER=postgres
DB_PASSWORD=your_password
DB_PORT=5432
```

### 3. Running the Dashboard

Option 1: Use the launcher script (auto-detects schema):
```bash
python run_business_dashboard.py
```

Option 2: Run directly:
```bash
# For agricultural schema (area_ha, field_crops table)
python business_dashboard_updated.py

# For other schemas
python business_dashboard.py
```

The dashboard runs on port 8004 by default.

### 4. Access the Dashboard

Open your browser to:
```
http://localhost:8004
```

## API Endpoints

The dashboard exposes several API endpoints for integration:

- `GET /api/business/database-overview` - Overview metrics
- `GET /api/business/growth-trends` - Growth trend data
- `GET /api/business/farmer-growth-chart?period=30d` - Chart data
- `GET /api/business/activity-stream?limit=20` - Recent activity
- `GET /api/business/recent-changes?limit=20` - Database changes
- `GET /health` - Health check endpoint

## Features

### Auto-Refresh
The dashboard automatically refreshes every 30 seconds to show real-time data.

### Privacy Compliance
- Farmer names are anonymized in activity streams
- No personal data is exposed in metrics
- Constitutional privacy-first approach

### Performance
- Efficient SQL queries with proper indexing
- Caching of static data
- Minimal database load

## Customization

### Modify Refresh Rate
In the HTML template, change:
```javascript
setInterval(() => {
    window.location.reload();
}, 30000);  // Change 30000 to desired milliseconds
```

### Add New Metrics
1. Add method to `BusinessAnalytics` class
2. Create new API endpoint
3. Update HTML template to display
4. Add to auto-refresh if needed

### Crop Categories
Modify the crop categorization in `get_database_overview()`:
```python
WHEN LOWER(fc.crop_name) SIMILAR TO '%(your|crops|here)%' THEN 'category'
```

## Troubleshooting

### No Data Showing
1. Check database connection
2. Verify tables exist: `farmers`, `fields`, `field_crops`
3. Run migrations if needed
4. Check for data in tables

### Missing Timestamps
Run the migration:
```sql
ALTER TABLE farmers ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();
```

### Port Already in Use
Change port in the main script:
```python
uvicorn.run(app, host="0.0.0.0", port=8005)  # Different port
```

## Docker Deployment

Create a Dockerfile:
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY business_dashboard_updated.py .
COPY templates/ templates/

EXPOSE 8004

CMD ["python", "business_dashboard_updated.py"]
```

## Constitutional Compliance ✅

This dashboard follows all 13 constitutional principles:
1. **Privacy-First**: Anonymized farmer data
2. **Global-Ready**: Works with any crop/country
3. **Error Isolation**: Graceful fallbacks
4. **Farmer-Centric**: Focus on farmer metrics
5. **Simple**: Clean, intuitive interface
6. **Transparent**: Clear data sources
7. **Scalable**: Efficient queries
8. **Sustainable**: Low resource usage
9. **Secure**: Read-only operations
10. **Open Source**: Full code available
11. **LLM-First**: Ready for AI integration
12. **Anti-Monoculture**: Supports diverse crops
13. **Mango Rule**: Works for Bulgarian mango farmers! 🥭