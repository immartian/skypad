# Skypad MVP3 - Docker Setup Guide

This document describes how to run Skypad using Docker for development and production environments.

## Prerequisites

- Docker (version 20.10 or higher)
- Docker Compose (version 2.0 or higher)

## Quick Start

### Development Environment

The easiest way to get started is using the development script:

```bash
# Start development environment (frontend + backend)
./docker-dev.sh dev

# View logs
./docker-dev.sh logs

# Stop services
./docker-dev.sh stop
```

### Manual Development Setup

```bash
# Start development environment
docker-compose up frontend-dev backend --build -d

# Frontend will be available at: http://localhost:5173
# Backend API will be available at: http://localhost:8080
```

### Production Build

```bash
# Build and run production version
./docker-dev.sh prod

# Or manually:
docker-compose --profile production up app --build -d

# Application will be available at: http://localhost:8080
```

## Development Script Commands

The `docker-dev.sh` script provides convenient commands for managing the application:

| Command | Description |
|---------|-------------|
| `dev` | Start development environment (frontend + backend) |
| `build` | Build production Docker image |
| `prod` | Run production build |
| `backend` | Start only backend service |
| `frontend` | Start only frontend service |
| `logs` | Show logs for all services |
| `stop` | Stop all services |
| `clean` | Stop and remove all containers/images |
| `install` | Install Python dependencies locally |
| `status` | Show service status |
| `shell` | Open shell in backend container |

## Architecture

### Development Mode
- **Frontend**: Vite dev server with hot reload (port 5173)
- **Backend**: FastAPI with uvicorn reload (port 8080)
- Both services run in separate containers with volume mounts for live editing

### Production Mode
- **Combined**: Single container with built frontend served by FastAPI
- Frontend assets are built and served as static files
- Optimized for deployment (port 8080)

## Environment Configuration

### Required Files

1. **`.env`** - Environment variables (created automatically if missing)
2. **`sage-striker-294302-b248a695e8e5.json`** - Google Cloud credentials
3. **`requirements.txt`** - Python dependencies

### Environment Variables

Create a `.env` file in the root directory with:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Google Cloud (optional, for Vision API)
GOOGLE_APPLICATION_CREDENTIALS=/app/google-credentials.json

# Development settings
VITE_API_BASE_URL=http://localhost:8080
```

## Docker Services

### frontend-dev
- **Purpose**: Development frontend with hot reload
- **Port**: 5173
- **Volumes**: Source code mounted for live editing
- **Dependencies**: backend service

### backend
- **Purpose**: FastAPI backend with auto-reload
- **Port**: 8080
- **Volumes**: Backend source, .env, and credentials mounted
- **Environment**: Development mode with reload enabled

### app (production)
- **Purpose**: Combined frontend + backend for production
- **Port**: 8080
- **Profile**: production (use with `--profile production`)
- **Optimization**: Multi-stage build with minimal final image

## Development Workflow

1. **Start development environment**:
   ```bash
   ./docker-dev.sh dev
   ```

2. **Open your browser**:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8080/docs (FastAPI docs)

3. **Edit code**: Changes to frontend and backend will automatically reload

4. **View logs**: 
   ```bash
   ./docker-dev.sh logs
   ```

5. **Stop when done**:
   ```bash
   ./docker-dev.sh stop
   ```

## Production Deployment

### Build Production Image

```bash
# Build optimized production image
./docker-dev.sh build

# Or manually
docker-compose build app
```

### Run Production Container

```bash
# Start production version
./docker-dev.sh prod

# Or manually
docker-compose --profile production up app -d
```

### Deploy to Cloud Run

The production Dockerfile is optimized for Google Cloud Run:

```bash
# Build and tag for Cloud Run
docker build -t gcr.io/YOUR_PROJECT_ID/skypad .

# Push to Google Container Registry
docker push gcr.io/YOUR_PROJECT_ID/skypad

# Deploy to Cloud Run
gcloud run deploy skypad \
  --image gcr.io/YOUR_PROJECT_ID/skypad \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## Troubleshooting

### Common Issues

1. **Port already in use**:
   ```bash
   # Stop existing services
   ./docker-dev.sh stop
   
   # Or kill processes using the ports
   sudo lsof -t -i tcp:5173 -i tcp:8080 | xargs kill -9
   ```

2. **Build fails**:
   ```bash
   # Clean and rebuild
   ./docker-dev.sh clean
   ./docker-dev.sh dev
   ```

3. **Environment variables not loading**:
   - Ensure `.env` file exists in root directory
   - Check file permissions: `chmod 644 .env`

4. **Google credentials error**:
   - Ensure `sage-striker-294302-b248a695e8e5.json` exists
   - Check file permissions: `chmod 644 sage-striker-294302-b248a695e8e5.json`

### Debugging

1. **Access backend container**:
   ```bash
   ./docker-dev.sh shell
   ```

2. **View specific service logs**:
   ```bash
   docker-compose logs frontend-dev
   docker-compose logs backend
   ```

3. **Check service health**:
   ```bash
   ./docker-dev.sh status
   ```

## File Structure

```
skypad/
├── docker-compose.yml           # Multi-service orchestration
├── Dockerfile                   # Production build
├── Dockerfile.backend           # Backend development
├── Dockerfile.frontend-dev      # Frontend development
├── docker-dev.sh               # Development script
├── .dockerignore               # Docker build exclusions
├── .env                        # Environment variables
├── requirements.txt            # Python dependencies
├── frontend/                   # React application
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
└── backend files               # FastAPI application
    ├── main.py
    ├── bella_prompt.py
    └── utils.py
```

## Performance Tips

1. **Use .dockerignore**: Already configured to exclude unnecessary files
2. **Layer caching**: Dependencies are installed before copying source code
3. **Multi-stage builds**: Production image only includes built assets
4. **Volume mounts**: Development mode uses volumes for fast iteration

## Security Notes

- Environment files are mounted read-only in containers
- Google credentials are mounted separately (not copied into image)
- Production image doesn't include development dependencies
- Use Docker secrets for production deployments
