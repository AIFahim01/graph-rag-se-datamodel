# Graph RAG System - Quick Reference

## 🚀 Quick Start

### Setup (First Time Only)
```bash
cd /home/ib3/Documents/test_bp/knowledge_graph_vector_GC_Data/graph_check

# Setup Neo4j
./setup_neo4j.sh

# Activate environment
source ../activate_ultrathink.sh
```

---

## 📋 Common Commands

### Test with Sample Data (10 files - FAST)
```bash
python3 main.py --mode full --sample
```

### Run on Full Dataset (25,000+ files - SLOW)
```bash
python3 main.py --mode full
```

### Query Only (After data is loaded)
```bash
python3 main.py --mode query
```

---

## 🔧 Manual Step-by-Step

### Step 1: Chunking
```bash
# Sample (10 files)
python3 main.py --mode chunk --sample

# Full (all files)
python3 main.py --mode chunk
```

### Step 2: Extract Entities
```bash
python3 main.py --mode extract
```

### Step 3: Load to Neo4j
```bash
python3 main.py --mode load
```

### Step 4: Query
```bash
python3 main.py --mode query
```

---

## ❓ Example Questions

Once in query mode, try:
- "How many HVDC projects?"
- "How many SynCon projects?"
- "How many OWF projects?"
- "List all project types"
- "How many entities are in the graph?"

Type `exit` to quit query mode.

---

## 🧪 Test Scripts

### Test Single Query
```bash
python3 test_query.py
```

### Incremental Testing
```bash
./run_incremental_test.sh
```

---

## 📁 Output Files

- `output/chunks.json` - Text chunks from markdown files
- `output/knowledge_graph.json` - Extracted knowledge graph
- Neo4j database - Loaded graph data (query via browser or Python)

---

## 🔍 Neo4j Browser

Access Neo4j at: http://localhost:7474

**Credentials:**
- Username: `neo4j`
- Password: `siemensenergy`

**Sample Cypher Queries:**
```cypher
// Count all projects
MATCH (p:Project) RETURN count(p)

// Count HVDC projects
MATCH (p:Project {type: 'HVDC'}) RETURN count(p)

// List all project types
MATCH (p:Project) RETURN DISTINCT p.type, count(p) as count

// Show all entities
MATCH (e:Entity) RETURN e.name, e.mention_count LIMIT 20

// Show relationships
MATCH (s:Entity)-[r:RELATION]->(o:Entity)
RETURN s.name, r.type, o.name LIMIT 20
```

---

## ⚙️ Configuration

Edit `config.py` to customize:

```python
# Data source
DATA_SOURCE = Path("/path/to/markdown/files")

# Neo4j
NEO4J_PASSWORD = "siemensenergy"

# LLM
LLM_MODEL = "qwen3:8b"

# Chunking
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Use simple extractor (no ReLiK)
USE_SIMPLE_EXTRACTOR = True
```

---

## 🐛 Troubleshooting

### Neo4j Connection Error
```bash
# Check if running
docker ps | grep neo4j

# Restart Neo4j
./setup_neo4j.sh
```

### Ollama Not Available
```bash
# Check if running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve
```

### Permission Errors
```bash
chmod +x *.sh
chmod +x *.py
```

---

## 📊 Performance

- **Sample Mode (10 files):** ~2-5 minutes
- **Full Mode (25,000 files):** ~1-3 hours
- **Query Time:** ~2-5 seconds per question

---

## 🎯 Workflow

```
1. Setup Neo4j          → ./setup_neo4j.sh
2. Activate env         → source ../activate_ultrathink.sh
3. Test with sample     → python3 main.py --mode full --sample
4. Query                → python3 main.py --mode query
5. Run full (optional)  → python3 main.py --mode full
```
