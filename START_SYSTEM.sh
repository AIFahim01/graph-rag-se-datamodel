#!/bin/bash

#================================
# GRAPH-RAG SYSTEM STARTUP SCRIPT
#================================

echo "=================================================="
echo "🚀 Graph-RAG System Startup"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# Function to check if port is in use
check_port() {
    lsof -i :$1 >/dev/null 2>&1
    return $?
}

# Function to kill existing process on port
kill_port() {
    fuser -k $1/tcp 2>/dev/null || true
    sleep 1
}

# ====================
# 1. CHECK PREREQUISITES
# ====================
echo -e "\n${YELLOW}[1/5]${NC} Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker${NC}"

if ! command -v npm &> /dev/null; then
    echo -e "${RED}✗ npm not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓ npm${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python 3${NC}"

# ====================
# 2. START NEO4J
# ====================
echo -e "\n${YELLOW}[2/5]${NC} Checking Neo4j database..."

if docker ps | grep -q neo4j; then
    echo -e "${GREEN}✓ Neo4j already running${NC}"
else
    echo "Starting Neo4j..."
    docker start neo4j-graphrag 2>/dev/null || \
    docker run -d \
        --name neo4j-graphrag \
        -p 7474:7474 \
        -p 7687:7687 \
        -e NEO4J_AUTH=neo4j/siemensenergy \
        -v "$PROJECT_DIR/neo4j/data":/data \
        -v "$PROJECT_DIR/neo4j/logs":/logs \
        neo4j:latest

    sleep 5
    echo -e "${GREEN}✓ Neo4j started${NC}"
fi

# ====================
# 3. START BACKEND API
# ====================
echo -e "\n${YELLOW}[3/5]${NC} Starting backend API server..."

if check_port 8001; then
    kill_port 8001
fi

# Activate conda environment and start API
source activate graph-rag 2>/dev/null || true
python integrated_api_server.py > /tmp/api_server.log 2>&1 &
API_PID=$!

sleep 5
if check_port 8001; then
    echo -e "${GREEN}✓ API Server running on port 8001${NC}"
else
    echo -e "${RED}✗ API Server failed to start${NC}"
    cat /tmp/api_server.log
    exit 1
fi

# ====================
# 4. START FRONTEND
# ====================
echo -e "\n${YELLOW}[4/5]${NC} Starting frontend server..."

if check_port 3000; then
    kill_port 3000
fi

npm run start > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!

sleep 15
if check_port 3000; then
    echo -e "${GREEN}✓ Frontend running on port 3000${NC}"
else
    echo -e "${YELLOW}⚠ Frontend may still be starting...${NC}"
    echo "Check /tmp/frontend.log for details"
fi

# ====================
# 5. VERIFY SYSTEM
# ====================
echo -e "\n${YELLOW}[5/5]${NC} Verifying system..."

echo ""
echo "=================================================="
echo "✅ System Status"
echo "=================================================="

# Check Neo4j
if curl -s http://localhost:7474 -o /dev/null; then
    echo -e "${GREEN}✓${NC} Neo4j Browser: http://localhost:7474"
else
    echo -e "${RED}✗${NC} Neo4j Browser: http://localhost:7474"
fi

# Check API
if curl -s http://localhost:8001/docs -o /dev/null; then
    echo -e "${GREEN}✓${NC} Backend API: http://localhost:8001/docs"
else
    echo -e "${RED}✗${NC} Backend API: http://localhost:8001/docs"
fi

# Check Frontend
if curl -s http://localhost:3000 -o /dev/null; then
    echo -e "${GREEN}✓${NC} Frontend UI: http://localhost:3000"
else
    echo -e "${RED}✗${NC} Frontend UI: http://localhost:3000"
fi

echo ""
echo "=================================================="
echo "📝 Process IDs"
echo "=================================================="
echo "API Server PID: $API_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "To stop the system:"
echo "  kill $API_PID $FRONTEND_PID"
echo ""
echo "=================================================="

# Keep script running
wait
