#!/bin/bash
# Script to build and deploy to Google Cloud Run

# Configuration
PROJECT_ID="sage-striker-294302"  # Replace with your GCP project ID
IMAGE_NAME="skypad-ai-app"
REGION="us-central1"  # Change to your preferred region

# Ensure we're authenticated with Google Cloud
echo "Authenticating with Google Cloud..."
gcloud auth login
gcloud config set project $PROJECT_ID

# Configure Docker to use gcloud credentials
echo "Configuring Docker authentication..."
gcloud auth configure-docker

# Build the docker image
echo "Building Docker image..."
docker build -t $IMAGE_NAME .

# Tag the image for Google Container Registry
echo "Tagging image for GCR..."
docker tag $IMAGE_NAME gcr.io/$PROJECT_ID/$IMAGE_NAME

# Push to Container Registry
echo "Pushing image to Container Registry..."
docker push gcr.io/$PROJECT_ID/$IMAGE_NAME

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy skypad-ai \
  --image gcr.io/$PROJECT_ID/$IMAGE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 2Gi

echo "Deployment complete!"
echo "Visit the service URL above to access your app"
