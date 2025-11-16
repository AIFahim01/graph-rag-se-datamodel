# Neo4j Vector Database Status

## ✅ Current Active Database (in Neo4j)

**Chunks:** 18,437
**PDFs:** 1,082 (GC_2024 + GC_2025)
**Projects:** 61 total
**Created:** November 14, 2025

**Features:**
- ✅ Docling extraction with page tracking attempt
- ✅ GC_2024 (29 projects) + GC_2025 (32 projects)
- ✅ Quality filtering (>100 char chunks)
- ✅ Customer metadata
- ✅ Enhanced query search
- ⚠️ Page numbers: all 0 (parsing issue)

## 📁 Backups

### NEW Database (ACTIVE)
**Location:** `data/neo4j_backups/backup_new_18437_chunks/`
- chunks_with_metadata.json (68 MB)
- embeddings.npy (145 MB)
- Total: 213 MB

**Content:**
- 18,437 chunks
- 1,082 PDFs
- Both 2024 and 2025 data

### OLD Database (ARCHIVED)
**Location:** `data/neo4j_backups/backup_old_25942_chunks/`
- chunks_with_metadata.json (26 MB)
- embeddings.npy (203 MB)
- Total: 229 MB

**Content:**
- 25,942 chunks
- 335 PDFs
- GC_2025 only

## 🔌 Frontend Viewer Integration

**Backend API:** http://localhost:8000
- Enhanced query expansion
- Intent extraction
- Result fusion
- Connected to Neo4j (18,437 chunks)

**Frontend:** http://localhost:3000
- Next.js viewer
- Real-time vector search
- Metadata display

## 📊 Search Quality

**Current (NEW database):**
- Relevance: 87-89%
- Query expansion working
- Intent filters active
- GC24 + GC25 coverage

**Results tested and verified:**
- "syncon" → 10 SynCon projects (correct)
- "TenneT" → 5 TenneT projects (correct)
- "technical" → 87% relevance (excellent)
