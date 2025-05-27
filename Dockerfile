# Stage 1: Build React Frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app # Initial WORKDIR /app

# Copy the entire frontend directory from the build context
# to /app/frontend/ in the image.
COPY frontend /app/frontend/

# Verify the contents of /app/frontend/ after copy
RUN echo "Contents of /app/frontend/ in the image:" && ls -la /app/frontend/ && echo "--- End of /app/frontend/ listing ---"

# Now, set the WORKDIR to where the frontend app files are
WORKDIR /app/frontend

# Install a placeholder frontend in case the build fails
# (we'll try to build the real frontend first)
# This will create placeholder-package.json in /app/frontend
RUN echo '{"name":"skypad-placeholder","scripts":{"build":"mkdir -p dist && echo \\"<!DOCTYPE html><html><head><title>Skypad AI</title></head><body><h1>Skypad AI</h1><p>Frontend build placeholder - check deployment logs.</p></body></html>\\" > dist/index.html"}}' > placeholder-package.json

# The individual COPY lines for frontend/* are no longer needed here
# as the entire directory has been copied.

# Debug what files we have in the current WORKDIR (/app/frontend)
RUN echo "Current WORKDIR (/app/frontend) contents:" && ls -la ./

# Install dependencies with more logging
# npm install will look for package.json in the current WORKDIR (/app/frontend)
RUN npm install || (echo "Failed to install dependencies - falling back to placeholder" && cp placeholder-package.json package.json)

# Build with more detailed error reporting
RUN npm run build || (echo "Build failed with exit code $? - using placeholder frontend" && npm --package=placeholder-package.json run build)

# Verify what was built
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
