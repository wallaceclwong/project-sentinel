# WeatherNext 2 Access Guide

## 🎯 Recommended Path: Earth Engine (Free)

### Step 1: Fill Out Data Request Form
**URL**: https://docs.google.com/forms/d/e/1FAIpQLSeCf1JY8G78UDWzbm0ly9kJxfSjUIJT5WyMR_HiNqCm-IHIBg/viewform

**What to Request:**
- Project: PROJECT SENTINEL
- Use Case: Weather trading system
- Data Needed: WeatherNext 2 Forecasts
- Regions: Tokyo, Seoul, London
- Timeline: Immediate

### Step 2: Set Up Google Cloud Project
1. Go to: https://console.cloud.google.com/
2. Create new project (or use existing: project-sentinel-2026)
3. Enable Earth Engine API
4. Set up authentication

### Step 3: Access Dataset
**Dataset ID**: `projects/gcp-public-data-weathernext/assets/weathernext_2_0_0`

**Sample Code**:
```python
import ee
import pandas as pd

# Initialize Earth Engine
ee.Initialize()

# Access WeatherNext 2 data
weathernext2 = ee.ImageCollection('projects/gcp-public-data-weathernext/assets/weathernext_2_0_0')

# Filter for Tokyo region
tokyo = ee.Geometry.Rectangle([139.6, 35.5, 139.8, 35.8])
tokyo_forecasts = weathernext2.filterBounds(tokyo)

# Get ensemble data
ensemble_data = tokyo_forecasts.select('temperature_ensemble').getInfo()
```

## 🚀 Alternative Path: Vertex AI (Paid)

### Step 1: Apply for Early Access
**URL**: https://docs.google.com/forms/d/e/1FAIpQLSee8cooW4X30MAjZxSt7DbEcgyk3XpbOYFAxz7tDYEQvbuQ8w/viewform

### Step 2: Set Up Vertex AI
1. Enable Vertex AI API
2. Set up billing (required)
3. Deploy WeatherNext 2 model
4. Use Colab notebook for inference

### Step 3: Real-time API Access
```python
from vertexai.preview.model_garden import ModelGarden

# Deploy WeatherNext 2
model = ModelGarden.get_model("weather-next-v2")
endpoint = model.deploy()

# Generate forecasts
forecast = endpoint.predict(
    location="Tokyo",
    lead_time_hours=168,
    ensemble_members=31
)
```

## 💡 Recommendation

**Start with Earth Engine** because:
- ✅ Free access to ensemble data
- ✅ No billing required
- ✅ Perfect for backtesting
- ✅ Can upgrade to Vertex AI later

**Upgrade to Vertex AI** when:
- You need real-time forecasts
- System is profitable
- Want custom inference

## 🎯 Next Steps

1. **Fill out Earth Engine form** (5 minutes)
2. **Wait for approval** (1-3 days)
3. **Test integration** with our code
4. **Start enhanced trading**

## 📞 Support

- Google Earth Engine Docs: https://developers.google.com/earth-engine
- WeatherNext 2 Guide: https://storage.googleapis.com/weathernext-public/colabs/WeatherNext_2_Starter_Guide_Earth_Engine.ipynb
- Our Integration: Already built and ready
