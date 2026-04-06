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
import time

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai

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

# Usage tracking
api_calls_count = 0
total_tokens_used = 0
start_time = time.time()

# Initialize Gemini Pro
try:
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-2.5-pro')  # Updated to use latest model
    logger.info("✓ Gemini Pro 2.5 initialized")
except Exception as e:
    logger.error(f"Failed to initialize Gemini Pro: {e}")
    model = None

def track_api_usage(prompt: str, response: str, response_time: float):
    """Track API usage for cost monitoring"""
    global api_calls_count, total_tokens_used
    
    # Estimate tokens (rough calculation: 1 token ≈ 4 characters)
    prompt_tokens = len(prompt) // 4
    response_tokens = len(response) // 4
    total_tokens = prompt_tokens + response_tokens
    
    api_calls_count += 1
    total_tokens_used += total_tokens
    
    # Calculate cost (Gemini Pro pricing)
    cost_per_1k_tokens = 0.00025  # $0.00025 per 1K tokens
    cost = (total_tokens / 1000) * cost_per_1k_tokens
    
    logger.info(f"API Usage: Call #{api_calls_count}, {total_tokens} tokens, "
               f"{response_time:.2f}s, ${cost:.6f}")
    
    return {
        "call_number": api_calls_count,
        "tokens_used": total_tokens,
        "response_time": response_time,
        "estimated_cost": cost
    }

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
    
    async def validate_trade(self, weather_data: WeatherData, market_sentiment: MarketSentiment) -> Dict[str, Any]:
        """Validate trade using Gemini Pro reasoning"""
        if not self.model:
            raise HTTPException(status_code=503, detail="Gemini Pro not available")
        
        start_time = time.time()
        
        try:
            # Construct the reasoning prompt
            prompt = self.reasoning_prompt_template.format(
                region=weather_data.region,
                max_delta=weather_data.max_delta,
                min_delta=weather_data.min_delta,
                mean_delta=weather_data.mean_delta,
                std_delta=weather_data.std_delta,
                confidence_score=weather_data.confidence_score,
                impact_score=weather_data.impact_score,
                polymarket_volume=market_sentiment.polymarket_volume,
                price_movement=market_sentiment.price_movement,
                social_sentiment=market_sentiment.social_sentiment
            )
            
            # Generate response
            response = self.model.generate_content(prompt)
            response_time = time.time() - start_time
            
            if not response or not response.text:
                raise HTTPException(status_code=500, detail="No response from Gemini Pro")
            
            # Track usage
            usage_stats = track_api_usage(prompt, response.text, response_time)
            
            # Parse the response
            response_text = response.text.strip()
            
            # Try to extract JSON from the response
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            else:
                json_text = response_text
            
            try:
                trade_decision = json.loads(json_text)
            except json.JSONDecodeError:
                # Fallback: create a basic response from the text
                trade_decision = {
                    "action": "HOLD",
                    "confidence": 0.5,
                    "reasoning": response_text[:200] + "..." if len(response_text) > 200 else response_text,
                    "market_contract": f"Weather_{weather_data.region}",
                    "weather_impact_score": weather_data.impact_score
                }
            
            # Add usage stats to response
            trade_decision["usage_stats"] = usage_stats
            
            logger.info(f"Trade validation completed: {trade_decision.get('action', 'UNKNOWN')} "
                       f"(confidence: {trade_decision.get('confidence', 0):.2f})")
            
            return trade_decision
            
        except Exception as e:
            logger.error(f"Trade validation failed: {e}")
            raise HTTPException(status_code=500, detail=f"Trade validation failed: {str(e)}")

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
        trade_signal = await reasoning_engine.validate_trade(request.weather_data, request.market_sentiment)
        
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

@app.get("/usage")
async def usage_dashboard():
    """Usage and cost monitoring dashboard"""
    uptime = time.time() - start_time
    cost_per_1k_tokens = 0.00025
    
    return {
        "service": "Sentinel Reasoning Service",
        "usage_stats": {
            "total_api_calls": api_calls_count,
            "total_tokens_used": total_tokens_used,
            "uptime_seconds": uptime,
            "avg_calls_per_hour": api_calls_count / (uptime / 3600) if uptime > 0 else 0,
            "estimated_total_cost": (total_tokens_used / 1000) * cost_per_1k_tokens,
            "cost_per_call": ((total_tokens_used / 1000) * cost_per_1k_tokens) / api_calls_count if api_calls_count > 0 else 0
        },
        "model_info": {
            "model_name": "gemini-2.5-pro",
            "cost_per_1k_tokens": cost_per_1k_tokens,
            "available": model is not None
        },
        "limits": {
            "daily_calls_limit": 1000,
            "monthly_budget_usd": 50.0,
            "pro_tier_benefits": "60 requests/minute, 1M context window"
        },
        "timestamp": datetime.now().isoformat()
    }

# Cloud Run startup
if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
