FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for PyTorch and other packages
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies 
# Consider using pipenv or poetry for more robust dependency management
RUN pip install --no-cache-dir -r requirements.txt

# The following line is commented out as dependencies should now be managed by requirements.txt
# RUN pip install --no-cache-dir streamlit openai torch open-clip-torch pillow python-dotenv google-cloud-vision

# Copy the application credential files
COPY .env .
COPY sage-striker-294302-b248a695e8e5.json /app/google-credentials.json

# Copy the application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8000
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/google-credentials.json

# Create a directory for credentials
# RUN mkdir -p /app/credentials # This line is not strictly necessary if copying directly to /app

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application with environment variables
# CMD streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true --server.fileWatcherType=none
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
