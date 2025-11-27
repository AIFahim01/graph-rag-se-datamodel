#!/bin/bash
# Setup Neo4j for Graph RAG System

echo "🔧 Setting up Neo4j..."
echo ""

# Stop and remove old container
echo "1. Stopping old Neo4j container..."
docker stop neo4j-vector-test 2>/dev/null || true
docker rm neo4j-vector-test 2>/dev/null || true
echo "   ✅ Old container removed"
echo ""

# Create new container
echo "2. Creating new Neo4j container..."
docker run -d \
  --name neo4j-vector-test \
  -p 7474:7474 \
  -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/siemensenergy \
  neo4j:5.26-community

if [ $? -eq 0 ]; then
    echo "   ✅ Container created successfully"
else
    echo "   ❌ Failed to create container"
    exit 1
fi
echo ""

# Wait for Neo4j to start
echo "3. Waiting for Neo4j to start (15 seconds)..."
sleep 15
echo "   ✅ Wait complete"
echo ""

# Verify
echo "4. Verifying Neo4j is running..."
if docker ps | grep -q neo4j-vector-test; then
    echo "   ✅ Container is running"
else
    echo "   ❌ Container is not running"
    exit 1
fi

if curl -s -o /dev/null -w "%{http_code}" http://localhost:7474 | grep -q 200; then
    echo "   ✅ HTTP interface accessible (port 7474)"
else
    echo "   ⚠️  HTTP interface not ready yet (may need more time)"
fi
echo ""

echo "✨ Neo4j setup complete!"
echo ""
echo "Credentials:"
echo "   URL: http://localhost:7474"
echo "   Username: neo4j"
echo "   Password: siemensenergy"
echo ""
echo "Ready to run:"
echo "   cd /home/ib3/Documents/test_bp/knowledge_graph_vector_GC_Data/graph_check"
echo "   source ../activate_ultrathink.sh"
echo "   python3 main.py --mode load"
