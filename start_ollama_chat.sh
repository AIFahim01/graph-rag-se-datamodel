#!/bin/bash
# Start Ollama GraphRAG Interactive Chat

echo "Starting Ollama GraphRAG Interactive Chat with Mistral 7B..."
echo ""
echo "You can ask questions about HVDC/SYNCON systems."
echo "Type 'exit' or 'quit' to stop."
echo ""

source ~/miniconda3/etc/profile.d/conda.sh
conda activate hdvc_syncon_vectordb

python ollama_graphrag_chat.py --interactive --model mistral
