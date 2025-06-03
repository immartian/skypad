#!/bin/bash

# Skypad Fast Development Runner
# This script runs frontend and backend separately for faster development
# Use this for rapid iteration, use run.sh for production-like testing

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to cleanup background processes
cleanup() {
    print_status "Stopping development servers..."
    jobs -p | xargs -r kill 2>/dev/null || true
    wait 2>/dev/null || true
}

trap cleanup EXIT

# Parse arguments
FRONTEND_ONLY=false
BACKEND_ONLY=false
FRONTEND_PORT=5173
BACKEND_PORT=8080

while [[ $# -gt 0 ]]; do
    case $1 in
        --frontend-only|-f)
            FRONTEND_ONLY=true
            shift
            ;;
        --backend-only|-b)
            BACKEND_ONLY=true
            shift
            ;;
        --frontend-port)
            FRONTEND_PORT="$2"
            shift 2
            ;;
        --backend-port)
            BACKEND_PORT="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --frontend-only, -f    Run only frontend dev server"
            echo "  --backend-only, -b     Run only backend dev server"
            echo "  --frontend-port PORT   Frontend port (default: 5173)"
            echo "  --backend-port PORT    Backend port (default: 8080)"
            echo "  --help, -h            Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

print_status "Starting Skypad fast development environment..."

# Check requirements
if [[ "$FRONTEND_ONLY" != "true" ]]; then
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 is required but not installed"
        exit 1
    fi
    
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 is required but not installed"
        exit 1
    fi
fi

if [[ "$BACKEND_ONLY" != "true" ]]; then
    if ! command -v npm &> /dev/null; then
        print_error "npm is required but not installed"
        exit 1
    fi
fi

# Setup backend
if [[ "$FRONTEND_ONLY" != "true" ]]; then
    print_status "Setting up Python backend..."
    
    # Check if virtual environment exists
    if [[ ! -d "venv" ]]; then
        print_status "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    print_status "Installing Python dependencies..."
    pip install -r requirements.txt >/dev/null 2>&1 || {
        print_warning "Some Python dependencies may have failed to install"
    }
    
    # Check for .env file
    if [[ ! -f .env ]]; then
        print_warning ".env file not found. Creating template..."
        cat > .env << EOF
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_APPLICATION_CREDENTIALS=./sage-striker-294302-b248a695e8e5.json
PORT=$BACKEND_PORT
EOF
        print_warning "Please update .env with your actual API keys"
    fi
fi

# Setup frontend
if [[ "$BACKEND_ONLY" != "true" ]]; then
    print_status "Setting up React frontend..."
    
    cd frontend
    
    # Check if node_modules exists
    if [[ ! -d "node_modules" ]]; then
        print_status "Installing npm dependencies..."
        npm install
    fi
    
    cd ..
fi

# Start servers
if [[ "$FRONTEND_ONLY" == "true" ]]; then
    print_success "Starting frontend development server on port $FRONTEND_PORT..."
    cd frontend
    npm run dev -- --port $FRONTEND_PORT --host 0.0.0.0
    
elif [[ "$BACKEND_ONLY" == "true" ]]; then
    print_success "Starting backend development server on port $BACKEND_PORT..."
    source venv/bin/activate
    uvicorn main:app --reload --host 0.0.0.0 --port $BACKEND_PORT
    
else
    print_success "Starting both frontend and backend servers..."
    
    # Start backend in background
    print_status "Starting backend on port $BACKEND_PORT..."
    source venv/bin/activate
    uvicorn main:app --reload --host 0.0.0.0 --port $BACKEND_PORT &
    BACKEND_PID=$!
    
    # Wait a moment for backend to start
    sleep 2
    
    # Check if backend started successfully
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        print_error "Backend failed to start"
        exit 1
    fi
    
    print_success "Backend started successfully (PID: $BACKEND_PID)"
    
    # Start frontend in foreground
    print_status "Starting frontend on port $FRONTEND_PORT..."
    cd frontend
    
    # Update vite config to proxy to backend
    export VITE_API_URL="http://localhost:$BACKEND_PORT"
    
    npm run dev -- --port $FRONTEND_PORT --host 0.0.0.0
fi
