# Google Maps API Setup for Field Drawing

## 🗺️ Overview
The field drawing feature requires a Google Maps API key to display interactive maps where farmers can draw their field boundaries.

## 🔧 Setup Instructions

### 1. Get Google Maps API Key
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the following APIs:
   - **Maps JavaScript API** (for the map display)
   - **Geometry Library** (for area calculations)

### 2. Create API Key
1. Navigate to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **API Key**
3. Copy the generated API key
4. (Optional but recommended) Restrict the key to your domain

### 3. Add to Environment Variables
Add the API key to your environment variables:

#### For Development (.env file):
```bash
GOOGLE_MAPS_API_KEY=your_api_key_here
```

#### For Production (AWS ECS):
Add the environment variable in your AWS ECS configuration:
```bash
GOOGLE_MAPS_API_KEY=your_api_key_here
```

### 4. Update Template
Replace `YOUR_GOOGLE_MAPS_API_KEY` in the template with your actual API key, or better yet, use environment variable injection:

```html
<script async defer 
    src="https://maps.googleapis.com/maps/api/js?key={{ GOOGLE_MAPS_API_KEY }}&libraries=geometry,drawing&callback=initFieldMap">
</script>
```

## 🚨 Important Security Notes

1. **Restrict API Key Usage**: In Google Cloud Console, restrict your API key to:
   - Specific APIs (Maps JavaScript API, Geometry Library)
   - HTTP referrers (your domain)
   - IP addresses (if applicable)

2. **Never commit API keys to Git**: Always use environment variables

3. **Monitor Usage**: Set up billing alerts and quotas to avoid unexpected charges

## 🎯 Features Enabled

With Google Maps API properly configured, users can:
- ✅ View satellite imagery of their location
- ✅ Draw field boundaries by clicking points
- ✅ Auto-calculate field area in hectares
- ✅ Auto-generate GPS coordinates for field center
- ✅ Edit field shapes by dragging points
- ✅ Save polygon data to database

## 📊 API Usage

The field drawing feature uses:
- **Maps JavaScript API**: For displaying the map
- **Geometry Library**: For calculating area and distances
- **Satellite imagery**: For better field visualization

Typical usage per field drawing session:
- ~1-5 API calls per field
- Minimal data transfer
- No ongoing API calls after field is saved

## 🔍 Troubleshooting

### Common Issues:
1. **Map not loading**: Check if API key is correct and APIs are enabled
2. **"For development purposes only" watermark**: API key restrictions too strict
3. **Area calculation errors**: Geometry library not loaded properly

### Debug Steps:
1. Check browser console for API errors
2. Verify API key in environment variables
3. Confirm APIs are enabled in Google Cloud Console
4. Test with a simple HTML file first

## 🌍 Constitutional Compliance

This feature works worldwide:
- ✅ Supports any country/region
- ✅ Multiple map types (satellite, terrain, hybrid)
- ✅ Automatic geolocation detection
- ✅ Works for any crop type
- ✅ Accessible design for older farmers

## 💰 Cost Considerations

Google Maps API pricing (as of 2024):
- Maps JavaScript API: $7 per 1,000 loads
- Geometry Library: Usually included with Maps JavaScript API
- First $200/month is free (Google Cloud credits)

For a typical farm management system:
- Small farms: Likely within free tier
- Medium farms: $5-20/month
- Large enterprises: $50-200/month

## 📈 Future Enhancements

With polygon data stored, future features can include:
- Crop rotation planning
- Irrigation zone mapping
- Yield mapping
- Weather overlay
- Soil analysis integration
- Satellite imagery comparison