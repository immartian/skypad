# Stage 1: Build React Frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Install a placeholder frontend in case the build fails
# (we'll try to build the real frontend first)
RUN echo '{"name":"skypad-placeholder","scripts":{"build":"mkdir -p dist && echo \"<!DOCTYPE html><html><head><title>Skypad AI</title></head><body><h1>Skypad AI</h1><p>Frontend build placeholder - check deployment logs.</p></body></html>\" > dist/index.html"}}' > placeholder-package.json

# Create directories for frontend files
RUN mkdir -p src public

# Try to copy the frontend files
COPY frontend/package.json ./package.json || cp placeholder-package.json package.json
COPY frontend/package-lock.json* ./package-lock.json* || echo "No package-lock.json found"
COPY frontend/src ./src || echo "No src directory found"
COPY frontend/public ./public || echo "No public directory found" 
COPY frontend/index.html ./index.html || echo "No index.html found"
COPY frontend/vite.config.ts ./vite.config.ts || echo "No vite.config.ts found"
COPY frontend/tsconfig*.json ./ || echo "No tsconfig files found"

# Debug what we have
RUN ls -la

# Try to install dependencies and build
RUN npm install || echo "Failed to install dependencies, will use placeholder"
RUN npm run build || (echo "Build failed, using placeholder frontend" && npm --package=placeholder-package.json run build)

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