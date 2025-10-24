#!/bin/bash
# Setup Neo4j with Docker

set -e

echo "====================================="
echo "Neo4j Setup for PDF-to-GraphRAG"
echo "====================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker not found. Please install Docker first."
    exit 1
fi

# Check if Neo4j container already exists
if docker ps -a | grep -q neo4j-graphrag; then
    echo "Neo4j container already exists."
    read -p "Remove and recreate? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker stop neo4j-graphrag 2>/dev/null || true
        docker rm neo4j-graphrag 2>/dev/null || true
    else
        echo "Exiting. Use existing container or remove manually."
        exit 0
    fi
fi

# Set password
read -p "Enter Neo4j password (default: password): " NEO4J_PASSWORD
NEO4J_PASSWORD=${NEO4J_PASSWORD:-password}

# Run Neo4j container
echo ""
echo "Starting Neo4j 5.15 container..."
docker run -d \
  --name neo4j-graphrag \
  -p 7474:7474 \
  -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/$NEO4J_PASSWORD \
  -v $PWD/neo4j_data:/data \
  -v $PWD/neo4j_logs:/logs \
  neo4j:5.15

echo ""
echo "Waiting for Neo4j to start..."
sleep 10

echo ""
echo "✓ Neo4j setup complete!"
echo ""
echo "Access Neo4j Browser: http://localhost:7474"
echo "Username: neo4j"
echo "Password: $NEO4J_PASSWORD"
echo "Bolt URI: bolt://localhost:7687"
echo ""
echo "Update your .env file with:"
echo "NEO4J_URI=bolt://localhost:7687"
echo "NEO4J_USER=neo4j"
echo "NEO4J_PASSWORD=$NEO4J_PASSWORD"
