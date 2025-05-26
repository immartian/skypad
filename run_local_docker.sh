#!/bin/bash
# Script to test the Docker image locally with .env variables

# Build the Docker image
echo "Building Docker image..."
docker build -t skypad-local .

# Run the container with environment variables from .env
echo "Running container with .env variables..."

# Check if .env file exists
if [ -f .env ]; then
  echo "Using variables from .env file."
  docker run -p 8501:8501 --env-file .env skypad-local
else
  echo "Error: .env file not found."
  exit 1
fi
