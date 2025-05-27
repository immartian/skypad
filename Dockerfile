# Stage 1: Build React Frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app

# First copy EVERYTHING to make sure we have the frontend files
COPY . /app/

# Debug what we got
RUN ls -la /app/
RUN ls -la /app/frontend || echo "Frontend dir not found"
RUN find /app -name "package.json" || echo "No package.json found"

WORKDIR /app/frontend

# Install dependencies and build
RUN if [ -f "package.json" ]; then \
      npm install && npm run build; \
    else \
      echo "Creating placeholder frontend" && \
      mkdir -p dist && \
      echo '<!DOCTYPE html><html><head><title>Skypad AI</title></head><body><h1>Skypad AI</h1><p>Frontend build placeholder - check deployment logs.</p></body></html>' > dist/index.html; \
    fi

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
# Don't copy .env file - instead we'll use runtime environment variables
# COPY .env .
# Copy Google credentials file
COPY sage-striker-294302-b248a695e8e5.json /app/google-credentials.json 

# Copy the backend application code
COPY main.py bella_prompt.py utils.py ./ 

# Copy built frontend assets from the frontend-builder stage
COPY --from=frontend-builder /app/frontend/dist /app/static

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
# PORT will be provided by Cloud Run at runtime (usually 8080)
ENV PORT=8080
# Update this if your application code expects a different path for Google credentials
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/google-credentials.json 

# Expose the port the app runs on (using PORT env var)
EXPOSE ${PORT}

# Command to run the application (using the PORT env var)
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT}
