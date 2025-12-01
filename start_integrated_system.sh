#!/usr/bin/bash

echo "========================================================================="
echo "ULTRATHINK - Integrated Document Search System with Image Viewer"
echo "========================================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Neo4j is running
echo -e "${BLUE}📌 Checking Neo4j status...${NC}"
if neo4j status > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Neo4j is running${NC}"
else
    echo -e "${YELLOW}⚠️  Neo4j is not running. Starting it...${NC}"
    neo4j start
    sleep 5
fi

# Start the integrated API server
echo ""
echo -e "${BLUE}📌 Starting Integrated API Server...${NC}"
echo "This server provides:"
echo "  - Vector search with our 214,426 documents"
echo "  - Image serving from processed documents"
echo "  - Metadata filtering (HVDC/SynCon, years, customers)"
echo ""

# Activate conda environment and start API server
source /home/ib3/miniconda3/etc/profile.d/conda.sh
conda activate ultrathink

# Install FastAPI dependencies if needed
echo -e "${BLUE}📌 Checking FastAPI dependencies...${NC}"
pip install fastapi uvicorn python-multipart 2>/dev/null

# Start the API server in background
echo -e "${GREEN}✅ Starting API server on http://localhost:8000${NC}"
python integrated_api_server.py &
API_PID=$!

echo ""
echo "========================================================================="
echo -e "${GREEN}✅ Backend API Server Started!${NC}"
echo "========================================================================="
echo ""

# Navigate to frontend directory
cd /home/ib3/Documents/test_bp/knowledge_graph_vector_GC_Data/graph-rag-se-datamodel/frontend_viewer/frontend

echo -e "${BLUE}📌 Starting Frontend Application...${NC}"
echo ""

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    npm install
fi

echo -e "${GREEN}✅ Starting Next.js frontend on http://localhost:3000${NC}"
echo ""
echo "========================================================================="
echo -e "${GREEN}✨ SYSTEM READY!${NC}"
echo "========================================================================="
echo ""
echo "📡 Backend API: http://localhost:8000"
echo "🌐 Frontend UI: http://localhost:3000"
echo ""
echo "Available features:"
echo "  • Vector similarity search across 214,426 documents"
echo "  • View page images from documents"
echo "  • Filter by technology (HVDC/SynCon)"
echo "  • Filter by year (2021, 2022, 2024, 2025)"
echo "  • Natural language queries"
echo ""
echo "Example searches:"
echo "  • 'transformer protection systems'"
echo "  • 'HVDC converter specifications'"
echo "  • 'power requirements'"
echo ""
echo "Press Ctrl+C to stop both servers"
echo "========================================================================="

# Start the frontend
npm run dev

# Cleanup on exit
trap "kill $API_PID 2>/dev/null; exit" INT TERM EXIT