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

# Install additional packages needed for the app
RUN pip install --no-cache-dir streamlit openai \
    torch open-clip-torch pillow python-dotenv google-cloud-vision

# Copy the application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8501

# Expose the port the app runs on
EXPOSE 8501

# Command to run the application
CMD streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true --server.fileWatcherType=none
