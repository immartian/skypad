# Stage 1: Build React Frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Create a valid placeholder package.json for fallback
RUN echo '{"name":"skypad-placeholder","version":"0.0.1","scripts":{"build":"mkdir -p dist && echo \\"<!DOCTYPE html><html><head><title>Skypad AI - Placeholder</title></head><body><h1>Skypad AI - Placeholder</h1><p>Frontend build placeholder - check deployment logs.</p></body></html>\\" > dist/index.html"}}' > placeholder-package.json

# Copy only package.json and package-lock.json first for better Docker cache usage
COPY frontend/package.json frontend/package-lock.json* ./

# Verify that package.json was copied, fallback to placeholder if not
RUN if [ ! -f package.json ]; then \
      echo "WARNING: frontend/package.json not found after COPY. Using placeholder for npm install."; \
      cp placeholder-package.json package.json; \
    else \
      echo "frontend/package.json found. Proceeding with npm install."; \
    fi

# Install dependencies (using real or placeholder package.json)
RUN npm install || (echo "npm install failed. Using placeholder package.json." && cp placeholder-package.json package.json && npm install)

# Copy the rest of the frontend files (excluding package.json to avoid overwriting)
COPY frontend/. ./

# Debug: List contents to see what's available for the build.
RUN echo "Contents of /app/frontend before build:" && ls -la

# Build the frontend application, fallback to placeholder build if it fails
RUN npm run build || (echo "npm run build failed. Falling back to placeholder build." && cp placeholder-package.json package.json && npm run build)

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
COPY --from=frontend-builder /app/frontend/dist /app/static

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
