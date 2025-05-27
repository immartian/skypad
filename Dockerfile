# Stage 1: Build React Frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app

# Create a clean workspace
RUN mkdir -p /app/frontend

# Copy frontend files to builder stage
# First just copy package.json files for better caching
COPY frontend/package.json /app/frontend/package.json
COPY frontend/package-lock.json* /app/frontend/

# Switch to frontend working directory
WORKDIR /app/frontend

# Install dependencies
RUN npm install

# Now copy the rest of the frontend files
COPY frontend/src/ /app/frontend/src/
COPY frontend/public/ /app/frontend/public/
COPY frontend/index.html /app/frontend/index.html
COPY frontend/vite.config.ts /app/frontend/vite.config.ts
COPY frontend/tsconfig*.json /app/frontend/

# Log what was copied to debug
RUN ls -la /app/frontend/

# Build frontend application
RUN npm run build || (echo "Build failed, creating fallback frontend" && \
    mkdir -p dist && \
    echo '<!DOCTYPE html><html><head><title>Skypad AI</title></head><body><h1>Skypad AI</h1><p>Full application could not be built. Check deployment logs.</p></body></html>' > dist/index.html)

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
