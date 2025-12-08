# 💾 Ultrathink Embedding Backup Guide

## Why Backup Embeddings?

**Embeddings are expensive to generate:**
- 240,806 pages × ~0.5 sec each = **33+ hours CPU time**
- If Neo4j crashes or data corrupted = **Start over from scratch!**

**With backup:**
- Restore in ~5 minutes
- No re-embedding needed
- Data safety guaranteed

---

## 📦 Backup Strategy

### Option 1: Backup After Vectorization Completes (Recommended)

**When:** After `vectorize_and_store.py` finishes all 240K pages

**Command:**
```bash
cd /home/ib3/Documents/test_bp/knowledge_graph_vector_GC_Data
source activate_ultrathink.sh
python backup_embeddings.py
```

**Creates:**
```
backups/ultrathink_backup_20251128_153045/
├── chunks_metadata.json      (~150 MB - all chunk data)
├── embeddings.npy            (~980 MB - all 240K embeddings)
├── chunk_to_index.json       (~50 MB - mapping)
└── backup_info.json          (~1 KB - metadata)

Total: ~1.2 GB
```

**Benefits:**
- ✅ Complete backup
- ✅ One-time operation
- ✅ Fast restore if needed

---

### Option 2: Periodic Backups (During Vectorization)

**When:** Every N batches while vectorization is running

**Schedule:**
```bash
# In another terminal, run every hour:
while true; do
  sleep 3600  # 1 hour
  python backup_embeddings.py
done
```

**Creates:**
```
backups/
├── ultrathink_backup_20251128_130000/  (after 1 hour - 30K pages)
├── ultrathink_backup_20251128_140000/  (after 2 hours - 60K pages)
├── ultrathink_backup_20251128_150000/  (after 3 hours - 90K pages)
└── ultrathink_backup_20251128_160000/  (complete - 240K pages)
```

**Benefits:**
- ✅ Multiple restore points
- ✅ Resume from any point if something fails
- ⚠️ Uses more disk space

---

## 💾 Backup File Structure

### chunks_metadata.json
```json
[
  {
    "chunk_id": "GC21_001_Doc_page1",
    "text": "page content...",
    "page": 1,
    "project_id": "GC21_001",
    "year": 2021,
    "customer": "TenneT",
    "technology": "HVDC",
    "embedding_index": 0
  },
  ...
]
```

### embeddings.npy
```
NumPy array shape: (240806, 1024)
Type: float32
Size: ~980 MB

# Load with:
embeddings = np.load('embeddings.npy')
# embeddings[0] = embedding for chunk_id at index 0
```

---

## 🔄 How to Restore

### Scenario 1: Neo4j Data Loss

```bash
# Restore from backup
python restore_embeddings.py backups/ultrathink_backup_20251128_153045

# Then create indexes
python create_indexes.py

# System fully restored!
```

**Time:** ~5 minutes for 240K pages

---

### Scenario 2: Partial Restore (Test)

```bash
# Want to restore just 10K pages for testing?
# Edit restore_embeddings.py line with LIMIT or use checkpoint.json
```

---

## 📊 Backup Sizes (240,806 pages)

| File | Size | Content |
|------|------|---------|
| **chunks_metadata.json** | ~150 MB | Text + metadata |
| **embeddings.npy** | ~980 MB | 240K × 1024 float32 |
| **chunk_to_index.json** | ~50 MB | ID mapping |
| **backup_info.json** | ~1 KB | Backup metadata |
| **Total** | **~1.2 GB** | Complete backup |

**Fits easily on any disk!**

---

## 🚀 Recommended Workflow

### During Vectorization (Now):
```bash
# Terminal 1: Vectorization running in screen
screen -r ultrathink_vec  # Watch progress

# Terminal 2: Monitor
tail -f logs/vec_*.log
```

### After Vectorization Complete (~9 hours):
```bash
# Step 1: Backup embeddings
python backup_embeddings.py

# Step 2: Create indexes
python create_indexes.py

# Step 3: Test search
# Use frontend or API

# Done!
```

---

## 💡 Best Practices

### Regular Backups:
```bash
# After major milestones
- After full vectorization: BACKUP
- After adding new data: BACKUP
- Before Neo4j upgrades: BACKUP
- Weekly: BACKUP
```

### Backup Location:
```bash
# Local backup (default)
backups/

# External backup (safer)
cp -r backups/ /mnt/external_drive/ultrathink_backups/

# Cloud backup
aws s3 sync backups/ s3://your-bucket/ultrathink/
```

---

## ⚡ Quick Commands

```bash
# Backup now
python backup_embeddings.py

# Restore from backup
python restore_embeddings.py backups/ultrathink_backup_TIMESTAMP

# List backups
ls -lh backups/

# Delete old backups (keep latest 3)
cd backups && ls -t | tail -n +4 | xargs rm -rf
```

---

## 🛡️ Disaster Recovery

**If Neo4j crashes:**
1. Fix Neo4j
2. `python restore_embeddings.py backups/latest`
3. `python create_indexes.py`
4. Back online in 5 minutes!

**Much better than re-vectorizing for 9 hours!**
