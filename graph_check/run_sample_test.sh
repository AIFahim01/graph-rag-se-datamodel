#!/bin/bash
# Quick test script for the Graph RAG pipeline

echo "=========================================="
echo "GRAPH RAG SYSTEM - SAMPLE TEST"
echo "=========================================="
echo ""

# Check if in correct directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: Run this script from the graph_check directory"
    exit 1
fi

# Check Neo4j
echo "🔍 Checking Neo4j status..."
if ! curl -s http://localhost:7474 > /dev/null 2>&1; then
    echo "❌ Neo4j is not running!"
    echo "   Start it with: docker start neo4j-vector-test"
    exit 1
fi
echo "✅ Neo4j is running"
echo ""

# Check Ollama
echo "🔍 Checking Ollama status..."
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  Ollama is not running!"
    echo "   Start it with: ollama serve"
    echo "   (Pipeline will use fallback query generation)"
fi
echo ""

# Run pipeline
echo "🚀 Running pipeline with sample data (10 documents)..."
echo ""

python3 main.py --mode full --sample

echo ""
echo "✨ Test complete!"
echo ""
echo "📊 Check the output folder for results:"
echo "   - output/chunks.json"
echo "   - output/knowledge_graph.json"
echo ""
echo "💬 To run query mode only:"
echo "   python3 main.py --mode query"
