# Frontend Setup Guide for Complete System

## ✅ Frontend Successfully Pushed to GitHub!

The frontend source code has been successfully pushed to the repository. You can now run the complete LLM-powered search system.

## Repository Structure

```
graph-rag-se-datamodel/
├── frontend_viewer_src/
│   ├── frontend/          # Next.js frontend application
│   │   ├── app/           # Application routes and API
│   │   ├── components/    # React components
│   │   ├── public/        # Static assets
│   │   └── package.json   # Dependencies
│   └── backend/           # Python backend API
│       ├── api_server.py
│       └── query_enhancer.py
└── [All other LLM system files]
```

## How to Run the Complete System

### 1. Clone the Repository

```bash
git clone https://github.com/AIFahim01/graph-rag-se-datamodel.git
cd graph-rag-se-datamodel
git checkout R_n_D_vector
```

### 2. Setup Backend (API Server)

```bash
# Navigate to your main project directory
cd /path/to/your/project

# Start the integrated API server (port 8001)
python integrated_api_server.py

# Or if you need the frontend-specific API
cd frontend_viewer_src/backend
python api_server.py
```

### 3. Setup Frontend

```bash
# Navigate to frontend directory
cd frontend_viewer_src/frontend

# Install dependencies
npm install

# Create .env.local file with your backend URL
echo "NEXT_PUBLIC_API_URL=http://localhost:8001" > .env.local

# Run the development server
npm run dev
```

### 4. Access the System

- **Frontend UI**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs

## Key Features Now Available

1. **LLM-Powered Search**: Intelligent query processing with Ollama
2. **Chat Interface**: Interactive chat with context preservation
3. **Vector Search**: Semantic search through project documents
4. **Three-Judge System**: Advanced query routing and validation
5. **UltraThink Integration**: High-performance vector database

## File Modifications Applied

The frontend includes all the fixes documented in `FRONTEND_MODIFICATIONS.md`:
- Removed hardcoded location patterns
- Fixed context building bugs
- Added location query detection
- Enhanced project summaries by year
- Switched to gpt-oss:20b model
- Added fallback counting logic

## Troubleshooting

If you encounter issues:

1. **Port conflicts**: Change ports in `.env.local` and server configs
2. **Missing dependencies**: Run `npm install` in frontend directory
3. **API connection errors**: Ensure backend is running on port 8001
4. **Database connection**: Check Neo4j is running and credentials are correct

## GitHub Repository

**Branch**: R_n_D_vector
**URL**: https://github.com/AIFahim01/graph-rag-se-datamodel/tree/R_n_D_vector

All frontend and backend source files are now available in the repository!