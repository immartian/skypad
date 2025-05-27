#!/bin/bash
# Script to view logs for the skypad-ai Cloud Run service

PROJECT_ID="sage-striker-294302"
SERVICE_NAME="skypad-ai"
REGION="us-central1"
LIMIT=100 # Number of log entries to fetch

echo "Fetching last $LIMIT log entries for service '$SERVICE_NAME' in region '$REGION'..."

gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=${SERVICE_NAME} AND resource.labels.location=${REGION}" \
  --project="${PROJECT_ID}" \
  --limit="${LIMIT}" \
  --format="table(timestamp,logName,severity,textPayload)" \
  --filter="timestamp>=-1h" # Show logs from the last hour, adjust as needed

echo ""
echo "To see logs for a specific revision, you can add:"
echo "AND resource.labels.revision_name=${SERVICE_NAME}-XXXXX-XXX"
echo "Replace XXXXX-XXX with the revision suffix."
echo ""
echo "If you see errors related to container startup, they will appear here."
echo "Look for messages indicating crashes, port issues, or health check failures."