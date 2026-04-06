from fastapi import FastAPI, HTTPException
from datetime import datetime
import requests
import uvicorn
import os
 
app = FastAPI(title="Sentinel Racing API Gateway")
 
# Use actual service URLs
SCRAPING_URL = "https://sentinel-scraping-service-tgo3qpmhda-df.a.run.app"
AI_URL = "https://sentinel-ai-service-tgo3qpmhda-df.a.run.app"
 
@app.get("/")
async def root():
    return {
        "message": "Sentinel Racing API Gateway",
        "status": "operational",
        "services": ["scraping", "ai"],
        "version": "1.0.0",
        "scraping_url": SCRAPING_URL,
        "ai_url": AI_URL,
        "timestamp": datetime.now()
    }
 
@app.get("/health")
async def health_check():
    try:
        scraping_health = requests.get(f"{SCRAPING_URL}/health", timeout=10)
        ai_health = requests.get(f"{AI_URL}/health", timeout=10)
        
        return {
            "status": "healthy",
            "services": {
                "scraping": {
                    "status": "healthy" if scraping_health.status_code == 200 else "unhealthy",
                    "response_time": scraping_health.elapsed.total_seconds() if scraping_health.status_code == 200 else None
                },
                "ai": {
                    "status": "healthy" if ai_health.status_code == 200 else "unhealthy",
                    "response_time": ai_health.elapsed.total_seconds() if ai_health.status_code == 200 else None
                }
            },
            "timestamp": datetime.now()
        }
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e),
            "timestamp": datetime.now()
        }
 
@app.post("/scrape/race-cards")
async def scrape_race_cards():
    """Proxy to scraping service"""
    try:
        response = requests.post(f"{SCRAPING_URL}/scrape/race-cards", timeout=30)
        response.raise_for_status()
        return {
            "data": response.json(),
            "service": "scraping",
            "timestamp": datetime.now()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Scraping service unavailable: {e}")
 
@app.post("/analyze/weather")
async def analyze_weather():
    """Proxy to AI service"""
    try:
        response = requests.post(f"{AI_URL}/analyze/weather", timeout=30)
        response.raise_for_status()
        return {
            "data": response.json(),
            "service": "ai",
            "timestamp": datetime.now()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI service unavailable: {e}")
 
@app.post("/predict/race")
async def predict_race():
    """Proxy to AI service"""
    try:
        response = requests.post(f"{AI_URL}/predict/race", timeout=30)
        response.raise_for_status()
        return {
            "data": response.json(),
            "service": "ai",
            "timestamp": datetime.now()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI service unavailable: {e}")
 
@app.post("/recommend/betting")
async def get_betting_recommendation():
    """Proxy to AI service"""
    try:
        response = requests.post(f"{AI_URL}/recommend/betting", timeout=30)
        response.raise_for_status()
        return {
            "data": response.json(),
            "service": "ai",
            "timestamp": datetime.now()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI service unavailable: {e}")
 
@app.get("/system/status")
async def system_status():
    """Complete system status"""
    try:
        # Get service health
        scraping_health = requests.get(f"{SCRAPING_URL}/health", timeout=10)
        ai_health = requests.get(f"{AI_URL}/health", timeout=10)
        
        # Test BigQuery
        bigquery_test = requests.get(f"{SCRAPING_URL}/test/bigquery", timeout=10)
        
        return {
            "system": "operational",
            "services": {
                "api_gateway": {"status": "healthy"},
                "scraping": {
                    "status": "healthy" if scraping_health.status_code == 200 else "unhealthy",
                    "bigquery": "connected" if bigquery_test.status_code == 200 else "disconnected"
                },
                "ai": {
                    "status": "healthy" if ai_health.status_code == 200 else "unhealthy",
                    "gemini": "connected" if ai_health.status_code == 200 else "disconnected"
                }
            },
            "capabilities": [
                "race_data_scraping",
                "weather_analysis", 
                "race_prediction",
                "betting_recommendations"
            ],
            "timestamp": datetime.now()
        }
    except Exception as e:
        return {
            "system": "degraded",
            "error": str(e),
            "timestamp": datetime.now()
        }
 
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
