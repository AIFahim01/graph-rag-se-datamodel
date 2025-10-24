#!/bin/bash
# Setup Ollama and download required models

set -e

echo "====================================="
echo "Ollama Setup for PDF-to-GraphRAG"
echo "====================================="

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "Ollama not found. Installing..."

    # Detect OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        curl https://ollama.ai/install.sh | sh
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "On macOS, please install from: https://ollama.ai/download"
        exit 1
    else
        echo "Unsupported OS. Please install from: https://ollama.ai/download"
        exit 1
    fi
else
    echo "✓ Ollama already installed"
fi

# Start Ollama service
echo ""
echo "Starting Ollama service..."
ollama serve &
OLLAMA_PID=$!
sleep 5

# Pull required models
echo ""
echo "Downloading Llama 3.1 70B (this will take time, ~140GB)..."
ollama pull llama3.1:70b

echo ""
echo "✓ Setup complete!"
echo ""
echo "Ollama is running at: http://localhost:11434"
echo "Model: llama3.1:70b"
echo ""
echo "To stop Ollama: kill $OLLAMA_PID"
echo "To start later: ollama serve"
