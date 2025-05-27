# Stage 1: Build React Frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Debug the directory structure to find frontend/package.json
RUN mkdir -p /debug-copy
COPY . /debug-copy
RUN ls -la /debug-copy/frontend || echo "frontend dir not found"
RUN find /debug-copy -name "package.json" || echo "No package.json found"

# Instead of trying to COPY the files directly (which is failing),
# copy them from the already copied directory
RUN cp /debug-copy/frontend/package.json . || echo "Failed to copy package.json"
RUN cp /debug-copy/frontend/package-lock.json . 2>/dev/null || echo "No package-lock.json found"

# Install frontend dependencies
RUN npm install

# Copy the rest of the frontend source code
# Copies contents of <build_context>/frontend/ to <WORKDIR>/
COPY frontend/. .

# Build the frontend application
RUN npm run build

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
ENV PORT=8000
# Update this if your application code expects a different path for Google credentials
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/google-credentials.json 

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
