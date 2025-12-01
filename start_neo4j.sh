#!/bin/bash

# Stop and remove existing neo4j container if it exists
sudo docker stop neo4j 2>/dev/null
sudo docker rm neo4j 2>/dev/null

# Create directories for Neo4j data and logs
mkdir -p neo4j/data neo4j/logs

# Run Neo4j container
sudo docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/siemensenergy \
  -v $PWD/neo4j/data:/data \
  -v $PWD/neo4j/logs:/logs \
  neo4j:latest

echo "Neo4j is starting..."
echo "Wait a few seconds, then access:"
echo "  Neo4j Browser: http://localhost:7474"
echo "  Bolt: bolt://localhost:7687"
echo ""
echo "Credentials:"
echo "  Username: neo4j"
echo "  Password: siemensenergy"
echo ""
echo "Check container status with: sudo docker ps"
