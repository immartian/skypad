#!/bin/bash

# Activate the CUDA environment
source /media/im2/plus/cuda_env/bin/activate

# Ensure temp directories exist
mkdir -p /media/im2/plus/tmp
mkdir -p /media/im2/plus/pip_cache
mkdir -p /media/im2/plus/pip_build

# Set environment variables for pip
export TMPDIR=/media/im2/plus/tmp
export PIP_NO_CACHE_DIR=1

# Install PyTorch if not already installed
if ! python -c "import torch" &>/dev/null; then
    echo "Installing PyTorch..."
    pip install torch --no-cache-dir
else
    echo "PyTorch is already installed!"
fi

# Print PyTorch information
python -c "import torch; print(f'PyTorch version: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}')"

echo ""
echo "Environment is ready! You can now run PyTorch in VSCode."
echo "To test in Python:"
echo ""
echo "import torch"
echo "print(torch.rand(3,3).cuda())"
echo ""