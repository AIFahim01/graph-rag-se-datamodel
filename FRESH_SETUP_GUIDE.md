# Complete Fresh Environment Setup Guide

This guide will help you set up the entire LLM-powered Knowledge Graph Vector Search System from scratch on a new machine.

## System Requirements

- **OS**: Ubuntu 20.04+ / macOS / Windows with WSL2
- **RAM**: Minimum 16GB (32GB recommended)
- **Storage**: At least 50GB free space
- **Python**: 3.8 or higher
- **Node.js**: 16.x or higher
- **Git**: 2.x or higher

## Step 1: Install Prerequisites

### 1.1 Update System and Install Basic Tools
```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y
sudo apt install -y git curl wget build-essential software-properties-common

# macOS
brew update
brew install git curl wget
```

### 1.2 Install Python 3.8+
```bash
# Ubuntu/Debian
sudo apt install -y python3.8 python3-pip python3-venv

# macOS
brew install python@3.8

# Verify installation
python3 --version
```

### 1.3 Install Node.js 16+
```bash
# Using NodeSource (Ubuntu/Debian)
curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash -
sudo apt install -y nodejs

# macOS
brew install node@16

# Verify installation
node --version
npm --version
```

### 1.4 Install Neo4j Database
```bash
# Ubuntu/Debian
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable latest' | sudo tee /etc/apt/sources.list.d/neo4j.list
sudo apt update
sudo apt install -y neo4j

# macOS
brew install neo4j

# Start Neo4j
neo4j start

# Set initial password (default user: neo4j, default password: neo4j)
# Access http://localhost:7474 and change password to your preferred one
```

### 1.5 Install Ollama (for LLM)
```bash
# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# macOS
brew install ollama

# Start Ollama service
ollama serve &

# Pull required models
ollama pull llama2
ollama pull mistral
ollama pull qwen3:14b
```

## Step 2: Clone and Setup Repository

### 2.1 Clone the Repository
```bash
# Create workspace directory
mkdir -p ~/workspace
cd ~/workspace

# Clone repository
git clone https://github.com/AIFahim01/graph-rag-se-datamodel.git
cd graph-rag-se-datamodel
git checkout R_n_D_vector
```

### 2.2 Create Python Virtual Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip
```

### 2.3 Install Python Dependencies
```bash
# Core dependencies
pip install fastapi uvicorn[standard]
pip install neo4j py2neo
pip install chromadb
pip install sentence-transformers
pip install ollama
pip install numpy pandas scikit-learn
pip install python-dotenv
pip install aiofiles python-multipart
pip install pytest pytest-asyncio

# Document processing
pip install pypdf2 pdfplumber
pip install docling  # If available
pip install langchain langchain-community

# Optional but recommended
pip install jupyter notebook
pip install black flake8  # Code formatting
```

## Step 3: Configure Environment

### 3.1 Create Environment File
```bash
# Create .env file in root directory
cat > .env << 'EOF'
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password_here

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:14b

# API Configuration
API_HOST=0.0.0.0
API_PORT=8001

# Vector Database
CHROMA_PERSIST_DIR=./chroma_db
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Optional: OpenAI (if using)
OPENAI_API_KEY=your_key_here
EOF

# Edit the file to add your actual passwords
nano .env
```

### 3.2 Initialize Neo4j Database
```bash
# Create indexes and constraints
python create_indexes.py

# Test Neo4j connection
python -c "
from neo4j import GraphDatabase
driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'your_password'))
with driver.session() as session:
    result = session.run('RETURN 1 as num')
    print('Neo4j connected:', result.single()['num'] == 1)
driver.close()
"
```

## Step 4: Setup Frontend

### 4.1 Install Frontend Dependencies
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Create frontend environment file
cat > .env.local << 'EOF'
NEXT_PUBLIC_API_URL=http://localhost:8001
EOF

# Return to root directory
cd ..
```

## Step 5: Initialize Vector Database (Optional)

### 5.1 Build Vector Database
```bash
# For testing with small dataset
python build_vectordb_test_small.py

# For production with full dataset (takes longer)
# python build_vectordb_full_240k_hybrid.py
```

## Step 6: Start the System

### 6.1 Start Backend Services (Terminal 1)
```bash
# Activate virtual environment
source venv/bin/activate

# Start main API server
python integrated_api_server.py
# Server will run on http://localhost:8001
```

### 6.2 Start Frontend (Terminal 2)
```bash
# Navigate to frontend
cd frontend

# Start development server
npm run dev
# Frontend will run on http://localhost:3000
```

### 6.3 Start Additional Services (Optional, Terminal 3)
```bash
# If you need the frontend-specific API
cd backend
python api_server.py
```

## Step 7: Verify Installation

### 7.1 Check Backend API
```bash
# Test API endpoint
curl http://localhost:8001/
curl http://localhost:8001/docs  # Swagger documentation
```

### 7.2 Check Frontend
Open browser and navigate to:
- http://localhost:3000 - Main UI
- http://localhost:3000/chat - Chat interface
- http://localhost:3000/search - Search interface

### 7.3 Test Search Functionality
```bash
# Test LLM search
curl "http://localhost:8001/api/llm-search?q=Germany+projects+2021"

# Test count endpoint
curl "http://localhost:8001/api/count?year=2021"
```

## Step 8: Load Sample Data (Optional)

### 8.1 Load Test Data
```bash
# If you have sample data
python vectorize_and_store.py --input data/sample --batch-size 100
```

## Troubleshooting

### Common Issues and Solutions

1. **Neo4j Connection Error**
```bash
# Check if Neo4j is running
neo4j status

# Restart Neo4j
neo4j restart

# Check logs
journalctl -u neo4j -f
```

2. **Ollama Not Responding**
```bash
# Check if Ollama is running
ps aux | grep ollama

# Restart Ollama
killall ollama
ollama serve &

# Test Ollama
curl http://localhost:11434/api/tags
```

3. **Port Already in Use**
```bash
# Find process using port
lsof -i :8001  # or :3000 for frontend

# Kill process
kill -9 <PID>

# Or change port in .env file
```

4. **Memory Issues**
```bash
# Increase Python memory limit
export PYTHONMAXMEM=8G

# For Node.js
export NODE_OPTIONS="--max-old-space-size=4096"
```

5. **Missing Python Packages**
```bash
# Install any missing package
pip install <package_name>

# Or reinstall all
pip install -r requirements.txt  # if available
```

## Production Deployment

For production deployment:

1. Use `gunicorn` or `uvicorn` with workers:
```bash
uvicorn integrated_api_server:app --host 0.0.0.0 --port 8001 --workers 4
```

2. Build and serve frontend:
```bash
cd frontend
npm run build
npm run start
```

3. Use process managers:
```bash
# Install PM2
npm install -g pm2

# Start backend with PM2
pm2 start integrated_api_server.py --interpreter python3

# Start frontend with PM2
pm2 start npm --name "frontend" -- start
```

4. Setup Nginx reverse proxy for production.

## Quick Start Commands Summary

```bash
# Clone and setup
git clone https://github.com/AIFahim01/graph-rag-se-datamodel.git
cd graph-rag-se-datamodel
git checkout R_n_D_vector

# Python setup
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn neo4j chromadb sentence-transformers ollama

# Configure
cp .env.example .env  # Then edit .env

# Start services
neo4j start
ollama serve &
python integrated_api_server.py &
cd frontend && npm install && npm run dev

# Access
# Backend: http://localhost:8001
# Frontend: http://localhost:3000
```

## Support

If you encounter issues:
1. Check the logs in the `logs/` directory
2. Verify all services are running
3. Ensure all dependencies are installed
4. Check environment variables in `.env`

---
Ready to use the complete LLM-powered Knowledge Graph Vector Search System!