from fastapi import FastAPI, HTTPException
from datetime import datetime
from google.cloud import bigquery
import uvicorn
import os
 
app = FastAPI(title="Sentinel Racing Scraping Service")
 
# Initialize BigQuery client
try:
    bigquery_client = bigquery.Client(project='project-sentinel-2026')
    BIGQUERY_AVAILABLE = True
except Exception as e:
    print(f"BigQuery not available: {e}")
    BIGQUERY_AVAILABLE = False
 
@app.get("/")
async def root():
    return {
        "message": "Sentinel Racing Scraping Service",
        "status": "operational",
        "bigquery": BIGQUERY_AVAILABLE,
        "timestamp": datetime.now()
    }
 
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "scraping",
        "bigquery": BIGQUERY_AVAILABLE,
        "timestamp": datetime.now()
    }
 
@app.post("/scrape/race-cards")
async def scrape_race_cards():
    """Mock scraping with BigQuery storage"""
    race_data = [{
        "id": 1,
        "venue": "Sha Tin",
        "distance": 1200,
        "race_class": "Class 1",
        "race_date": "2026-03-16",
        "scraped_at": datetime.now().isoformat()
    }]
    
    # Save to BigQuery if available
    if BIGQUERY_AVAILABLE:
        try:
            table_ref = bigquery_client.dataset('sentinel_racing_data').table('race_cards')
            errors = bigquery_client.insert_rows_json(table_ref, race_data)
            if errors:
                print(f"BigQuery errors: {errors}")
            else:
                print(f"Successfully inserted {len(race_data)} records")
        except Exception as e:
            print(f"BigQuery insert error: {e}")
    
    return race_data
 
@app.get("/test/bigquery")
async def test_bigquery():
    """Test BigQuery connection"""
    if not BIGQUERY_AVAILABLE:
        raise HTTPException(status_code=503, detail="BigQuery not available")
    
    try:
        # Test query
        query = "SELECT COUNT(*) as total FROM `project-sentinel-2026.sentinel_racing_data.race_cards`"
        query_job = bigquery_client.query(query)
        results = list(query_job.result())
        
        return {
            "bigquery_status": "connected",
            "total_records": results[0].total if results else 0,
            "timestamp": datetime.now()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"BigQuery error: {e}")
 
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
