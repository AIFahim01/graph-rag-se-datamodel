# How to Run the System Yourself

## 🚀 Quick Start

### 1. Start Neo4j (if not running)
```bash
docker start neo4j-vector-test
# Or if you need to create it:
docker run -d --name neo4j-vector-test -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=none neo4j:5.26-community
```

### 2. Start Backend API
```bash
cd /mnt/c/Users/z0051yym/Desktop/test_bp_code/knowledge_graph_vector_GC_Data/graph-rag-se-datamodel

# Activate conda environment
conda activate hdvc_syncon_vectordb

# Start backend
python frontend_viewer/backend/api_server.py

# Backend runs on: http://localhost:8000
# Press Ctrl+C to stop
```

### 3. Start Frontend (in new terminal)
```bash
cd /mnt/c/Users/z0051yym/Desktop/test_bp_code/knowledge_graph_vector_GC_Data/graph-rag-se-datamodel/frontend_viewer/frontend

# Load Node 20
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm use 20

# Start frontend
npm run dev

# Frontend runs on: http://localhost:3000
# Press Ctrl+C to stop
```

---

## 🔍 Check What's Running

```bash
# Check Neo4j
docker ps | grep neo4j

# Check backend API
ps aux | grep api_server

# Check frontend
ps aux | grep "next dev"

# Check ports
lsof -i :7687  # Neo4j
lsof -i :8000  # Backend
lsof -i :3000  # Frontend
```

---

## 🛠️ Troubleshooting

### Backend Won't Start
```bash
# Check error log
tail -50 backend_final.log

# Check if port 8000 is busy
lsof -i :8000
# If busy: kill $(lsof -t -i:8000)

# Test backend directly
curl http://localhost:8000/api/health
```

### Frontend Won't Start
```bash
# Make sure Node 20 is active
node --version  # Should be v20.x.x

# If not, activate nvm
nvm use 20

# Check if port 3000 is busy
lsof -i :3000
# If busy: kill $(lsof -t -i:3000)
```

### Neo4j Connection Failed
```bash
# Check Neo4j is running
docker ps | grep neo4j

# Start if stopped
docker start neo4j-vector-test

# Check logs
docker logs neo4j-vector-test --tail 50
```

---

## 📊 Database Info

**Current Database:**
- Chunks: 18,437
- PDFs: 1,082 (GC_2024 + GC_2025)
- Projects: 61

**Backup Location:**
```
data/neo4j_backups/backup_new_18437_chunks/backup_20251114_085150/
├── chunks_with_metadata.json (68 MB)
└── embeddings.npy (145 MB)
```

**Restore if needed:**
```bash
python scripts/utils/restore_neo4j_backup.py
```

---

## 🌐 Access Points

- **Frontend UI:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Neo4j Browser:** http://localhost:7474

---

## 🔄 Restart Everything

```bash
# Stop all
docker stop neo4j-vector-test
pkill -f api_server
pkill -f "next dev"

# Start all
docker start neo4j-vector-test
cd frontend_viewer/backend && python api_server.py &
cd frontend_viewer/frontend && npm run dev
```

---

## 📝 Search Examples

- "TenneT" → Find TenneT projects
- "HVDC protection" → Technical docs
- "syncon" → Synchronous condenser projects
- "how many technical" → Count technical documents

---

## ⚠️ Important Notes

- **Backend must run first** (before frontend)
- **Neo4j must be running** (before backend)
- **Use Node 20+** (not Node 18)
- **Conda env required** for backend (hdvc_syncon_vectordb)
