#!/bin/bash

# Simple local development script - NO DOCKER
# Builds frontend and serves everything from FastAPI backend on port 8080

set -e

echo "🚀 Starting Skypad AI - Local Development (Single Port)"
echo "======================================================="

# Kill any existing processes on ports 8080, 8000, and 5173
echo "🧹 Cleaning up existing processes..."
lsof -ti:8080 | xargs kill -9 2>/dev/null || true
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:5173 | xargs kill -9 2>/dev/null || true

# Install frontend dependencies if needed
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd frontend && npm install && cd ..
fi

# Build the React frontend
echo "⚛️  Building React frontend..."
cd frontend && npm run build && cd ..

# Copy built frontend to static directory
echo "📁 Copying frontend build to static directory..."
mkdir -p static
cp -r frontend/dist/* static/

# Ensure lattice directory exists with ontology file
echo "📁 Setting up lattice directory..."
mkdir -p lattice
cp -f frontend/public/skypad_ontology_mvp.jsonld lattice/ 2>/dev/null || true

# Install backend dependencies if needed
if [ ! -d ".venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment and install dependencies
echo "🐍 Installing backend dependencies..."
source .venv/bin/activate
pip install -r requirements.txt

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down..."
    # Kill any remaining processes on our ports
    lsof -ti:8080 | xargs kill -9 2>/dev/null || true
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    lsof -ti:5173 | xargs kill -9 2>/dev/null || true
    echo "✅ Cleanup complete"
    exit 0
}

# Set up signal handling
trap cleanup SIGINT SIGTERM

# Start backend on port 8080 (serves both frontend and API)
echo "🔧 Starting FastAPI backend on port 8080 (serving frontend + API)..."
echo ""
echo "✅ Skypad AI is starting up!"
echo "🌐 Application: http://localhost:8080"
echo "📚 API Docs:    http://localhost:8080/docs"
echo ""
echo "Press Ctrl+C to stop the service"
echo ""

uvicorn main:app --host 0.0.0.0 --port 8080 --reload
