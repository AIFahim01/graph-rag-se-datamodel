# ULTRATHINK Integrated System Guide

## 🚀 Complete Document Search System with Image Viewer

### Overview
This integrated system combines:
- **Vector Search**: 214,426 vectorized document pages
- **Image Viewer**: Display page images from processed documents
- **Frontend**: Next.js application at `/graph-rag-se-datamodel/frontend_viewer/frontend`
- **Backend API**: FastAPI server with Neo4j vector database

### Quick Start

#### Option 1: One-Command Start (Recommended)
```bash
./start_integrated_system.sh
```
This will:
- Check/start Neo4j
- Start the integrated API server (port 8000)
- Start the Next.js frontend (port 3000)
- Open browser to http://localhost:3000

#### Option 2: Manual Start

**Terminal 1 - Start API Server:**
```bash
source /home/ib3/miniconda3/etc/profile.d/conda.sh
conda activate ultrathink
python integrated_api_server.py
```

**Terminal 2 - Start Frontend:**
```bash
cd graph-rag-se-datamodel/frontend_viewer/frontend
npm run dev
```

### Features

#### 1. Vector Search with Images
- Search across 214,426 document pages
- View page images alongside search results
- Semantic similarity search using BAAI/bge-large-en-v1.5

#### 2. Filtering Options
- **Technology**: HVDC, SynCon, SVC/STATCOM, Other
- **Year**: 2021, 2022, 2024, 2025
- **Customer**: Filter by customer name
- **Project**: Specific project IDs

#### 3. Image Display
- Automatically serves images from `/output` directory
- Page images shown in search results
- Full document viewer with navigation

### API Endpoints

The integrated API server provides:

| Endpoint | Description |
|----------|-------------|
| `GET /api/search?q=query` | Vector similarity search |
| `GET /api/stats` | Database statistics |
| `GET /api/projects` | List all projects |
| `GET /api/document/{id}` | Get document details |
| `GET /api/image/{project}/{path}` | Serve document images |

### Example Queries

1. **Semantic Search**:
   - "transformer protection systems"
   - "HVDC converter specifications"
   - "power requirements for grid connection"

2. **Filtered Search**:
   ```
   /api/search?q=converter&technology=HVDC&year=2024
   ```

3. **Project Listing**:
   ```
   /api/projects?technology=SynCon&year=2025
   ```

### Database Statistics

- **Total Documents**: 214,426 pages
- **Technologies**:
  - HVDC: 13,470 documents
  - SynCon: 26,958 documents
  - SVC/STATCOM: 2,204 documents
  - Other: 171,794 documents
- **Years**: 2021, 2022, 2024, 2025

### File Structure

```
knowledge_graph_vector_GC_Data/
├── integrated_api_server.py      # Main API server with image support
├── query_api.py                  # Core query functions
├── output/                       # Document images and extracted content
│   ├── GC21_001/
│   │   ├── page_images/         # Page PNG files
│   │   ├── markdown/            # Extracted text
│   │   └── tables/              # Extracted tables
│   └── ...
├── backups/                      # Vector embeddings backup
└── graph-rag-se-datamodel/
    └── frontend_viewer/
        ├── frontend/             # Next.js frontend app
        └── backend/              # Original backend (can be replaced)
```

### Troubleshooting

#### Neo4j Connection Issues
```bash
# Check Neo4j status
neo4j status

# Restart if needed
neo4j restart
```

#### Port Already in Use
```bash
# Kill existing processes
lsof -i :8000  # Find API server
lsof -i :3000  # Find frontend

kill -9 <PID>  # Kill the process
```

#### Missing Dependencies
```bash
# Backend
pip install fastapi uvicorn python-multipart

# Frontend
cd graph-rag-se-datamodel/frontend_viewer/frontend
npm install
```

### Advanced Configuration

#### Change API Port
Edit `integrated_api_server.py`:
```python
uvicorn.run(app, host="0.0.0.0", port=8000)  # Change 8000 to desired port
```

#### Update Frontend API URL
Edit frontend environment file:
```bash
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > graph-rag-se-datamodel/frontend_viewer/frontend/.env.local
```

### Support

For issues or questions:
1. Check Neo4j is running: `neo4j status`
2. Verify indexes exist: `python create_indexes.py`
3. Check API health: http://localhost:8000/api/health
4. View API logs in terminal running `integrated_api_server.py`

### Next Steps

1. **Start the system**: `./start_integrated_system.sh`
2. **Open browser**: http://localhost:3000
3. **Try a search**: "HVDC transformer protection"
4. **View images**: Click on any result to see page images
5. **Filter results**: Use technology/year dropdowns

Enjoy your integrated document search system with full image support!