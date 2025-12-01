# ⚡ ULTRATHINK Quick Start Guide

## 1️⃣ Setup Conda Environment (FIRST TIME ONLY)

```bash
cd /home/ib3/Documents/test_bp/knowledge_graph_vector_GC_Data

# Run setup script (takes ~5-10 minutes)
./setup_ultrathink_conda.sh
```

---

## 2️⃣ Activate Environment

```bash
conda activate ultrathink
```

---

## 3️⃣ Run Test Vectorization

```bash
# Process GC21_001 project (~50-100 pages, takes 2-5 minutes)
python build_vectordb_test_small.py
```

**Expected Output:**
```
✨ TEST VECTORIZATION COMPLETE!
   Pages processed: ~50-100
   Neo4j Label: PageChunk
   Index: page_embeddings_ultrathink
```

---

## 4️⃣ Start Test Backend (Terminal 1)

```bash
# Keep this terminal open
python graph-rag-se-datamodel/frontend_viewer/backend/api_server_test.py
```

**Expected Output:**
```
🚀 ULTRATHINK TEST API SERVER
Port: 8001
```

---

## 5️⃣ Start Test Frontend (Terminal 2)

```bash
cd graph-rag-se-datamodel/frontend_viewer/frontend

# Create test config
echo "NEXT_PUBLIC_API_URL=http://localhost:8001" > .env.local

# Start on port 3001
PORT=3001 npm run dev
```

**Visit:** http://localhost:3001

---

## 🔍 Verify Test System

### Check Backend Health
```bash
curl http://localhost:8001/api/health
```

### Check Neo4j Data
```bash
# Open Neo4j Browser: http://localhost:7474

# Old data (untouched):
MATCH (c:Chunk) RETURN count(c)  # 18,437

# New test data:
MATCH (c:PageChunk) RETURN count(c)  # ~50-100
```

---

## 📊 System Overview

| Component | Port | Status |
|-----------|------|--------|
| **Production Frontend** | 3000 | ✅ Untouched |
| **Production Backend** | 8000 | ✅ Untouched |
| **Test Frontend** | 3001 | 🆕 New |
| **Test Backend** | 8001 | 🆕 New |
| **Neo4j** | 7687 | Both systems |

---

## 🐛 Troubleshooting

### Conda environment not found
```bash
conda env list  # Check if ultrathink exists
conda activate ultrathink
```

### Backend can't connect to Neo4j
```bash
# Check Neo4j is running
systemctl status neo4j
# OR
sudo neo4j status
```

### Frontend can't connect to backend
```bash
# Check backend is running on port 8001
curl http://localhost:8001/api/health

# Check .env.local file exists
cat graph-rag-se-datamodel/frontend_viewer/frontend/.env.local
```

### No search results
```bash
# Verify vectorization completed
# Neo4j: MATCH (c:PageChunk) RETURN count(c)
```

---

## 📖 Full Documentation

- **Setup Details:** `RUN_ULTRATHINK_TEST.md`
- **Architecture:** See diagrams in docs
- **Conda Setup:** `setup_ultrathink_conda.sh`

---

## 💡 Quick Commands Cheatsheet

```bash
# Activate environment
conda activate ultrathink

# Run vectorization
python build_vectordb_test_small.py

# Start backend (terminal 1)
python graph-rag-se-datamodel/frontend_viewer/backend/api_server_test.py

# Start frontend (terminal 2)
cd graph-rag-se-datamodel/frontend_viewer/frontend && PORT=3001 npm run dev

# Check health
curl http://localhost:8001/api/health

# Check Neo4j test data
# Browser: MATCH (c:PageChunk) RETURN c LIMIT 10
```
