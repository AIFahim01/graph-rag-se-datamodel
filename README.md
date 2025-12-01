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
pip install fastapi uvicorn neo4j chromadb
pip install sentence-transformers ollama numpy pandas
```

### Environment Setup
Create `.env` file:
```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
OLLAMA_BASE_URL=http://localhost:11434
```

### Run the System

1. **Start Neo4j Database**
```bash
neo4j start
```

2. **Start Ollama (LLM)**
```bash
ollama serve
```

3. **Start Main API Server**
```bash
python integrated_api_server.py
```

4. **Access API**
- API: http://localhost:8001
- Docs: http://localhost:8001/docs

## Key Features

- **Intelligent Search**: LLM-powered query understanding
- **Hybrid Retrieval**: Combines vector search with metadata queries
- **Three-Judge System**: Optimal result selection using multiple LLMs
- **240K+ Documents**: Handles large-scale document collections
- **Real-time Processing**: Fast query response times

## API Endpoints

### Search
```
GET /api/llm-search?q=your_query
```

### Count
```
GET /api/count?year=2021&technology=HVDC
```

### Chat
```
POST /api/chat
```

## Project Structure
```
.
├── integrated_api_server.py      # Main API
├── llm_query_generator.py        # LLM processing
├── three_llm_judge_system.py     # Decision system
├── build_vectordb_*.py           # Vector DB builders
├── graph_check/                  # Graph validation
│   ├── main.py
│   └── services/
└── test_*.py                     # Test files
```

## License
Proprietary - Contact repository owner for usage rights.