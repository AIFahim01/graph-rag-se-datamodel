#!/usr/bin/bash

echo "========================================================================="
echo "Starting ULTRATHINK Integrated System"
echo "========================================================================="

# Start API server
echo "Starting API server..."
source /home/ib3/miniconda3/etc/profile.d/conda.sh
conda activate ultrathink
python integrated_api_server.py &
API_PID=$!
echo "API server started with PID: $API_PID"

# Give API server time to start
sleep 5

# Start frontend
echo "Starting frontend..."
cd graph-rag-se-datamodel/frontend_viewer/frontend
npm run dev &
FRONTEND_PID=$!
echo "Frontend started with PID: $FRONTEND_PID"

echo ""
echo "========================================================================="
echo "System is running!"
echo "API Server: http://localhost:8001"
echo "Frontend: http://localhost:3000"
echo ""
echo "To stop: Press Ctrl+C or run: kill $API_PID $FRONTEND_PID"
echo "========================================================================="

# Wait for both processes
wait