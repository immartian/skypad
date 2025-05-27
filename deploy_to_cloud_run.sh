#!/bin/bash
set -euo pipefail # Exit on error, unset variable, or pipe failure

# Script to build and deploy to Google Cloud Run

# Configuration
PROJECT_ID="sage-striker-294302"  # Replace with your GCP project ID
IMAGE_NAME="skypad-ai-app"
REGION="us-central1"  # Change to your preferred region
TIMESTAMP=$(date +%Y%m%d%H%M%S) # Generate a unique timestamp for the image tag

# Command line arguments
SKIP_AUTH=false
SKIP_BUILD=false

# Process command line arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --skip-auth)
      SKIP_AUTH=true
      shift
      ;;
    --skip-build)
      SKIP_BUILD=true
      shift
      ;;
    *)
      echo "Unknown option: $key"
      echo "Usage: $0 [--skip-auth] [--skip-build]"
      exit 1
      ;;
  esac
done

# Check if we're already authenticated
if [ "$SKIP_AUTH" = false ]; then
  AUTHENTICATED=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null)
  if [ -z "$AUTHENTICATED" ]; then
    echo "Authenticating with Google Cloud..."
    gcloud auth login
  else
    echo "Already authenticated as: $AUTHENTICATED"
  fi
  
  # Set project
  gcloud config set project $PROJECT_ID
  
  # Configure Docker to use gcloud credentials
  echo "Configuring Docker authentication..."
  gcloud auth configure-docker
fi

# Build and push docker image if not skipped
if [ "$SKIP_BUILD" = false ]; then
  # Build the docker image
  echo "Building Docker image (forcing no-cache to ensure fresh build)..."
  docker build --no-cache -t $IMAGE_NAME .
  
  # Check if build was successful
  if [ $? -ne 0 ]; then
    echo "Error: Docker build failed. Please check the build logs for details."
    exit 1
  fi

  # Display build information for debugging
  echo "Docker image built successfully. Info:"
  docker inspect $IMAGE_NAME --format='{{.Config.Env}}'

  # Tag the image for Google Container Registry with a unique timestamp
  echo "Tagging image for GCR with unique tag: gcr.io/$PROJECT_ID/$IMAGE_NAME:$TIMESTAMP"
  docker tag $IMAGE_NAME gcr.io/$PROJECT_ID/$IMAGE_NAME:$TIMESTAMP
  # Also tag with latest for convenience, though deployment will use the timestamped tag
  docker tag $IMAGE_NAME gcr.io/$PROJECT_ID/$IMAGE_NAME:latest

  # Push to Container Registry
  echo "Pushing timestamped image to Container Registry..."
  docker push gcr.io/$PROJECT_ID/$IMAGE_NAME:$TIMESTAMP
  echo "Pushing latest tag to Container Registry..."
  docker push gcr.io/$PROJECT_ID/$IMAGE_NAME:latest
else
  echo "Skipping build and push steps..."
  # When skipping build, ensure we have a TIMESTAMP to use for deployment
  LATEST_IMAGE=$(gcloud container images list-tags gcr.io/$PROJECT_ID/$IMAGE_NAME --limit=1 --format='value(tags)')
  if [ -n "$LATEST_IMAGE" ]; then
    TIMESTAMP=$(echo $LATEST_IMAGE | cut -d ',' -f1)
    echo "Using latest image tag from GCR: $TIMESTAMP"
  fi
fi

# Read environment variables from .env file
echo "Reading environment variables from .env file..."
if [ -f .env ]; then
  # Extract OpenAI API key
  OPENAI_API_KEY=$(grep -o 'OPENAI_API_KEY=.*' .env | cut -d '=' -f2)
  
  # Default values if not found
  if [ -z "$OPENAI_API_KEY" ]; then
    echo "Warning: OPENAI_API_KEY not found in .env file."
    OPENAI_API_KEY=""
  fi
  
  echo "Environment variables loaded successfully."
else
  echo "Warning: .env file not found. Deploying without environment variables."
  OPENAI_API_KEY=""
fi

# Deploy to Cloud Run with environment variables
echo "Deploying to Cloud Run with environment variables using image gcr.io/$PROJECT_ID/$IMAGE_NAME:$TIMESTAMP"
gcloud run deploy skypad-ai \
  --image gcr.io/$PROJECT_ID/$IMAGE_NAME:$TIMESTAMP \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 2Gi \
  --timeout=300 \
  --set-env-vars="OPENAI_API_KEY=$OPENAI_API_KEY"

# Check if deployment was successful
if [ $? -ne 0 ]; then
  echo "Error: Deployment to Cloud Run failed."
  exit 1
fi

echo "Deployment was successful! Getting service URL..."
SERVICE_URL=$(gcloud run services describe skypad-ai --platform managed --region $REGION --format="value(status.url)")
echo "Service is available at: $SERVICE_URL"

# Upload Google credentials to Cloud Run
GOOGLE_CREDS_FILE="sage-striker-294302-b248a695e8e5.json"
if [ -f "$GOOGLE_CREDS_FILE" ]; then
  echo "Setting up Google credentials..."
  
  # Create a secret for Google credentials
  echo "Creating a secret for Google credentials..."
  gcloud secrets create skypad-google-creds --data-file="$GOOGLE_CREDS_FILE" --replication-policy="automatic" || echo "Secret already exists"
  
  # Grant access to the Cloud Run service account
  echo "Getting service account information..."
  # First try to get the service account from the existing service
  SERVICE_ACCOUNT=$(gcloud run services describe skypad-ai --region $REGION --format='value(spec.template.spec.serviceAccountName)' 2>/dev/null || echo "")
  
  # If the service account is empty, get the default Cloud Run service agent
  if [ -z "$SERVICE_ACCOUNT" ]; then
    PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
    SERVICE_ACCOUNT="$PROJECT_NUMBER-compute@developer.gserviceaccount.com"
    echo "Using default compute service account: $SERVICE_ACCOUNT"
  fi
  
  echo "Granting access to service account: $SERVICE_ACCOUNT"
  gcloud secrets add-iam-policy-binding skypad-google-creds \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor" || echo "Already has access"
    
  # Update the service to use the secret
  echo "Updating service to use the secret..."
  gcloud run services update skypad-ai \
    --region $REGION \
    --update-secrets=GOOGLE_APPLICATION_CREDENTIALS=skypad-google-creds:latest || echo "Failed to update secrets"
    
  echo "Google credentials configured."
else
  echo "Warning: Google credentials file not found."
fi

echo "Deployment complete!"
echo "Visit the service URL above to access your app"
