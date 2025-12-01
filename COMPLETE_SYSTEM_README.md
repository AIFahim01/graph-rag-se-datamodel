# Complete LLM-Powered Knowledge Graph Vector Search System

## 🚀 Everything is Now on GitHub!

All essential code for the complete system has been successfully pushed to the repository.

## Repository Structure

```
graph-rag-se-datamodel/ (R_n_D_vector branch)
│
├── Main LLM System (Root Level)
│   ├── integrated_api_server.py         # Main API server (port 8001)
│   ├── llm_query_generator.py           # LLM query generation
│   ├── three_llm_judge_system.py        # Three-judge decision system
│   ├── build_vectordb_full_240k_hybrid.py # UltraThink vector DB
│   ├── vectorize_and_store.py           # Vectorization pipeline
│   └── [60+ other system files]
│
├── frontend_viewer_src/
│   ├── frontend/                        # Next.js UI application
│   │   ├── app/api/                     # API routes with LLM integration
│   │   ├── components/                  # React components
│   │   └── package.json                 # Frontend dependencies
│   └── backend/                         # Frontend-specific backend
│       ├── api_server.py                # FastAPI server
│       └── query_enhancer.py            # Query enhancement
│
└── graph_rag_backend_src/
    ├── src/                              # Core backend modules
    │   ├── storage/                      # Neo4j, Chroma, vector stores
    │   ├── processing/                   # PDF, chunking, metadata
    │   ├── embeddings/                   # Vector generation
    │   ├── retrieval/                    # Hybrid retrieval
    │   └── qa/                           # QA systems
    └── setup.py                          # Python package setup
```

## Complete System Setup

### Prerequisites
- Python 3.8+
- Node.js 16+
- Neo4j Database
- Ollama (for LLM)

### 1. Clone the Repository

```bash
git clone https://github.com/AIFahim01/graph-rag-se-datamodel.git
cd graph-rag-se-datamodel
git checkout R_n_D_vector
```

### 2. Setup Backend Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt  # If available
# Or install manually:
pip install fastapi uvicorn neo4j chromadb sentence-transformers
pip install numpy pandas scikit-learn ollama
```

### 3. Configure Services

Create `.env` file in root:
```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
OLLAMA_BASE_URL=http://localhost:11434
```

### 4. Start Backend Services

```bash
# Terminal 1: Start main API server
python integrated_api_server.py

# Terminal 2: Start Neo4j (if not running)
neo4j start

# Terminal 3: Start Ollama (if not running)
ollama serve
```

### 5. Setup and Start Frontend

```bash
# Navigate to frontend
cd frontend_viewer_src/frontend

# Install dependencies
npm install

# Configure backend URL
echo "NEXT_PUBLIC_API_URL=http://localhost:8001" > .env.local

# Start development server
npm run dev
```

### 6. Access the System

- **Frontend UI**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs
- **Neo4j Browser**: http://localhost:7474

## Key Features

### 1. LLM-Powered Search
- Intelligent query processing with Ollama
- Automatic query enhancement
- Context-aware responses

### 2. Three-Judge System
- Vector search path
- Metadata/Cypher query path
- Judge LLM for optimal result selection

### 3. UltraThink Vector Database
- 240,000+ document processing
- Hybrid search capabilities
- High-performance retrieval

### 4. Frontend Features
- Interactive chat interface
- Real-time search results
- Document viewer with metadata
- Location-based queries

## Important Files

### Core System
- `integrated_api_server.py` - Main API server
- `llm_query_generator.py` - Query generation
- `three_llm_judge_system.py` - Decision system
- `build_vectordb_full_240k_hybrid.py` - Vector DB builder

### Frontend
- `frontend_viewer_src/frontend/app/api/chat/route.ts` - Chat API
- `frontend_viewer_src/frontend/app/api/search/route.ts` - Search API
- `frontend_viewer_src/backend/api_server.py` - Backend server

### Configuration
- `.gitignore` - Git exclusions
- `requirements.txt` - Python dependencies
- `package.json` - Node.js dependencies

## Data Note

The original `graph-rag-se-datamodel` directory contains 213GB of project data (GC_2021, GC_2022, GC_2023, GC_2024) which is NOT included in the repository. Only the source code and essential configuration files are included.

## Troubleshooting

### Common Issues

1. **Port Conflicts**: Change ports in configuration files
2. **Missing Dependencies**: Check requirements.txt and package.json
3. **Database Connection**: Verify Neo4j credentials
4. **LLM Connection**: Ensure Ollama is running

### Getting Help

Check the documentation files:
- `QUICK_START.md`
- `INTEGRATED_SYSTEM_GUIDE.md`
- `LLM_SEARCH_GUIDE.md`
- `README_ULTRATHINK.md`

## Repository Information

- **GitHub**: https://github.com/AIFahim01/graph-rag-se-datamodel
- **Branch**: R_n_D_vector
- **Total Files**: 180+ source files
- **Languages**: Python, TypeScript, JavaScript

## License

This project contains proprietary code. Please check with the repository owner for usage rights.