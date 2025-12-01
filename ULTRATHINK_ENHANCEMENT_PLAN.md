# ULTRATHINK Enhancement Plan: Graph Construction with RELIK + 4-Judge System

## Executive Summary

Enhance ULTRATHINK with:
1. **RELIK-based entity/relation extraction** (GPU-accelerated)
2. **Power grid domain ontology** (equipment, organizations, locations)
3. **4-Judge system** (Vector + Metadata + Graph + Super Judge)

---

## Phase 1: RELIK Integration (Week 1-2)

### 1.1 Setup RELIK Environment

```bash
# Install RELIK with GPU support
pip install relik transformers torch
```

### 1.2 Create Entity Extraction Pipeline

**New File: `relik_integration/extractors/relik_entity_extractor.py`**

```python
from relik import Relik

class PowerGridRelikExtractor:
    def __init__(self, device="cuda"):
        self.model = Relik.from_pretrained("relik-ie/relik-relation-extraction-small")
        self.entity_mapper = PowerGridEntityMapper()

    def extract(self, text: str) -> dict:
        result = self.model(text)
        return {
            "entities": [self._map_entity(e) for e in result.entities],
            "relations": [self._map_relation(r) for r in result.relations]
        }
```

### 1.3 Batch Processing for 214K Chunks

- **Batch size**: 500 chunks
- **Checkpointing**: Every 1000 chunks
- **Estimated time**: ~17-20 hours (GPU)

**New File: `relik_integration/scripts/run_full_extraction.py`**

---

## Phase 2: Domain Ontology Schema (Week 2-3)

### 2.1 Neo4j Node Types

```cypher
// Equipment Hierarchy
(:HVDCConverter {id, name, type: VSC|LCC|MMC, rated_power_mw, rated_voltage_kv})
(:SynchronousCondenser {id, name, rated_mvar, inertia_constant_h})
(:Transformer {id, name, rated_power_mva, vector_group})
(:BESS {id, name, energy_capacity_mwh, power_rating_mw})
(:Cable {id, name, type, voltage_kv, length_km})
(:ProtectionSystem {id, name, type})

// Organization
(:Organization {id, name, type: TSO|DSO|IPP|Manufacturer, country})

// Location
(:Country {code, name, grid_frequency_hz})
(:Substation {id, name, type, voltage_levels})

// Project (migrate from PageChunk)
(:Project {id, name, technology_type, year, status})

// Document (new - groups PageChunks)
(:Document {id, file_name, document_type, project_id})
```

### 2.2 Relationship Types

```cypher
// Equipment
(Equipment)-[:CONNECTED_TO]->(Equipment)
(Equipment)-[:PART_OF]->(Equipment)
(ProtectionSystem)-[:PROTECTS]->(Equipment)

// Project
(Project)-[:CONTRACTED_BY]->(Organization)
(Project)-[:LOCATED_IN]->(Country)
(Project)-[:INCLUDES_EQUIPMENT]->(Equipment)

// Document
(PageChunk)-[:BELONGS_TO]->(Document)
(Document)-[:PART_OF_PROJECT]->(Project)
(Document)-[:MENTIONS {count, pages}]->(Entity)

// Technical Parameters
(Document)-[:SPECIFIES]->(TechnicalParameter)
```

### 2.3 Create Schema Script

**New File: `scripts/create_ontology_schema.cypher`**

---

## Phase 3: 4-Judge System Architecture (Week 3-4)

### 3.1 System Flow

```
User Query
    │
    ▼
┌─────────────────────────────────┐
│     Query Classifier (LLM)      │
│  Returns: {vector, metadata,    │
│            graph} confidence    │
└─────────────────────────────────┘
    │
    ├────────────┬────────────┬────────────┐
    ▼            ▼            ▼            │
┌─────────┐ ┌──────────┐ ┌──────────┐     │
│ Path 1  │ │ Path 2   │ │ Path 3   │     │
│ VECTOR  │ │ METADATA │ │ GRAPH    │     │
│ Search  │ │ Cypher   │ │ Traversal│     │
└─────────┘ └──────────┘ └──────────┘     │
    │            │            │            │
    └────────────┴────────────┴────────────┘
                      │
                      ▼
         ┌─────────────────────────┐
         │   Super Judge (LLM)     │
         │   qwen3:14b             │
         │   - Evaluates 3 paths   │
         │   - Fusion strategy     │
         │   - Final answer        │
         └─────────────────────────┘
                      │
                      ▼
              Final Response
```

### 3.2 New Files to Create

1. **`graph_path_executor.py`** - Graph traversal path
   - Extract entities from query using LLM
   - Find entities in Neo4j graph
   - Traverse relationships (1-2 hops)
   - Return related entities + context chunks

2. **`four_judge_system.py`** - Main orchestrator
   - Query classification
   - Parallel path execution
   - Super Judge evaluation
   - Result fusion

3. **API Endpoints** (add to `integrated_api_server.py`):
   - `GET /api/graph-search` - Entity relationship search
   - `GET /api/multi-judge` - Full 4-judge search

### 3.3 Query Routing Logic

| Query Pattern | Primary Path | Example |
|---------------|--------------|---------|
| "How many X in Y" | METADATA | "How many HVDC in 2025?" |
| "Find documents about X" | VECTOR | "Find transformer protection docs" |
| "How does X relate to Y" | GRAPH | "How does HVDC relate to converters?" |
| "Connections between X and Y" | GRAPH | "Connections between protection and BESS" |

### 3.4 Graph Path Cypher Templates

```cypher
-- Find entity relationships
MATCH path = (e1:Entity {name: $entity})-[:RELATION*1..2]-(e2:Entity)
RETURN e1.name, [rel in relationships(path) | rel.type], e2.name

-- Find co-occurring entities
MATCH (c:Chunk)-[:MENTIONS]->(e1:Entity {name: $entity})
MATCH (c)-[:MENTIONS]->(e2:Entity)
WHERE e1 <> e2
RETURN e2.name, count(c) as co_occurrences
ORDER BY co_occurrences DESC

-- Entity context from chunks
MATCH (c:Chunk)-[:MENTIONS]->(e:Entity {name: $entity})
RETURN c.chunk_id, c.project_id, substring(c.text, 0, 500)
LIMIT 5
```

---

## Phase 4: Integration & Testing (Week 5-6)

### 4.1 Update LLM Query Generator

Extend `llm_query_generator.py` with ontology schema:

```python
ONTOLOGY_SCHEMA = """
Node Types:
- Project: id, name, technology_type, year
- HVDCConverter: type (VSC/LCC/MMC), rated_power_mw, rated_voltage_kv
- SynchronousCondenser: rated_mvar, inertia_constant_h
- BESS: energy_capacity_mwh, power_rating_mw
- Organization: type (TSO/DSO/IPP), country
- Entity: name, type, mention_count

Relationships:
- (Project)-[:CONTRACTED_BY]->(Organization)
- (Project)-[:INCLUDES_EQUIPMENT]->(Equipment)
- (Entity)-[:MENTIONED_IN]->(PageChunk)
- (Entity)-[:RELATES_TO {type}]->(Entity)
"""
```

### 4.2 Test Query Suite

```python
TEST_QUERIES = {
    "metadata": ["How many HVDC in 2025?", "List SynCon projects"],
    "vector": ["Find transformer protection docs", "Search harmonic filters"],
    "graph": ["How does HVDC relate to converters?", "Connections between BESS and protection"],
    "hybrid": ["Germany HVDC projects with converter issues"]
}
```

---

## Implementation Files Summary

### New Files to Create

| File | Purpose |
|------|---------|
| `relik_integration/extractors/relik_entity_extractor.py` | RELIK wrapper with domain mapping |
| `relik_integration/extractors/entity_mapper.py` | Map RELIK output to ontology |
| `relik_integration/scripts/run_full_extraction.py` | Batch extraction for 214K chunks |
| `relik_integration/storage/neo4j_kg_writer.py` | Write entities/relations to Neo4j |
| `graph_path_executor.py` | Graph traversal for 4-judge system |
| `four_judge_system.py` | Main 4-judge orchestrator |
| `scripts/create_ontology_schema.cypher` | Neo4j schema creation |
| `src/ontology/extractors/parameter_extractor.py` | Technical parameter extraction |

### Files to Modify

| File | Changes |
|------|---------|
| `integrated_api_server.py` | Add `/api/graph-search`, `/api/multi-judge` endpoints |
| `llm_query_generator.py` | Add ontology schema, graph query generation |
| `create_indexes.py` | Add ontology indexes |

---

## Critical Files to Read Before Implementation

1. `graph_check/services/relik_extractor.py` - Existing RELIK wrapper to extend
2. `graph_check/services/neo4j_loader.py` - KG loading patterns
3. `src/storage/neo4j_store.py` - Graph traversal methods
4. `src/retrieval/hybrid_retriever.py` - Hybrid search patterns
5. `three_llm_judge_system.py` - Current 3-judge architecture

---

## Estimated Timeline

| Week | Milestone |
|------|-----------|
| 1-2 | RELIK setup + batch extraction pipeline |
| 2-3 | Ontology schema creation + migration |
| 3-4 | 4-Judge system implementation |
| 4-5 | Run full extraction (17-20 hours background) |
| 5-6 | Integration testing + optimization |

---

## Success Criteria

- [ ] RELIK extracts entities from all 214K chunks
- [ ] Neo4j has ontology schema with relationships
- [ ] 4-Judge system routes queries correctly
- [ ] Graph path finds entity relationships
- [ ] Response time < 3s for hybrid queries
