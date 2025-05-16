#!/bin/bash

# Set correct Python paths
export PYTHONPATH="/media/im2/plus/lab4/skypad/.skypad_app:/media/im2/plus/cuda_env/lib/python3.12/site-packages:/media/im2/plus/python_libs:/media/im2/plus/python_env/lib/python3.12/site-packages::/media/im2/plus/cuda_env/lib/python3.12/site-packages:/media/im2/plus/python_env/lib/python3.12/site-packages:"
export PIP_NO_CACHE_DIR=1
export TMPDIR="/media/im2/plus/tmp"

# Make sure the temp directory exists
mkdir -p "/media/im2/plus/tmp" 2>/dev/null

# Find the Python path
PYTHON_PATH="/media/im2/plus/cuda_env/bin/python"
if [ ! -x "$PYTHON_PATH" ]; then
    PYTHON_PATH=$(which python3)
fi

# Get system IP addresses for display purposes
IPV4_ADDR=$(hostname -I | awk '{print $1}')
IPV6_ADDR=$(ip -6 addr show scope global | grep -oP '(?<=inet6 )[\da-f:]+'| head -1)

# Run streamlit with explicit server settings
# Configure for true dual-stack support (IPv4+IPv6)
# Enable CORS and disable XSRF protection to allow file uploads from mobile

echo "Starting Streamlit server with dual IPv4+IPv6 support on port 8501"
echo "Access via IPv4: http://${IPV4_ADDR}:8501"
echo "Access via IPv6: http://[${IPV6_ADDR}]:8501"

"$PYTHON_PATH" -m streamlit run app.py \
    --server.port 8501 \
    --server.address :: \
    --server.enableCORS true \
    --server.enableXsrfProtection false \
    --server.headless true \
    --server.fileWatcherType none \
    --browser.serverAddress 0.0.0.0 \
    --browser.gatherUsageStats false \
    --global.developmentMode false "$@"

