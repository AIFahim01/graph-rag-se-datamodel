# 🔬 Knowledge Graph Comparison & Recommendations

**Research Date**: 2025-11-11
**Based on**: ACL 2024, Neo4j GraphRAG, Microsoft GraphRAG, Latest Research

---

## 📊 Part 1: ReLiK vs REBEL Comparison

### **Overview**

| Feature | REBEL (2021) | ReLiK (ACL 2024) |
|---------|--------------|------------------|
| **Team** | Babelscape/Sapienza | Sapienza NLP Group |
| **Architecture** | Autoregressive Seq2Seq | Retriever-Reader |
| **Speed** | Baseline | **40x faster** |
| **Performance** | State-of-art (2021) | **Current SOTA** |
| **Inference** | Sequential generation | Single forward pass |
| **Best For** | Research, flexibility | **Production, scale** |

---

### **REBEL Architecture (Your Current System)**

```
Input Text → Transformer Encoder → Autoregressive Decoder → Triplets
              (BART-large)         (Sequential generation)    (subject, relation, object)
```

**Advantages**:
- ✅ End-to-end learning
- ✅ Flexible relation extraction
- ✅ No predefined entity/relation types needed

**Disadvantages**:
- ❌ **Slow inference** (autoregressive = sequential)
- ❌ Generates triplets token-by-token
- ❌ Several orders of magnitude slower than ReLiK
- ❌ Not suitable for large-scale production

**Your Results with REBEL**:
- Entities: 1,674 (filtered from 6,447)
- Relationships: 12,522
- **Issue**: Noisy entities with XML tags (`</s`, `<obj>`)

---

### **ReLiK Architecture (Recommended)**

```
Input Text → RETRIEVER → READER → Entities + Relations
             (Find candidates)  (Link & extract)  (Single pass)
```

**3-Step Process**:
1. **Retrieve**: Identify candidate entities/relations
2. **Read**: Contextualize text and candidates
3. **Link**: Extract entities and triplets

**Advantages**:
- ✅ **40x faster** than REBEL/autoregressive methods
- ✅ State-of-the-art accuracy (current SOTA on REBEL benchmark)
- ✅ Single forward pass (no sequential generation)
- ✅ Entity linking to knowledge bases (Wikipedia, Wikidata)
- ✅ Production-ready (academic budget training)
- ✅ Available on HuggingFace: `sapienzanlp/relik-entity-linking-large`

**Disadvantages**:
- ⚠️ Newer (2024) - less battle-tested
- ⚠️ Requires entity/relation candidates retrieval step

---

### **Performance Benchmarks**

| Metric | REBEL | ReLiK |
|--------|-------|-------|
| **Speed** | 1x (baseline) | **40x faster** |
| **F1 Score (REBEL dataset)** | ~85% | **State-of-the-art** |
| **Inference Type** | Autoregressive | Single-pass |
| **Entity Linking** | No | **Yes (to KB)** |
| **Production Ready** | Research | **Yes** |

**ReLiK is current SOTA on the REBEL benchmark itself!**

---

### **Recommendation: Which to Use?**

| Use Case | Recommendation |
|----------|----------------|
| **Your HVDC/SYNCON system** | **ReLiK** |
| Large-scale extraction (10k+ docs) | **ReLiK** (40x faster) |
| Real-time extraction | **ReLiK** |
| Research/experimentation | REBEL |
| Need entity linking to Wikipedia | **ReLiK only** |
| Budget constraints | **ReLiK** (academic budget) |

**Verdict**: **Switch to ReLiK** for better speed, accuracy, and cleaner entity extraction.

---

## 📦 Part 2: Chunk-Level vs Document-Level Graphs

### **Current Status: Your Graph is Document-Level**

**What you have now**:
```
Project → mentions → Entity
Entity → RELATED → Entity
```

**Missing**:
- ❌ No chunk tracking
- ❌ No provenance (which chunk mentioned which entity?)
- ❌ No document metadata
- ❌ Cannot trace entity back to source text

---

### **Industry Best Practice: Hierarchical Chunk-Level Graph**

Based on **Microsoft GraphRAG** and **Neo4j GraphRAG** (2024):

```
┌─────────────────────────────────────────────────────┐
│                    Document                         │
│   (name, source, path, date)                        │
└─────────────────────────────────────────────────────┘
                      ↓ HAS_CHUNK
        ┌─────────────┬─────────────┬─────────────┐
        │   Chunk 1   │   Chunk 2   │   Chunk 3   │
        │ (text, idx) │ (text, idx) │ (text, idx) │
        └─────────────┴─────────────┴─────────────┘
              ↓              ↓              ↓
           MENTIONS       MENTIONS       MENTIONS
              ↓              ↓              ↓
        ┌─────────────┬─────────────┬─────────────┐
        │   Entity A  │   Entity B  │   Entity C  │
        │ (name, desc)│ (name, desc)│ (name, desc)│
        └─────────────┴─────────────┴─────────────┘
              └──────── RELATED ─────────┘
```

**Key Relationships**:
- `Document -[HAS_CHUNK]-> Chunk`
- `Chunk -[MENTIONS {start, end}]-> Entity`
- `Chunk -[HAS_EMBEDDING]-> Vector`
- `Entity -[RELATED {type, confidence}]-> Entity`
- `Entity -[IN_COMMUNITY]-> Community`

---

### **Why Chunk-Level Graphs?**

| Benefit | Explanation |
|---------|-------------|
| **Provenance** | Know exactly which chunk mentioned each entity |
| **Context** | Retrieve surrounding text for entity |
| **Confidence** | Track how many chunks mention same entity |
| **Debugging** | Trace back to source when entities are wrong |
| **Hybrid Retrieval** | Combine vector (chunk) + graph (entity) search |
| **Trust** | Users can verify entity extractions |

---

### **Chunk Size Recommendations (2024 Research)**

| Chunk Size | Pros | Cons | Best For |
|------------|------|------|----------|
| **300 tokens** | Fast, fits LLM context | Loses context | Short documents |
| **600 tokens** | **Best balance** | Moderate context | **Recommended** |
| **2400 tokens** | Full context | Fewer entities extracted | Long technical docs |

**Microsoft GraphRAG defaults**: 300 tokens + 100 token overlap
**Neo4j recommendation**: 600 tokens
**Your HVDC docs**: **600 tokens + 100 overlap** (technical content)

**Overlap Strategy**:
- Carry forward 100 tokens from previous chunk
- Captures cross-chunk relationships
- Maintains coreferences (e.g., "it", "this system")

---

### **Multi-Pass Extraction (Microsoft Finding)**

**Problem**: LLM doesn't extract all entities in one pass

**Solution**: Multiple extraction passes (2-3 iterations)

```python
for pass_num in range(1, 3):  # 2-3 passes
    new_entities = llm.extract_entities(chunk, existing_entities)
    entities.extend(new_entities)
```

**Cost Optimization**: Use cheaper model (Mistral 7B locally) for multiple passes

---

## 🏷️ Part 3: Metadata & Provenance Tracking

### **What is Provenance?**

Metadata detailing:
- **Origin**: Which document/chunk?
- **Timestamp**: When extracted?
- **Confidence**: How certain?
- **Method**: Which model extracted it?
- **Version**: Which extraction run?

---

### **Graph Fact Synthesis Approach**

**Two-Table Design**:

**1. Edges Table** (Relationships with provenance):
```json
{
  "edge_id": "e123",
  "subject": "HVDC",
  "relation": "uses",
  "object": "VSC technology",
  "fact_text": "HVDC systems use VSC technology for efficient conversion",
  "source_id": "doc_025_chunk_12",
  "confidence": 0.92,
  "extracted_by": "relik-large",
  "timestamp": "2025-11-11T10:23:45Z"
}
```

**2. Sources Table** (Document metadata):
```json
{
  "source_id": "doc_025_chunk_12",
  "document": "GC25_086_HVDC_VSC_Balwin3_Tennet",
  "chunk_index": 12,
  "chunk_text": "...",
  "page": 45,
  "section": "Protection Systems",
  "source_url": "/data/projects/GC25_086.pdf",
  "source_type": "technical_specification",
  "metadata": {
    "project": "GC25_086",
    "technology": "VSC",
    "client": "TenneT",
    "country": "Netherlands"
  }
}
```

---

### **Enhanced Neo4j Schema with Provenance**

```cypher
// Document node
CREATE (d:Document {
  name: 'GC25_086_HVDC_VSC_Balwin3_Tennet',
  source: '/data/projects/GC25_086.pdf',
  doc_type: 'technical_specification',
  project: 'GC25_086',
  date: date('2024-06-15'),
  total_chunks: 156
})

// Chunk nodes
CREATE (c:Chunk {
  chunk_id: 'doc_025_chunk_12',
  text: '...',
  chunk_index: 12,
  page: 45,
  section: 'Protection Systems',
  token_count: 534,
  embedding: [0.23, -0.45, ...]  // Vector for hybrid search
})

// Entity with provenance
CREATE (e:Entity {
  name: 'VSC technology',
  description: 'Voltage Source Converter technology for HVDC',
  entity_type: 'Technology',
  mentions: 47,
  first_seen: timestamp(),
  confidence: 0.92
})

// Relationships with provenance
CREATE (d)-[:HAS_CHUNK {order: 12}]->(c)
CREATE (c)-[:MENTIONS {
  start_pos: 234,
  end_pos: 247,
  confidence: 0.92,
  extracted_by: 'relik-large',
  extraction_timestamp: timestamp()
}]->(e)

// Entity relationships with provenance
CREATE (e1:Entity {name: 'HVDC'})-[:RELATED {
  type: 'uses',
  confidence: 0.89,
  source_chunks: ['doc_025_chunk_12', 'doc_032_chunk_8'],
  co_occurrence_count: 15
}]->(e2:Entity {name: 'VSC technology'})
```

---

### **Provenance Benefits**

| Benefit | Use Case |
|---------|----------|
| **Trust** | "Show me where this came from" |
| **Debugging** | Find why entity extraction failed |
| **Versioning** | Track changes across extraction runs |
| **Confidence** | Weight entities by extraction confidence |
| **Audit Trail** | Compliance & regulatory requirements |
| **Hybrid Search** | Combine chunk vectors + entity graph |

---

## 🎯 Part 4: RECOMMENDED APPROACH

### **Best Practice Architecture (2024)**

```
┌─────────────────────────────────────────────────────────┐
│  HIERARCHICAL KNOWLEDGE GRAPH WITH PROVENANCE          │
└─────────────────────────────────────────────────────────┘

LEVEL 1: DOCUMENTS
  └─ Document nodes (metadata: project, client, date)

LEVEL 2: CHUNKS (600 tokens + 100 overlap)
  └─ Chunk nodes (text, embedding, page, section)
  └─ Relationship: Document -[HAS_CHUNK]-> Chunk

LEVEL 3: ENTITIES (ReLiK extraction)
  └─ Entity nodes (name, type, description, confidence)
  └─ Relationship: Chunk -[MENTIONS {pos, confidence}]-> Entity

LEVEL 4: RELATIONSHIPS (with provenance)
  └─ Entity -[RELATED {type, sources, confidence}]-> Entity

LEVEL 5: COMMUNITIES (Leiden algorithm)
  └─ Community nodes (level, summary)
  └─ Entity -[IN_COMMUNITY]-> Community
  └─ Community -[PARENT_COMMUNITY]-> Community
```

---

### **Implementation Roadmap**

#### **Phase 1: Switch to ReLiK (1-2 days)**
- Install ReLiK: `pip install relik`
- Replace REBEL extraction with ReLiK
- Test on sample documents
- **Expected**: 40x faster, cleaner entities

#### **Phase 2: Add Chunk-Level Structure (2-3 days)**
- Chunk documents (600 tokens + 100 overlap)
- Create Document and Chunk nodes in Neo4j
- Link: Document → Chunk → Entity
- Add chunk embeddings for vector search

#### **Phase 3: Add Provenance Metadata (1-2 days)**
- Add source tracking to relationships
- Record extraction metadata (confidence, timestamp, model)
- Create Sources table/nodes
- Link entities to source chunks

#### **Phase 4: Multi-Pass Extraction (1 day)**
- Implement 2-pass entity extraction
- Merge duplicate entities
- Increase entity coverage

#### **Phase 5: Community Detection (Optional, 1 day)**
- Apply Leiden algorithm for hierarchical clustering
- Create Community nodes
- Generate community summaries with LLM

**Total Effort**: ~5-8 days for complete upgrade

---

## 📊 Part 5: Comparison Matrix

### **Current vs Recommended System**

| Feature | Current (REBEL + Project-level) | Recommended (ReLiK + Chunk-level) |
|---------|--------------------------------|-----------------------------------|
| **Extraction Model** | REBEL (2021) | **ReLiK (2024)** |
| **Speed** | Slow (autoregressive) | **40x faster** |
| **Entity Quality** | Noisy (XML tags) | **Clean, linked to KB** |
| **Granularity** | Project-level | **Chunk-level** |
| **Provenance** | None | **Full tracking** |
| **Metadata** | Limited | **Rich (doc, chunk, confidence)** |
| **Trust** | Low (can't verify) | **High (traceable)** |
| **Hybrid Search** | No | **Yes (vector + graph)** |
| **Community Detection** | No | **Yes (hierarchical)** |
| **Query Accuracy** | 20% (previous tests) | **100% (with Smart Cypher)** |

---

## 💡 Part 6: Specific Recommendations for Your System

### **Your HVDC/SYNCON Context**

**Characteristics**:
- 28 projects
- 10,924 chunks (already chunked!)
- Technical domain (HVDC, VSC, LCC, SynCon)
- Need to answer: "Which projects use X technology?"

### **Recommended Actions**

#### **Immediate (This Week)**:
1. ✅ **Keep Smart Cypher GraphRAG** (already working well!)
2. **Test ReLiK extraction** on 1-2 sample projects
3. **Compare entity quality**: REBEL vs ReLiK

#### **Short-term (Next 2 Weeks)**:
1. **Rebuild graph with chunk-level structure**:
   - Use your existing chunks (10,924)
   - Create Document/Chunk/Entity hierarchy
   - Add provenance metadata

2. **Use ReLiK for extraction**:
   - Cleaner entities (no XML tags)
   - 40x faster processing
   - Entity linking to knowledge bases

3. **Multi-pass extraction**:
   - 2 passes per chunk
   - Capture more entities (especially acronyms)

#### **Long-term (Next Month)**:
1. **Add metadata nodes**:
   - Company nodes (TenneT, Siemens, RTE)
   - Technology nodes (VSC, LCC, HVDC)
   - Country nodes (Germany, Netherlands)
   - Extract from project names

2. **Community detection**:
   - Find entity clusters
   - Generate summaries per community
   - Hierarchical navigation

3. **Hybrid retrieval**:
   - Vector search on chunk embeddings
   - Graph traversal on entities
   - Combine results with Smart Cypher

---

## 🧪 Part 7: Quick Test Plan

### **Test 1: ReLiK vs REBEL Entity Quality**

**Setup**:
- Take 1 sample document (e.g., GC25_086)
- Extract with REBEL (current)
- Extract with ReLiK (new)
- Compare results

**Metrics**:
- Number of entities extracted
- Entity cleanliness (XML tags?)
- Processing time
- F1 score (manual validation)

**Expected**: ReLiK extracts cleaner entities 40x faster

---

### **Test 2: Chunk-Level Provenance**

**Setup**:
- Create chunk-level graph for 1 project
- Query: "Which chunks mention HVDC in GC25_086?"
- Retrieve original text

**Expected**: Can trace entities back to source chunks

---

### **Test 3: Multi-Pass Extraction**

**Setup**:
- Extract entities with 1 pass
- Extract entities with 2 passes
- Compare coverage

**Expected**: 10-20% more entities with 2 passes

---

## 🎓 Part 8: Academic References

1. **ReLiK (ACL 2024)**:
   - Orlando et al., "ReLiK: Retrieve and LinK, Fast and Accurate Entity Linking and Relation Extraction"
   - arXiv:2408.00103
   - HuggingFace: `sapienzanlp/relik-entity-linking-large`

2. **Microsoft GraphRAG (2024)**:
   - Chunk-level extraction with community detection
   - Leiden algorithm for hierarchical clustering
   - Multi-pass gleaning for entity coverage

3. **Neo4j GraphRAG (2024)**:
   - Chunk size recommendations (600 tokens)
   - Document/Chunk/Entity hierarchy
   - Provenance tracking patterns

4. **Graph Fact Synthesis**:
   - Atomic facts with source tracking
   - Edges table + Sources table design
   - Confidence scoring

---

## 📝 Summary & Next Steps

### **Your Questions Answered**:

1. **"Test which will be good: REBEL or ReLiK?"**
   - **Answer**: **ReLiK is better** (40x faster, SOTA accuracy, cleaner entities)

2. **"Do we need chunk-level graph creation?"**
   - **Answer**: **YES** - Industry best practice (Microsoft, Neo4j)
   - Benefits: Provenance, trust, hybrid search, debugging

3. **"Do we need meta info?"**
   - **Answer**: **YES** - Critical for:
     - Tracing entities to sources
     - Confidence scoring
     - Audit trails
     - Company/Country/Technology filtering

4. **"What is the best approach?"**
   - **Answer**: **Hierarchical chunk-level graph with ReLiK + provenance**

---

### **Recommended Implementation**:

```
Phase 1: Test ReLiK (1 day)
    ↓
Phase 2: Build chunk-level graph (2-3 days)
    ↓
Phase 3: Add provenance metadata (1-2 days)
    ↓
Phase 4: Multi-pass extraction (1 day)
    ↓
Phase 5: Community detection (optional, 1 day)
```

**Total**: 5-8 days for complete upgrade

**ROI**:
- 40x faster extraction
- Cleaner entities (no XML tags)
- Provenance tracking (trust)
- Better query accuracy
- Hierarchical navigation

---

**Next Step**: Would you like me to implement a ReLiK test extraction on one of your projects to compare with REBEL?
