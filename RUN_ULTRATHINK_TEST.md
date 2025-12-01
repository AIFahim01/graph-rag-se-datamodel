# ULTRATHINK Test Setup - Page-by-Page Vectorization

## Overview
Test the new page-by-page vectorization system with **one project** (GC21_001_CCPP_Dils) before scaling to 240K pages.

## System Architecture

```
┌─────────────────────────────────────────────────────┐
│ PRODUCTION (Running - DO NOT STOP)                  │
├─────────────────────────────────────────────────────┤
│ Frontend: http://localhost:3000                     │
│ Backend:  http://localhost:8000                     │
│ Neo4j:    Label="Chunk", Index="chunk_embeddings"   │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ TEST (New System)                                    │
├─────────────────────────────────────────────────────┤
│ Frontend: http://localhost:3001                     │
│ Backend:  http://localhost:8001                     │
│ Neo4j:    Label="PageChunk", Index="page_embeddings"│
└─────────────────────────────────────────────────────┘
```

---

## Step 1: Run Vectorization (Test Data)

```bash
cd /home/ib3/Documents/test_bp/knowledge_graph_vector_GC_Data

# Make script executable
chmod +x build_vectordb_test_small.py

# Run test vectorization (GC21_001 only, ~50-100 pages)
python3 build_vectordb_test_small.py
```

**Expected Output:**
```
✨ TEST VECTORIZATION COMPLETE!
========================================
📊 Statistics:
   Project: GC21_001_CCPP_Dils
   Pages processed: ~50-100
   Chunks created: ~50-100
   Processing time: ~2-5 minutes

🔍 Neo4j Details:
   Node label: PageChunk
   Index name: page_embeddings_ultrathink
   Old data: UNTOUCHED (still using 'Chunk' label)
```

---

## Step 2: Start Test Backend (Port 8001)

```bash
cd /home/ib3/Documents/test_bp/knowledge_graph_vector_GC_Data/graph-rag-se-datamodel/frontend_viewer/backend

# Start test backend
python3 api_server_test.py
```

**Verify it's running:**
- Visit: http://localhost:8001/docs
- Check health: http://localhost:8001/api/health

---

## Step 3: Configure Frontend for Test

### Option A: Use Existing Frontend on Port 3001

```bash
cd /home/ib3/Documents/test_bp/knowledge_graph_vector_GC_Data/graph-rag-se-datamodel/frontend_viewer/frontend

# Create test .env file
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8001
EOF

# Start on port 3001 (production on 3000 keeps running)
PORT=3001 npm run dev
```

### Option B: Update API URL Temporarily

Edit the frontend code to point to port 8001:
```typescript
// In your API calls, change:
const API_URL = "http://localhost:8001"  // Test backend
```

---

## Step 4: Test the System

### Visit Test Frontend
http://localhost:3001

### Test Searches
1. **Basic search**: `grid compliance`
2. **Customer filter**: `TenneT projects`
3. **Technology**: `HVDC protection systems`

### Verify Results Show:
- ✅ Page number (e.g., "Page 1 of 2")
- ✅ Page thumbnail/image preview
- ✅ Metadata from metadata.json (total_pages, total_images, total_tables)
- ✅ Project info (GC21_001_CCPP_Dils)

---

## Step 5: Verify Data Separation

### Check Neo4j has BOTH systems:

```bash
# Open Neo4j Browser: http://localhost:7474

# Query OLD system (untouched):
MATCH (c:Chunk) RETURN count(c)
# Should return: 18,437

# Query NEW test system:
MATCH (c:PageChunk) RETURN count(c)
# Should return: ~50-100 (test data)

# View test data:
MATCH (c:PageChunk) RETURN c LIMIT 5
```

---

## Port Summary

| Service | Port | Status |
|---------|------|--------|
| **Production Frontend** | 3000 | ✅ Keep Running |
| **Production Backend** | 8000 | ✅ Keep Running |
| **Test Frontend** | 3001 | 🆕 New |
| **Test Backend** | 8001 | 🆕 New |
| **Neo4j** | 7687 | ✅ Both systems |

---

## Troubleshooting

### If frontend can't connect to backend:
```bash
# Check backend is running:
curl http://localhost:8001/api/health

# Check CORS settings allow localhost:3001
```

### If no search results:
```bash
# Verify Neo4j has PageChunk nodes:
# Neo4j Browser: MATCH (c:PageChunk) RETURN count(c)

# Check index exists:
# Neo4j Browser: SHOW INDEXES
```

### If images don't display:
```bash
# Verify image path exists:
ls -la output/GC_2021/GC21_001_CCPP_Dils/.../pages/

# Check backend image endpoint:
curl http://localhost:8001/api/page-image/GC_2021/.../page%201.png
```

---

## Next Steps (After Test Success)

✅ When test works well, tell Claude to:
1. Create full vectorization script for all 240K pages
2. Production deployment plan
3. Switch production frontend to new system

---

## Quick Commands Reference

```bash
# Run test vectorization
python3 build_vectordb_test_small.py

# Start test backend (terminal 1)
python3 frontend_viewer/backend/api_server_test.py

# Start test frontend (terminal 2)
cd frontend_viewer/frontend && PORT=3001 npm run dev

# Check Neo4j
# Browser: http://localhost:7474
# Query: MATCH (c:PageChunk) RETURN c LIMIT 10
```
