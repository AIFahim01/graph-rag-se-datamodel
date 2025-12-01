# 🚀 Run Full 240K Vectorization - Quick Guide

## Two-Step Process

### ✅ **Step 1: Store Data** (3-4 hours in background)
### ✅ **Step 2: Create Indexes** (1-2 minutes after Step 1)

---

## 🔧 **Before Starting - Fix Neo4j Auth:**

### Check Neo4j Password:

```bash
# Try default password first
python -c "from neo4j import GraphDatabase; d=GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'neo4j')); d.verify_connectivity(); print('✅ Connected with neo4j/neo4j')"
```

**If that fails:**
```bash
# Update password in scripts
nano vectorize_and_store.py
# Change line 36: NEO4J_PASSWORD = "your_actual_password"

nano create_indexes.py
# Change line 13: NEO4J_PASSWORD = "your_actual_password"
```

---

## 📊 **STEP 1: Run Vectorization (Background)**

### Option A: Screen (Recommended)

```bash
cd /home/ib3/Documents/test_bp/knowledge_graph_vector_GC_Data

# Launch
./start_vectorization.sh

# Or manually:
screen -S ultrathink_vec
source activate_ultrathink.sh
python vectorize_and_store.py 2>&1 | tee logs/vec_$(date +%Y%m%d_%H%M%S).log

# Detach: Ctrl+A, then D
```

**Monitor (different terminal):**
```bash
# Live progress
tail -f logs/vec_*.log

# Or use monitor
python monitor_vectorization.py
```

**Reattach:**
```bash
screen -r ultrathink_vec
```

---

### Option B: Nohup (If no screen)

```bash
cd /home/ib3/Documents/test_bp/knowledge_graph_vector_GC_Data
source activate_ultrathink.sh

nohup python vectorize_and_store.py > logs/vec_$(date +%Y%m%d_%H%M%S).log 2>&1 &
echo $! > logs/vectorization.pid

# Monitor
tail -f logs/vec_*.log
```

---

## ⏱️ **Expected Timeline for Step 1:**

```
Processing: 240,806 pages
Speed: ~4-5 pages/second
Time: ~3-4 hours

Progress updates every batch (1000 pages):
[15:45:30] BATCH 24/241 (10.0%)
[15:45:30] Pages stored: 24,000/240,806
[15:45:30] ETA: 2h 48m
```

**You can close terminal - it keeps running!**

---

## ✅ **STEP 2: Create Indexes (After Step 1 Complete)**

### Wait for Step 1 to finish:

```bash
# Check if done
tail -20 logs/vec_*.log | grep "COMPLETE"

# Should show:
# ✨ VECTORIZATION DATA STORAGE COMPLETE!
# 🚀 Next step: Run create_indexes.py
```

### Run Index Creation:

```bash
cd /home/ib3/Documents/test_bp/knowledge_graph_vector_GC_Data
source activate_ultrathink.sh

python create_indexes.py
```

**Output:**
```
========================================
ULTRATHINK - Create Neo4j Indexes
========================================

✅ Connected! Found 240,806 PageChunk nodes

📝 Creating Vector Index...
✅ Vector index created (took 45s)

📝 Creating Metadata Indexes...
✅ Created 5 metadata indexes

📝 Creating Fulltext Index (BM25)...
✅ Fulltext index created

✨ ALL INDEXES CREATED SUCCESSFULLY!
```

**Time: 1-2 minutes**

---

## 🔍 **Verify Everything Works:**

### Test Vector Search:
```bash
curl "http://localhost:8001/api/search?q=power&top_k=5"
```

### Test Count Query (Neo4j Browser):
```cypher
// How many HVDC projects?
MATCH (c:PageChunk)
WHERE c.technology = 'HVDC'
RETURN count(DISTINCT c.project_id) as hvdc_count

// Projects by year
MATCH (c:PageChunk)
WHERE c.year IS NOT NULL
RETURN c.year, count(DISTINCT c.project_id) as projects
ORDER BY c.year
```

---

## 📋 **Resume if Interrupted:**

### If vectorization stops (power failure, etc.):

```bash
# Just run again - it resumes automatically!
./start_vectorization.sh

# Or:
python vectorize_and_store.py

# Checkpoint file remembers where it stopped
```

---

## 🐛 **Troubleshooting:**

### Neo4j Connection Error:
```bash
# Check Neo4j is running
sudo systemctl status neo4j

# Start if stopped
sudo systemctl start neo4j

# Check credentials in scripts
```

### Slow Performance:
```bash
# Check GPU/CPU usage
htop

# Check Neo4j memory
# Edit /etc/neo4j/neo4j.conf
# Increase: dbms.memory.heap.max_size=4G
```

---

## ✅ **Complete Workflow:**

```bash
# 1. Fix Neo4j auth (if needed)
# Edit scripts with correct password

# 2. Launch vectorization
./start_vectorization.sh

# 3. Detach and monitor
# Ctrl+A, D
tail -f logs/vec_*.log

# 4. Wait 3-4 hours...

# 5. Create indexes
python create_indexes.py

# 6. Test searches
# Use frontend or API
```

**Simple, safe, resumable!** 🎯
