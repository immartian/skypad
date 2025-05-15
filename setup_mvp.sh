#!/bin/bash

# This script sets up the Skypad Image Tagging MVP with correct dependencies
# Handles the complex Python environment issues

echo "Setting up Skypad Image Tagging MVP..."

# Define paths from VSCode settings
PYTHON_PATH="/media/im2/plus/cuda_env/bin/python"
SITE_PACKAGES="/media/im2/plus/cuda_env/lib/python3.12/site-packages"
CUSTOM_LIBS="/media/im2/plus/python_libs"

# Make sure we're using the right Python
if [ ! -x "$PYTHON_PATH" ]; then
    echo "Error: Custom Python not found at $PYTHON_PATH"
    echo "Using system Python instead."
    PYTHON_PATH=$(which python3)
fi

echo "Using Python: $PYTHON_PATH"

# Create a directory to store our app-specific files
APP_DIR="$PWD/.skypad_app"
mkdir -p "$APP_DIR"

# Create a wrapper script that sets the correct paths
echo "#!/bin/bash

# Set correct Python paths
export PYTHONPATH=\"$SITE_PACKAGES:$CUSTOM_LIBS:$APP_DIR\"
export PIP_NO_CACHE_DIR=1
export TMPDIR=\"/media/im2/plus/tmp\"

# Run the specified command with the correct Python
\"$PYTHON_PATH\" \"\$@\"
" > "$APP_DIR/python_wrapper.sh"

chmod +x "$APP_DIR/python_wrapper.sh"

# Install dependencies directly to our app directory
echo "Installing core dependencies..."
"$APP_DIR/python_wrapper.sh" -m pip install -t "$APP_DIR" streamlit requests pillow

echo "Installing optional dependencies..."
"$APP_DIR/python_wrapper.sh" -m pip install -t "$APP_DIR" python-dotenv || echo "Could not install python-dotenv"

echo "Installing CLIP dependencies (this might take a while)..."
"$APP_DIR/python_wrapper.sh" -m pip install -t "$APP_DIR" open-clip-torch || echo "Could not install CLIP"

# Create a run script that sets the environment correctly
echo "#!/bin/bash

# Set correct Python paths
export PYTHONPATH=\"$APP_DIR:$SITE_PACKAGES:$CUSTOM_LIBS:$PYTHONPATH\"
export PIP_NO_CACHE_DIR=1
export TMPDIR=\"/media/im2/plus/tmp\"

# Find the streamlit executable in our app directory
STREAMLIT_PATH=\"$APP_DIR/bin/streamlit\"
if [ ! -x \"\$STREAMLIT_PATH\" ]; then
    # Try looking inside the app directory
    STREAMLIT_PATH=\"\$(find \"$APP_DIR\" -name streamlit -type f | head -1)\"
fi

if [ ! -x \"\$STREAMLIT_PATH\" ]; then
    # Fall back to using Python module
    echo \"Running streamlit as a module...\"
    \"$PYTHON_PATH\" -m streamlit run app_robust.py \"\$@\"
else
    echo \"Running streamlit executable...\"
    \"\$STREAMLIT_PATH\" run app_robust.py \"\$@\"
fi
" > run_mvp.sh

chmod +x run_mvp.sh

echo ""
echo "Setup complete! Run the app with:"
echo "./run_mvp.sh"
echo ""
echo "This setup creates an app-specific environment that works with your"
echo "existing Python setup at $PYTHON_PATH"