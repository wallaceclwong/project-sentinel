#!/usr/bin/env python3
"""
PROJECT SENTINEL - Gemini Pro Reasoning Service
GCP Cloud Run service in Hong Kong region
Processes weather deltas and validates trades against Polymarket sentiment
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import json

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
from google.cloud import aiplatform

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Sentinel Reasoning Service",
    description="Gemini Pro powered weather trade validation",
    version="1.0.0"
)

# CORS middleware for Tailscale bridge
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Pydantic models
class WeatherData(BaseModel):
    max_delta: float
    min_delta: float
    mean_delta: float
    std_delta: float
    region: str
    confidence_score: float
    impact_score: float

class MarketSentiment(BaseModel):
    polymarket_volume: float
    price_movement: float
    social_sentiment: float

class TradeValidationRequest(BaseModel):
    timestamp: str
    weather_data: WeatherData
    market_sentiment: MarketSentiment
    request_type: str = "trade_validation"

class TradeSignal(BaseModel):
    timestamp: str
    action: str  # BUY, SELL, HOLD
    confidence: float
    reasoning: str
    market_contract: str
    weather_impact_score: float

# Initialize Gemini Pro
try:
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-pro')
    logger.info("✓ Gemini Pro initialized")
except Exception as e:
    logger.error(f"Failed to initialize Gemini Pro: {e}")
    model = None

class GeminiReasoningEngine:
    """Gemini Pro powered reasoning engine for trade validation"""
    
    def __init__(self):
        self.model = model
        self.reasoning_prompt_template = """
You are an expert weather derivatives trading analyst. Analyze the following data and provide a trade recommendation.

WEATHER DATA:
- Region: {region}
- Max Temperature Delta: {max_delta}°C
- Min Temperature Delta: {min_delta}°C
- Mean Temperature Delta: {mean_delta}°C
- Standard Deviation: {std_delta}°C
- Ensemble Confidence: {confidence_score:.2f}
- Weather Impact Score: {impact_score:.2f}

MARKET SENTIMENT:
- Polymarket Volume: ${polymarket_volume:,.0f}
- Price Movement: {price_movement:.2%}
- Social Sentiment Score: {social_sentiment:.2f}

ANALYSIS REQUIREMENTS:
1. Assess weather anomaly significance (scale: extreme, high, moderate, low)
2. Evaluate market sentiment alignment with weather data
3. Consider historical weather-market correlations
4. Factor in ensemble model confidence

RESPONSE FORMAT (JSON only):
{{
    "action": "BUY|SELL|HOLD",
    "confidence": 0.00-1.00,
    "reasoning": "Brief analysis explaining the decision",
    "market_contract": "Weather contract identifier",
    "weather_impact_score": 0.00-1.00
}}

Provide only the JSON response, no additional text.
"""
    
    async def validate_trade(self, request: TradeValidationRequest) -> Optional[TradeSignal]:
        """Validate trade using Gemini Pro reasoning"""
        if not self.model:
            raise HTTPException(status_code=503, detail="Gemini Pro not available")
        
        try:
            # Format prompt with request data
            prompt = self.reasoning_prompt_template.format(
                region=request.weather_data.region,
                max_delta=request.weather_data.max_delta,
                min_delta=request.weather_data.min_delta,
                mean_delta=request.weather_data.mean_delta,
                std_delta=request.weather_data.std_delta,
                confidence_score=request.weather_data.confidence_score,
                impact_score=request.weather_data.impact_score,
                polymarket_volume=request.market_sentiment.polymarket_volume,
                price_movement=request.market_sentiment.price_movement,
                social_sentiment=request.market_sentiment.social_sentiment
            )
            
            logger.info(f"Sending trade validation request to Gemini Pro")
            
            # Generate response
            response = await asyncio.to_thread(
                self.model.generate_content, prompt
            )
            
            # Parse JSON response
            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()
            
            result = json.loads(response_text)
            
            # Validate response structure
            if not all(key in result for key in ["action", "confidence", "reasoning", "market_contract", "weather_impact_score"]):
                raise ValueError("Invalid response structure from Gemini Pro")
            
            # Validate action
            if result["action"] not in ["BUY", "SELL", "HOLD"]:
                raise ValueError(f"Invalid action: {result['action']}")
            
            # Validate confidence
            if not (0 <= result["confidence"] <= 1):
                raise ValueError(f"Invalid confidence: {result['confidence']}")
            
            trade_signal = TradeSignal(
                timestamp=request.timestamp,
                action=result["action"],
                confidence=result["confidence"],
                reasoning=result["reasoning"],
                market_contract=result["market_contract"],
                weather_impact_score=result["weather_impact_score"]
            )
            
            logger.info(f"Trade validation completed: {trade_signal.action} "
                       f"(confidence: {trade_signal.confidence:.2f})")
            
            return trade_signal
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini Pro response: {e}")
            raise HTTPException(status_code=500, detail="Invalid response from reasoning engine")
        except Exception as e:
            logger.error(f"Trade validation failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

# Initialize reasoning engine
reasoning_engine = GeminiReasoningEngine()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "gemini_pro_available": model is not None
    }

@app.post("/validate-trade", response_model=TradeSignal)
async def validate_trade(request: TradeValidationRequest):
    """Validate trade using weather delta and market sentiment"""
    try:
        # Validate request timestamp
        try:
            datetime.fromisoformat(request.timestamp.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid timestamp format")
        
        # Validate weather impact score
        if not (0 <= request.weather_data.impact_score <= 1):
            raise HTTPException(status_code=400, detail="Invalid weather impact score")
        
        # Process trade validation
        trade_signal = await reasoning_engine.validate_trade(request)
        
        return trade_signal
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in trade validation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Sentinel Reasoning Service",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

# Cloud Run startup
if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
