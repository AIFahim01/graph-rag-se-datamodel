# Quick Start Guide - Run the Complete System

## Prerequisites

- Docker installed and running
- Python 3.10+
- WSL or Linux environment

## 🚀 Complete System Setup (10 minutes)

### Step 1: Start Infrastructure (1 min)

```bash
# Start ChromaDB and Neo4j
docker ps | grep chromadb  # Check if already running
docker ps | grep neo4j

# If not running, start them:
docker run -d --name neo4j-graphrag -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=none neo4j:latest
```

### Step 2: Install Dependencies (2 min)

```bash
pip install -r requirements.txt
```

### Step 3: Process Your PDFs (3 min)

**Option A: Use Example Data (Dummy PDFs already created)**
```bash
# Check example projects
python scripts/dataset_stats.py

# Process all projects
python scripts/process_project.py --all
```

**Option B: Add Your Own PDFs**
```bash
# Create project folder
mkdir -p datasets/projects/my_project

# Copy your PDFs
cp /path/to/your/*.pdf datasets/projects/my_project/

# Process
python scripts/process_project.py --project my_project
```

### Step 4: Build Knowledge Graph (2 min)

```bash
# Extract entities and relationships using REBEL
python scripts/build_knowledge_graph_rebel_with_metadata.py --all

# Build unified cross-project graph
python scripts/build_unified_knowledge_graph.py
```

### Step 5: Generate Embeddings (2 min)

```bash
# Create vector embeddings for all chunks
python scripts/generate_embeddings.py
```

### Step 6: Load into Databases (1 min)

```bash
# Load vectors into ChromaDB
python scripts/load_into_chromadb.py

# Load knowledge graph into Neo4j
python scripts/load_into_neo4j.py
```

### Step 7: Test the System (1 min)

```bash
# Verify everything works
python scripts/test_system.py
```

**Expected Output:**
```
✅ ChromaDB Test PASSED
✅ Neo4j Test PASSED
🎉 ALL TESTS PASSED! System is ready!
```

### Step 8: Start Chatting! 🎉

```bash
# Interactive chat mode
python scripts/chat_graphrag.py --interactive --deployment gpt-4.1
```

**Try these questions:**
- "What database technologies are mentioned?"
- "Which projects use Kubernetes?"
- "What is SAP S/4HANA?"

---

## 📋 Quick Commands Reference

```bash
# ============================================================
# DATA MANAGEMENT
# ============================================================

# Check dataset statistics
python scripts/dataset_stats.py

# Process all projects
python scripts/process_project.py --all

# Process specific project
python scripts/process_project.py --project alpha_erp_system

# ============================================================
# KNOWLEDGE GRAPH
# ============================================================

# Build KG with REBEL (without metadata)
python scripts/build_knowledge_graph_rebel.py --all

# Build KG with REBEL (with metadata - RECOMMENDED)
python scripts/build_knowledge_graph_rebel_with_metadata.py --all

# Build unified cross-project KG
python scripts/build_unified_knowledge_graph.py

# Visualize knowledge graphs
python scripts/visualize_knowledge_graph.py --all

# Create interactive graphs
python scripts/create_comprehensive_graph.py
python scripts/create_visible_graph.py

# ============================================================
# EMBEDDINGS & STORAGE
# ============================================================

# Generate vector embeddings
python scripts/generate_embeddings.py

# Load into ChromaDB
python scripts/load_into_chromadb.py

# Load into Neo4j
python scripts/load_into_neo4j.py

# Test both databases
python scripts/test_system.py

# ============================================================
# CHAT & QUERY
# ============================================================

# Interactive chat
python scripts/chat_graphrag.py --interactive --deployment gpt-4.1

# Single question
python scripts/chat_graphrag.py --query "What are the database technologies?" --deployment gpt-4.1

# More results
python scripts/chat_graphrag.py --query "..." --deployment gpt-4.1 --top-k 10

# ============================================================
# VISUALIZATIONS
# ============================================================

# Open these in browser:
datasets/knowledge_graphs/HIGHLY_VISIBLE_graph.html
datasets/knowledge_graphs/comprehensive_knowledge_graph.html
datasets/knowledge_graphs/project_relationships_interactive.html

# ============================================================
# SERVICES
# ============================================================

# Check Docker services
docker ps

# Neo4j browser
open http://localhost:7474

# RabbitMQ management (if using microservices)
open http://localhost:15672
```

---

## 🎯 Typical Workflows

### Workflow 1: Quick Demo (5 min)

```bash
# Already have data? Just chat!
python scripts/chat_graphrag.py --interactive --deployment gpt-4.1
```

### Workflow 2: Fresh Start with Your PDFs (15 min)

```bash
# 1. Add your PDFs
mkdir -p datasets/projects/my_project
cp /path/to/pdfs/*.pdf datasets/projects/my_project/

# 2. Process everything
python scripts/process_project.py --all
python scripts/build_knowledge_graph_rebel_with_metadata.py --all
python scripts/generate_embeddings.py
python scripts/load_into_chromadb.py
python scripts/load_into_neo4j.py

# 3. Test
python scripts/test_system.py

# 4. Chat
python scripts/chat_graphrag.py --interactive --deployment gpt-4.1
```

### Workflow 3: Visualize Knowledge Graph Only

```bash
# Build KG
python scripts/build_knowledge_graph_rebel_with_metadata.py --all

# Create visualization
python scripts/create_visible_graph.py

# Open
datasets/knowledge_graphs/HIGHLY_VISIBLE_graph.html
```

---

## 🐛 Troubleshooting

### "Module not found" errors

```bash
# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "from src.embeddings import VectorGenerator; print('OK')"
```

### "Connection refused" to ChromaDB

```bash
# Check if running
docker ps | grep chroma

# Start if not running
docker run -d --name chromadb -p 8002:8000 chromadb/chroma:latest

# Update .env to use port 8002
CHROMADB_PORT=8002
```

### "Connection refused" to Neo4j

```bash
# Check if running
docker ps | grep neo4j

# Start if not running
docker run -d --name neo4j-graphrag -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=none neo4j:latest

# Wait 20 seconds for startup
sleep 20
```

### Chat deployment not found

```bash
# Try different deployment names
python scripts/chat_graphrag.py --query "..." --deployment gpt-4.1
python scripts/chat_graphrag.py --query "..." --deployment gpt-35-turbo
python scripts/chat_graphrag.py --query "..." --deployment gpt-4-turbo
```

---

## 📊 System Status Check

```bash
# Quick health check
docker ps | grep -E "chroma|neo4j"      # Should show 2 containers
python scripts/test_system.py           # Should pass both tests
ls datasets/embeddings/*.npy            # Should show embeddings file
```

---

## 🎨 For Client Presentation

```bash
# 1. Open visualization
datasets/knowledge_graphs/HIGHLY_VISIBLE_graph.html

# 2. Open documentation
docs/guides/EXECUTIVE_SUMMARY.md

# 3. Start chat demo
python scripts/chat_graphrag.py --interactive --deployment gpt-4.1

# Demo queries:
# - "What database technologies are mentioned?"
# - "Which projects use Kubernetes?"
# - "What is SAP S/4HANA?"
```

---

## ⚙️ Environment Setup

Make sure `.env` has these configured:

```bash
# Azure OpenAI
AZURE_API_KEY=your_key
AZURE_API_BASE=your_endpoint
AZURE_API_VERSION=2025-01-01-preview

# ChromaDB (local)
CHROMADB_HOST=localhost
CHROMADB_PORT=8002

# Neo4j (local, no auth)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=
NEO4J_PASSWORD=
```

---

**Your system is ready to run! Start with Step 1 and you'll be chatting with your documents in 10 minutes.** 🚀
