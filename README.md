# LLM-Powered Knowledge Graph Vector Search System

A production-ready system for intelligent document search using LLMs, vector databases, and knowledge graphs.

## Core Components

### 1. Main API Server
- **`integrated_api_server.py`** - Primary FastAPI server (port 8001)
- **`llm_query_generator.py`** - LLM query generation and processing
- **`three_llm_judge_system.py`** - Three-judge decision system for optimal results

### 2. Vector Database
- **`build_vectordb_full_240k_hybrid.py`** - UltraThink vector database builder
- **`vectorize_and_store.py`** - Document vectorization pipeline
- **`create_indexes.py`** - Database index creation

### 3. Frontend APIs
- **`frontend_api_server.py`** - Frontend-specific API endpoints
- **`frontend_api_server_with_docs.py`** - API with Swagger documentation

### 4. Graph Check Module (`graph_check/`)
Complete graph validation and query system:
- `main.py` - Main entry point
- `services/neo4j_loader.py` - Neo4j data loading
- `services/llm_query_generator.py` - Query generation
- `services/query_executor.py` - Query execution

### 5. Testing & Monitoring
- **`test_*.py`** - Various test files for different components
- **`monitor_vectorization.py`** - Monitor vectorization progress
- **`continuous_backup.py`** - Automated backup system

## Quick Start

### Prerequisites
```bash
# Python 3.8+
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Setup
Create `.env` file:
```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
OLLAMA_BASE_URL=http://localhost:11434
```

## Running the System

### Required Services (Must be running)

#### 1. Neo4j Database
```bash
# Check status
neo4j status

# Start Neo4j
neo4j start

# Verify (should see Neo4j browser)
curl -s http://localhost:7474
```

#### 2. Ollama (LLM Service)
```bash
# Check if running
ps aux | grep ollama

# Start Ollama
ollama serve &

# Pull required models
ollama pull qwen3:14b
ollama pull mistral

# Verify
curl http://localhost:11434/api/tags
```

#### 3. Main Backend API Server
```bash
# Activate virtual environment
source venv/bin/activate

# Start the server
python integrated_api_server.py

# Verify (should see {"message": "API is running"} or similar)
curl http://localhost:8001
```

#### 4. Frontend Application
```bash
# In a new terminal
cd frontend

# Install dependencies (first time only)
npm install

# Start development server
npm run dev

# Verify (should see the UI)
curl http://localhost:3000
```

## Verify All Services

Run this command to check all services at once:
```bash
echo "=== Service Status ===" && \
curl -s http://localhost:7474 >/dev/null 2>&1 && echo "✓ Neo4j: Running" || echo "✗ Neo4j: Not running" && \
curl -s http://localhost:11434 >/dev/null 2>&1 && echo "✓ Ollama: Running" || echo "✗ Ollama: Not running" && \
curl -s http://localhost:8001 >/dev/null 2>&1 && echo "✓ Backend API: Running" || echo "✗ Backend API: Not running" && \
curl -s http://localhost:3000 >/dev/null 2>&1 && echo "✓ Frontend: Running" || echo "✗ Frontend: Not running"
```

## Access Points

Once all services are running:
- **Frontend UI**: http://localhost:3000
- **Chat Interface**: http://localhost:3000/chat
- **API Documentation**: http://localhost:8001/docs
- **Neo4j Browser**: http://localhost:7474

## Key Features

- **Intelligent Search**: LLM-powered query understanding
- **Hybrid Retrieval**: Combines vector search with metadata queries
- **Three-Judge System**: Optimal result selection using multiple LLMs
- **240K+ Documents**: Handles large-scale document collections
- **Real-time Processing**: Fast query response times

## API Endpoints

### Search
```bash
curl "http://localhost:8001/api/llm-search?q=your_query"
```

### Count
```bash
curl "http://localhost:8001/api/count?year=2021&technology=HVDC"
```

### Chat
```bash
curl -X POST "http://localhost:8001/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "your question"}'
```

## Project Structure
```
.
├── frontend/                      # Next.js frontend application
│   ├── app/                      # Application routes and pages
│   ├── components/               # React components
│   └── package.json             # Frontend dependencies
├── backend/                      # Backend API servers
│   ├── api_server.py            # FastAPI server
│   └── query_enhancer.py        # Query processing
├── src/                         # Core modules
│   ├── storage/                 # Neo4j, Chroma, vector stores
│   ├── processing/              # Document processing
│   ├── embeddings/              # Vector generation
│   └── retrieval/               # Hybrid retrieval
├── graph_check/                 # Graph validation
│   ├── main.py
│   └── services/
├── integrated_api_server.py     # Main API server
├── llm_query_generator.py       # LLM processing
├── three_llm_judge_system.py    # Decision system
└── requirements.txt             # Python dependencies
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**
```bash
# Find process using port
lsof -i :8001  # or :3000, :7474, :11434

# Kill process
kill -9 <PID>
```

2. **Neo4j Connection Failed**
```bash
# Check Neo4j logs
neo4j console

# Reset password if needed
neo4j-admin set-initial-password newpassword
```

3. **Ollama Not Responding**
```bash
# Restart Ollama
killall ollama
ollama serve &

# Check models
ollama list
```

4. **Frontend Build Issues**
```bash
# Clear cache and reinstall
cd frontend
rm -rf node_modules .next
npm install
npm run dev
```

## Production Deployment

For production, use process managers:

```bash
# Backend with PM2
pm2 start integrated_api_server.py --interpreter python3

# Frontend production build
cd frontend
npm run build
npm start

# Or with PM2
pm2 start npm --name "frontend" -- start
```

## Fresh Installation

For complete setup from scratch, see `FRESH_SETUP_GUIDE.md`

## License
Proprietary - Contact repository owner for usage rights.