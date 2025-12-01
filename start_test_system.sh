#!/bin/bash
# Start ULTRATHINK Test System (Backend + Frontend)
# Handles proxy bypass for localhost

echo "=========================================="
echo "🚀 Starting ULTRATHINK Test System"
echo "=========================================="

# Set proxy bypass for localhost
export no_proxy="localhost,127.0.0.1,::1"
export NO_PROXY="localhost,127.0.0.1,::1"

echo ""
echo "✅ Proxy bypass configured for localhost"
echo ""
echo "📋 What to run:"
echo ""
echo "Terminal 1 - Backend (port 8001):"
echo "  cd /home/ib3/Documents/test_bp/knowledge_graph_vector_GC_Data"
echo "  source activate_ultrathink.sh"
echo "  export no_proxy='localhost,127.0.0.1'"
echo "  python graph-rag-se-datamodel/frontend_viewer/backend/api_server_test.py"
echo ""
echo "Terminal 2 - Frontend (port 3001):"
echo "  cd /home/ib3/Documents/test_bp/knowledge_graph_vector_GC_Data/graph-rag-se-datamodel/frontend_viewer/frontend_test"
echo "  export no_proxy='localhost,127.0.0.1'"
echo "  PORT=3001 npm run dev"
echo ""
echo "=========================================="
