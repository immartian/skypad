#!/bin/bash
# Script to build and deploy to Google Cloud Run

# Configuration
PROJECT_ID="sage-striker-294302"  # Replace with your GCP project ID
IMAGE_NAME="skypad-ai-app"
REGION="us-central1"  # Change to your preferred region

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
  echo "Building Docker image..."
  docker build -t $IMAGE_NAME .

  # Tag the image for Google Container Registry
  echo "Tagging image for GCR..."
  docker tag $IMAGE_NAME gcr.io/$PROJECT_ID/$IMAGE_NAME

  # Push to Container Registry
  echo "Pushing image to Container Registry..."
  docker push gcr.io/$PROJECT_ID/$IMAGE_NAME
else
  echo "Skipping build and push steps..."
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
echo "Deploying to Cloud Run with environment variables..."
gcloud run deploy skypad-ai \
  --image gcr.io/$PROJECT_ID/$IMAGE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 4Gi \
  --set-env-vars="OPENAI_API_KEY=$OPENAI_API_KEY"

# Upload Google credentials to Cloud Run
GOOGLE_CREDS_FILE="sage-striker-294302-b248a695e8e5.json"
if [ -f "$GOOGLE_CREDS_FILE" ]; then
  echo "Setting up Google credentials..."
  
  # Create a secret for Google credentials
  echo "Creating a secret for Google credentials..."
  gcloud secrets create skypad-google-creds --data-file="$GOOGLE_CREDS_FILE" --replication-policy="automatic" || true
  
  # Grant access to the Cloud Run service account
  SERVICE_ACCOUNT=$(gcloud run services describe skypad-ai --region $REGION --format='value(spec.template.spec.serviceAccountName)')
  if [ -z "$SERVICE_ACCOUNT" ]; then
    SERVICE_ACCOUNT=$(gcloud iam service-accounts list --filter="displayName:Cloud Run Service Agent" --format="value(email)" | head -1)
  fi
  
  echo "Granting access to service account: $SERVICE_ACCOUNT"
  gcloud secrets add-iam-policy-binding skypad-google-creds \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor" || true
    
  # Update the service to use the secret
  gcloud run services update skypad-ai \
    --region $REGION \
    --update-secrets=GOOGLE_APPLICATION_CREDENTIALS=skypad-google-creds:latest || true
    
  echo "Google credentials configured."
else
  echo "Warning: Google credentials file not found."
fi

echo "Deployment complete!"
echo "Visit the service URL above to access your app"
