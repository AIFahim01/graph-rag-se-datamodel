#!/bin/bash
# Manual download of ReLiK models using git-lfs

echo "=================================================================="
echo "MANUAL RELIK MODEL DOWNLOAD SCRIPT"
echo "=================================================================="

# Create models directory
MODELS_DIR="$HOME/models"
mkdir -p "$MODELS_DIR"
cd "$MODELS_DIR"

echo ""
echo "📥 Downloading ReLiK relation extraction model..."
echo "   This will bypass HuggingFace Hub API and use git-lfs directly"
echo ""

# Install git-lfs if not present
if ! command -v git-lfs &> /dev/null; then
    echo "Installing git-lfs..."
    sudo apt-get update && sudo apt-get install -y git-lfs
    git lfs install
fi

# Clone the model repository
MODEL_NAME="relik-relation-extraction-small"
REPO_URL="https://huggingface.co/relik-ie/$MODEL_NAME"

echo "🔄 Cloning model repository: $REPO_URL"
if [ -d "$MODEL_NAME" ]; then
    echo "   Directory exists, pulling latest..."
    cd "$MODEL_NAME"
    git pull
else
    GIT_LFS_SKIP_SMUDGE=0 git clone "$REPO_URL"
    cd "$MODEL_NAME"
fi

# Check if files downloaded successfully
echo ""
echo "📊 Checking downloaded files..."
ls -lh

# Check file sizes
echo ""
echo "📏 File sizes:"
find . -type f -exec ls -lh {} + | grep -E "\.(bin|pt|safetensors)$"

echo ""
echo "✅ Manual download complete!"
echo ""
echo "📝 To use this model in Python:"
echo "   from relik import Relik"
echo "   model = Relik.from_pretrained('$MODELS_DIR/$MODEL_NAME', local_files_only=True)"
echo ""
echo "=================================================================="