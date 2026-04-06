
#!/bin/bash
# Sentinel-Racing AI - Google Cloud Run Deployment

set -e

echo "🚀 Deploying Sentinel-Racing AI to Google Cloud Run..."

# Set project
PROJECT_ID="sentinel-racing-ai"
REGION="us-central1"
SERVICE_NAME="sentinel-racing-ai"

echo "📋 Configuration:"
echo "   Project: $PROJECT_ID"
echo "   Region: $REGION"
echo "   Service: $SERVICE_NAME"

# Build and push Docker image
echo "🔧 Building Docker image..."
docker build -t gcr.io/$PROJECT_ID/$SERVICE_NAME:latest .

echo "📤 Pushing to Google Container Registry..."
docker push gcr.io/$PROJECT_ID/$SERVICE_NAME:latest

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME:latest \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --min-instances 1 \
    --max-instances 10 \
    --set-env-vars REDIS_URL=redis://10.0.0.1:6379 \
    --set-env-vars ENVIRONMENT=production

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region $REGION \
    --format='value(status.url)')

echo "✅ Deployment complete!"
echo "🌐 Service URL: $SERVICE_URL"
echo "🔍 Health check: $SERVICE_URL/health"
