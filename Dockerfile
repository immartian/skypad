# Stage 1: Build React Frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app

# Copy package files first for better layer caching
COPY frontend/package*.json ./

# Install dependencies
RUN npm install

# Now copy the rest of the frontend files
COPY frontend/ ./

# Debug: Check what files are in the current directory
RUN echo "Files in /app after all copies:" && ls -la
RUN npm install

# Build the frontend application
RUN npm run build

# Verify build output
RUN echo "Build output:" && ls -la dist || echo "No dist directory found"

# Stage 2: Python Backend
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (if any beyond what's already there, though slim is minimal)
# RUN apt-get update && apt-get install -y ... && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application credential files
# Handle .env files - create empty one if doesn't exist to avoid errors
RUN touch /app/.env
# The COPY .env* line was removed as it was causing build errors and is redundant
# given runtime environment variable injection.
# Copy Google credentials file
COPY sage-striker-294302-b248a695e8e5.json /app/google-credentials.json 

# Copy the backend application code
COPY main.py bella_prompt.py utils.py ./ 

# Copy built frontend assets from the frontend-builder stage
COPY --from=frontend-builder /app/dist /app/static

# Add debug information after copying
RUN echo "Static files after copy:" && ls -la /app/static && \
    if [ -f /app/static/index.html ]; then \
      echo "Index.html exists in static directory"; \
      cat /app/static/index.html | grep -o 'src="[^"]*"' || echo "No script src found in index.html"; \
    else \
      echo "Index.html MISSING from static directory"; \
    fi

# Copy the fallback index.html if the build process didn't create one
RUN mkdir -p /app/static && \
    if [ ! -f /app/static/index.html ]; then \
    echo "<!DOCTYPE html><html><head><title>Skypad AI</title></head><body><h1>Skypad AI</h1><p>This is a fallback frontend - check build logs for details.</p></body></html>" > /app/static/index.html; \
    fi

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
# PORT will be provided by Cloud Run at runtime (usually 8080)
# Update this if your application code expects a different path for Google credentials
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/google-credentials.json

# Expose port 8080 - Cloud Run will set PORT env var automatically
EXPOSE 8080

# Command to run the application - use PORT env var which will be set by Cloud Run
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}
