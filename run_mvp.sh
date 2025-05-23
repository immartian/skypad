#!/bin/bash

# Set correct Python paths
export PYTHONPATH="/media/im2/plus/lab4/skypad/.skypad_app:/media/im2/plus/cuda_env/lib/python3.12/site-packages:/media/im2/plus/python_libs:/media/im2/plus/python_env/lib/python3.12/site-packages::/media/im2/plus/cuda_env/lib/python3.12/site-packages:/media/im2/plus/python_env/lib/python3.12/site-packages:"
export PIP_NO_CACHE_DIR=1
export TMPDIR="/media/im2/plus/tmp"

# Disable Streamlit's file watcher to avoid inotify and torch issues
export STREAMLIT_SERVER_FILE_WATCHER_TYPE="none"

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

# Create a Python module that patches PyTorch path handling
cat > "/media/im2/plus/tmp/torch_patch.py" << 'EOF'
# Patch for torch.classes.__path__._path issue
import sys
import types
import importlib

# Function to create a patched torch module
def create_patched_torch():
    # Import the original torch
    old_torch = importlib.import_module('torch')
    
    # Create a new module to replace torch.classes
    safe_classes = types.ModuleType('torch.classes')
    
    # Define __getattr__ to handle all attribute accesses safely
    def safe_getattr(name):
        if name == '__path__':
            # Return a list that won't have _path accessed
            class SafePath(list):
                def __getattr__(self, attr):
                    if attr == '_path':
                        return []
                    return super().__getattr__(attr)
            return SafePath(['<safe_path>'])
        
        # For any other attribute, access the real torch.classes
        try:
            return getattr(old_torch.classes, name)
        except (AttributeError, RuntimeError):
            return None
    
    # Add the safe __getattr__
    safe_classes.__getattr__ = safe_getattr
    
    # Replace torch.classes with our safe version
    setattr(old_torch, 'classes', safe_classes)
    
    return old_torch

# Replace torch in sys.modules
sys.modules['torch'] = create_patched_torch()

# Load streamlit with the patched torch
import streamlit.web.bootstrap
EOF

# Choose an available port
PORT=8502

# Run streamlit with explicit server settings
echo "Starting Streamlit server with dual IPv4+IPv6 support on port $PORT"
echo "Access via IPv4: http://${IPV4_ADDR}:${PORT}"
echo "Access via IPv6: http://[${IPV6_ADDR}]:${PORT}"

"$PYTHON_PATH" -c "
import sys
sys.path.insert(0, '/media/im2/plus/tmp')
import torch_patch
from streamlit.web import cli as streamlit_cli
sys.argv = ['streamlit', 'run', '$PWD/app.py', 
    '--server.port', '$PORT',
    '--server.address', '::',
    '--server.enableCORS', 'true',
    '--server.enableXsrfProtection', 'false',
    '--server.headless', 'true',
    '--server.fileWatcherType', 'none',
    '--browser.serverAddress', '0.0.0.0',
    '--browser.gatherUsageStats', 'false',
    '--global.developmentMode', 'false']
streamlit_cli.main()
"

