#!/bin/bash
#
# ULTRATHINK Conda Environment Setup
# Creates conda environment with all requirements for page-by-page vectorization
#

set -e  # Exit on error

echo "=============================================="
echo "🚀 ULTRATHINK Conda Environment Setup"
echo "=============================================="

# Configuration
ENV_NAME="ultrathink"
PYTHON_VERSION="3.10"

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo "❌ Error: conda not found. Please install Miniconda or Anaconda first."
    exit 1
fi

echo ""
echo "📋 Configuration:"
echo "   Environment name: ${ENV_NAME}"
echo "   Python version: ${PYTHON_VERSION}"
echo ""

# Check if environment already exists
if conda env list | grep -q "^${ENV_NAME} "; then
    echo "⚠️  Environment '${ENV_NAME}' already exists!"
    read -p "Do you want to remove and recreate it? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️  Removing existing environment..."
        conda env remove -n ${ENV_NAME} -y
    else
        echo "❌ Setup cancelled."
        exit 0
    fi
fi

echo ""
echo "📦 Step 1: Creating conda environment..."
conda create -n ${ENV_NAME} python=${PYTHON_VERSION} -y

echo ""
echo "📦 Step 2: Activating environment..."
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate ${ENV_NAME}

echo ""
echo "📦 Step 3: Installing core packages..."
conda install -c conda-forge -y \
    numpy \
    scipy \
    pandas \
    matplotlib \
    seaborn \
    pyyaml \
    tqdm

echo ""
echo "📦 Step 4: Installing PyTorch (CPU version)..."
# Install PyTorch CPU version for faster installation
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

echo ""
echo "📦 Step 5: Installing ML/AI packages..."
pip install \
    sentence-transformers>=2.2.0 \
    transformers>=4.30.0 \
    accelerate>=0.20.0

echo ""
echo "📦 Step 6: Installing Neo4j and vector DB packages..."
pip install \
    neo4j>=5.0.0 \
    chromadb>=0.4.0

echo ""
echo "📦 Step 7: Installing FastAPI and web framework..."
pip install \
    fastapi>=0.100.0 \
    uvicorn[standard]>=0.23.0 \
    pydantic>=2.0.0

echo ""
echo "📦 Step 8: Installing utilities..."
pip install \
    python-dotenv>=1.0.0 \
    loguru>=0.7.0 \
    networkx>=3.0.0

echo ""
echo "📦 Step 9: Installing PDF processing (if needed)..."
pip install \
    pymupdf>=1.23.0 \
    pdfplumber>=0.10.0

echo ""
echo "=============================================="
echo "✅ ULTRATHINK Environment Setup Complete!"
echo "=============================================="
echo ""
echo "📊 Installed packages summary:"
conda list | grep -E "(torch|sentence-transformers|neo4j|fastapi|numpy)"
echo ""
echo "🎯 Next Steps:"
echo ""
echo "1️⃣  Activate environment:"
echo "   conda activate ${ENV_NAME}"
echo ""
echo "2️⃣  Run test vectorization:"
echo "   cd /home/ib3/Documents/test_bp/knowledge_graph_vector_GC_Data"
echo "   python build_vectordb_test_small.py"
echo ""
echo "3️⃣  Start test backend:"
echo "   python graph-rag-se-datamodel/frontend_viewer/backend/api_server_test.py"
echo ""
echo "4️⃣  Start test frontend:"
echo "   cd graph-rag-se-datamodel/frontend_viewer/frontend"
echo "   PORT=3001 npm run dev"
echo ""
echo "=============================================="
echo "💡 Quick command to activate:"
echo "   conda activate ${ENV_NAME}"
echo "=============================================="
