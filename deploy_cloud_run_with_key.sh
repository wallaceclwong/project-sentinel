#!/bin/bash
# PROJECT SENTINEL - Cloud Run Deployment Script with API Key
# Phase 3: Deploy Gemini Pro Reasoning Service to GCP Hong Kong

set -e

# Configuration
PROJECT_ID="your-gcp-project-id"
SERVICE_NAME="sentinel-reasoning"
REGION="asia-east2"  # Hong Kong
GEMINI_API_KEY="REDACTED_API_KEY"

echo "🚀 Deploying PROJECT SENTINEL - Gemini Pro Reasoning Service"
echo "Region: $REGION"
echo "Service: $SERVICE_NAME"
echo "Model: gemini-2.5-pro"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Please install Google Cloud SDK."
    exit 1
fi

# Set project
echo "📋 Setting GCP project..."
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable run.googleapis.com
gcloud services enable aiplatform.googleapis.com

# Build and deploy Cloud Run service
echo "🏗️ Building container..."
cd cloud_run

# Build the image
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME --region $REGION .

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --timeout 30s \
    --set-env-vars GEMINI_API_KEY=$GEMINI_API_KEY \
    --set-env-vars MODEL_NAME=gemini-2.5-pro \
    --max-instances 10

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region $REGION \
    --format 'value(status.url)')

echo "✅ Deployment complete!"
echo "🔗 Service URL: $SERVICE_URL"
echo "🧪 Testing health endpoint..."

# Test health endpoint
curl -s "$SERVICE_URL/health" | jq .

echo "📝 Update your config.yaml with:"
echo "gcp_bridge:"
echo "  cloud_run_url: \"$SERVICE_URL\""

echo ""
echo "🎯 PROJECT SENTINEL Phase 3 deployment complete!"
echo "   Your Gemini Pro 2.5 reasoning service is now live in Hong Kong."
