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

# Run streamlit with explicit server settings
# Disable development mode and file watching to avoid inotify limit issues
echo "Starting Streamlit server on port 8501 with consolidated app.py..."
"$PYTHON_PATH" -m streamlit run app.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.fileWatcherType none \
    --global.developmentMode false "$@"

