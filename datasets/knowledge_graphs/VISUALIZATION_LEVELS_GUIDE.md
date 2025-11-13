# Knowledge Graph Visualization Levels Guide

## 📊 All Visualizations Created (5 Levels)

All files in: `C:\Users\User\PycharmProjects\pdf-to-graphrag\datasets\knowledge_graphs\`

---

## Level 1: Simple Test (Minimal) 🟢 Simplest

**File:** `simple_project_relations.html` (4.4 KB)

**What it shows:**
- 3 project boxes only
- 4 basic connections
- No entities, no details

**Nodes:** 3
**Edges:** 4

**Use when:** Quick test to verify graph works

**Visual:**
```
[Alpha] ──── [Beta] ──── [Gamma]
```

---

## Level 2: Project Relationships (Semantic) 🟡 Project-Level

**File:** `project_relationships_interactive.html` (18 KB) ⭐ Updated

**What it shows:**
- 3 project boxes (large)
- Top 5 entities from each project
- 10 semantic relationships (DATABASE, ANALYTICS, CLOUD, etc.)
- Aggregated connections

**Nodes:** 18 (3 projects + 15 top entities)
**Edges:** 18

**Use when:** Understanding how projects relate by technology categories

**Visual:**
```
[Alpha] ──DATABASE + ANALYTICS──> [Beta]
   │
   └──ANALYTICS + SECURITY──> [Gamma]
                                  │
                    CLOUD + ANALYTICS + INTEGRATION
```

---

## Level 3: Cross-Project Entities Only 🟠 Entity-Focused

**File:** `cross_project_entities_interactive.html` (9.3 KB)

**What it shows:**
- 3 project boxes
- ONLY entities appearing in 2+ projects (2 gold stars)
- Chunk connections via shared entities

**Nodes:** 5 (3 projects + 2 cross-project entities)
**Edges:** ~8

**Use when:** Finding REAL shared technologies (Kubernetes!)

**Visual:**
```
[Alpha] (isolated)

[Beta] ──> ★ Kubernetes ★ <── [Gamma]
```

---

## Level 4: Chunk-Level Connections 🔵 Chunk-Level

**File:** `chunk_to_chunk_connections.html` (16 KB)

**What it shows:**
- 3 project boxes
- 2 cross-project entities (gold stars)
- ~6 specific chunks mentioning those entities
- ORANGE lines showing chunk ↔ chunk connections

**Nodes:** ~11 (3 projects + 2 entities + 6 chunks)
**Edges:** ~16

**Use when:** Seeing which SPECIFIC chunks from different projects connect

**Visual:**
```
[Beta]
  ├─ chunk_1 ──> ★ Kubernetes ★ <── chunk_4 ─┤
  │                                          │
                                        [Gamma]

Chunk-to-chunk connection via Kubernetes!
```

---

## Level 5: Comprehensive (Everything!) 🔴 Complete View

**File:** `comprehensive_knowledge_graph.html` (Latest) ⭐⭐⭐ **RECOMMENDED**

**What it shows:**
- ALL 97 entities from all projects
- ALL 59 triplet relationships
- Internal project relationships (colored)
- Cross-project relationships (ORANGE)
- Gold stars for shared entities

**Nodes:** 97 (all entities)
**Edges:** 59 (all relationships)
- 53 within-project (colored by project)
- 6 cross-project (ORANGE - highlighted!)

**Use when:** Complete exploration, seeing everything at once

**Visual:**
```
Alpha Cluster (RED - 36 entities):
  SAP ──> S/4HANA ──> ERP ──> procurement
   │        │         │
  HANA ──analytics──data protection
  [All internal connections shown]

Beta Cluster (TEAL - 29 entities):
  AWS ──> RDS ──> database
   │       │
  EKS ──> ★Kubernetes★ ←──[ORANGE]──┐
   │       │                        │
  migration services                │
  [All internal connections shown]  │
                                    │
Gamma Cluster (MINT - 34 entities): │
  Kafka ──> Spark ──> TensorFlow    │
   │         │                      │
  ★Kubernetes★ ←────────────────────┘
   │         │
  FastAPI ──> microservices
  [All internal connections shown]

ORANGE edges = Cross-project!
```

---

## 🎯 Quick Reference: Which File to Open?

| Your Goal | File to Open | Nodes | Edges |
|-----------|--------------|-------|-------|
| **See everything** | `comprehensive_knowledge_graph.html` ⭐⭐⭐ | 97 | 59 |
| Project tech similarities | `project_relationships_interactive.html` | 18 | 18 |
| Find shared entities | `cross_project_entities_interactive.html` | 5 | 8 |
| Chunk-level detail | `chunk_to_chunk_connections.html` | 11 | 16 |
| Quick test | `simple_project_relations.html` | 3 | 4 |

---

## ⭐ RECOMMENDED: Open the Comprehensive Graph!

```
C:\Users\User\PycharmProjects\pdf-to-graphrag\datasets\knowledge_graphs\comprehensive_knowledge_graph.html
```

**This has:**
- ✅ **97 nodes** - All entities from all projects
- ✅ **59 edges** - All triplet relationships
- ✅ **Internal relationships** - See how entities connect within each project
- ✅ **Cross-project connections** - 6 ORANGE edges highlighting shared entities
- ✅ **Color-coded clusters** - Red (Alpha), Teal (Beta), Mint (Gamma)
- ✅ **Gold stars** - Kubernetes and date (cross-project entities)

---

## 🔍 What to Look For

### In Comprehensive Graph:

1. **Red Cluster (top/left)** - Alpha ERP System
   - SAP, HANA, S/4HANA, ERP entities connected
   - All internal red edges

2. **Teal Cluster (middle)** - Beta Cloud Migration
   - AWS, Kubernetes, RDS, migration entities
   - Contains **Kubernetes gold star**
   - Has ORANGE edges going to/from Kubernetes

3. **Mint Cluster (bottom/right)** - Gamma Analytics
   - Kafka, Spark, TensorFlow, Kubernetes entities
   - Contains **Kubernetes gold star**
   - Has ORANGE edges going to/from Kubernetes

4. **ORANGE thick edges** - Cross-project connections
   - Connect entities that appear in multiple projects
   - Width 4 (thicker than internal edges)
   - These are the cross-project relationships!

---

## 💡 Pro Tips

1. **Start zoomed OUT** - See the 3 clusters
2. **Look for GOLD STARS** - These are shared entities
3. **Follow ORANGE edges** - These cross project boundaries
4. **Zoom into clusters** - Explore internal relationships
5. **Hover everything** - See source PDF, page, chunk info

---

**ANSWER: Open `comprehensive_knowledge_graph.html` for the complete view with all levels!** 🎨
