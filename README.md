# Skypad AI Platform

A containerized AI platform featuring a chat interface with Bella (OpenAI-powered assistant), image analysis capabilities (CLIP, OpenAI Vision, Google Vision), and customizable environment configurations.

## Features

- **Chat Interface**: Interact with Bella, an AI assistant powered by OpenAI
- **Image Analysis**: Leverage multiple vision technologies (CLIP, OpenAI Vision, Google Vision)
- **Containerized**: Optimized Docker container with CPU-only PyTorch to reduce memory footprint
- **Cloud Ready**: Streamlined deployment to Google Cloud Run

## Environment Setup

1. Create a `.env` file in the project root with the following variables:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

2. If using Google Vision API, place your Google credentials JSON file in the project root:
   ```
   sage-striker-294302-b248a695e8e5.json
   ```

## Local Development

To run the application locally:

```bash
streamlit run app.py
```

## Docker Deployment

### Local Docker Testing

Run the local Docker test script:

```bash
./run_local_docker.sh
```

### Google Cloud Run Deployment

The deployment script offers options to skip authentication and build steps for faster iterative deployments:

```bash
# Full deployment (authenticate, build, and deploy)
./deploy_to_cloud_run.sh

# Skip authentication (useful for repeated deployments in the same session)
./deploy_to_cloud_run.sh --skip-auth

# Skip build (when you haven't changed the code but want to update environment variables)
./deploy_to_cloud_run.sh --skip-build

# Skip both authentication and build (fastest redeployment)
./deploy_to_cloud_run.sh --skip-auth --skip-build
```

## Memory Configuration

The application is configured with 4GB of memory on Cloud Run. If you encounter memory issues, you can adjust this in the deployment script.

## Security

- `.dockerignore` prevents sensitive files from being included in the container
- `.gcloudignore` controls files sent to Cloud Run
- Google Secret Manager securely handles credentials
