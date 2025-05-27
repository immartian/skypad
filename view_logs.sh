#!/bin/bash
# Script to view logs for the skypad-ai Cloud Run service

PROJECT_ID="sage-striker-294302"
SERVICE_NAME="skypad-ai"
REGION="us-central1"
LIMIT=100 # Number of log entries to fetch

echo "Fetching last $LIMIT log entries for service '$SERVICE_NAME' in region '$REGION'..."

# Changed to use 'gcloud run services logs read' as suggested by gcloud error.
# Note: This command fetches recent logs. The previous custom table formatting 
# and specific time filter (e.g., last 1 hour) are not directly supported here.
# For advanced filtering or formatting, you might need to use 'gcloud logs read' 
# (if the original issue with it is resolved) or the Google Cloud Console.
gcloud run services logs read "${SERVICE_NAME}" \\
  --region "${REGION}" \\
  --project "${PROJECT_ID}" \\
  --limit "${LIMIT}"

echo ""
echo "To see logs for a specific revision, use the --revision flag with 'gcloud run services logs read',"
echo "for example: --revision ${SERVICE_NAME}-XXXXX-XXX"
echo "Replace XXXXX-XXX with the actual revision suffix (e.g., 00002-t5p from your list)."
echo ""
echo "If you see errors related to container startup, they will appear here."
echo "Look for messages indicating crashes, port issues, or health check failures."