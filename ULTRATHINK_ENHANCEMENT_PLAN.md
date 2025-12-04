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

---

## Phase 5: Graph Quality & Validation (Client Requirements) - LLM-Based

### 5.1 Ontology Structure (Triplet Format) - LLM Classification

**Triplet Schema**: `(Subject)-[Predicate]->(Object)`

**LLM-Based Schema Classification**:
```python
class LLMSchemaClassifier:
    def classify_entity(self, entity_text: str, context: str) -> Dict:
        prompt = f"""
        Classify this entity from power grid domain:
        Entity: "{entity_text}"
        Context: "{context}"

        Valid Types: Equipment, HVDCConverter, Transformer, BESS, SynCon,
                     Organization, Location, Country, Project, Document

        Return JSON:
        {{"type": "...", "confidence": 0.0-1.0, "reasoning": "..."}}
        """
        return self.llm.generate(prompt)

    def classify_relation(self, subject: str, predicate: str, object: str) -> Dict:
        prompt = f"""
        Classify this relationship:
        {subject} --[{predicate}]--> {object}

        Valid Relations: CONNECTED_TO, PART_OF, PROTECTS, CONTRACTED_BY,
                        LOCATED_IN, INCLUDES_EQUIPMENT, MANUFACTURED_BY

        Return JSON:
        {{"relation_type": "...", "valid": true/false, "confidence": 0.0-1.0}}
        """
        return self.llm.generate(prompt)
```

---

### 5.2 Dynamic Schema Updates (New Category Handling) - LLM Decision

**LLM-Based Category Handler**:
```python
class LLMDynamicOntologyHandler:
    def handle_new_category(self, entity_type: str, entity_name: str, context: str) -> Dict:
        prompt = f"""
        A new entity type was discovered that doesn't match existing schema.

        New Entity: "{entity_name}"
        Detected Type: "{entity_type}"
        Context: "{context}"

        Existing Schema Types:
        - Equipment (HVDCConverter, Transformer, BESS, SynCon, Cable)
        - Organization (TSO, DSO, IPP, Manufacturer)
        - Location (Country, Substation, Region)
        - Project, Document

        Decide:
        1. MAP_TO_EXISTING: If it's a variation of existing type
        2. CREATE_NEW_TYPE: If it's genuinely new and relevant
        3. IGNORE: If it's noise or irrelevant

        Return JSON:
        {{
            "action": "MAP_TO_EXISTING|CREATE_NEW_TYPE|IGNORE",
            "mapped_type": "existing type name or null",
            "new_type_name": "suggested name if CREATE_NEW_TYPE",
            "reasoning": "...",
            "confidence": 0.0-1.0
        }}
        """
        return self.llm.generate(prompt)
```

---

### 5.3 Duplicate Node Detection & Resolution - LLM Semantic Matching

**LLM-Based Duplicate Detection**:
```python
class LLMDuplicateDetector:
    def find_duplicates(self, entity_list: List[str]) -> List[Dict]:
        prompt = f"""
        Analyze these entities and identify duplicates/synonyms:
        {entity_list[:50]}  # Process in batches

        For power grid domain, identify:
        1. Exact duplicates (same entity, different spelling)
        2. Semantic duplicates (same concept, different names)
        3. Abbreviations vs full names

        Return JSON array:
        [
            {{
                "canonical": "primary name to keep",
                "duplicates": ["variant1", "variant2"],
                "confidence": 0.0-1.0,
                "reasoning": "why these are duplicates"
            }}
        ]
        """
        return self.llm.generate(prompt)

    def should_merge(self, entity1: str, entity2: str, contexts: List[str]) -> Dict:
        prompt = f"""
        Should these two entities be merged?

        Entity 1: "{entity1}"
        Entity 2: "{entity2}"

        Contexts where they appear:
        {contexts[:3]}

        Return JSON:
        {{
            "should_merge": true/false,
            "primary_name": "which name to keep",
            "confidence": 0.0-1.0,
            "reasoning": "..."
        }}
        """
        return self.llm.generate(prompt)
```

---

### 5.4 Invalid Duplicate Relationship Detection - LLM Validation

**LLM-Based Relationship Validator**:
```python
class LLMRelationshipValidator:
    def validate_duplicate_relationships(self, relationships: List[Dict]) -> Dict:
        prompt = f"""
        Analyze these relationships between same entity pairs:
        {relationships}

        For each pair, determine:
        1. Are these genuinely duplicate (same meaning)?
        2. Are they complementary (different aspects)?
        3. Are they conflicting (contradictory)?

        Return JSON:
        {{
            "duplicates_to_merge": [{{...}}],
            "complementary_to_keep": [{{...}}],
            "conflicts_to_resolve": [{{...}}],
            "recommendations": "..."
        }}
        """
        return self.llm.generate(prompt)

    def resolve_conflict(self, rel1: Dict, rel2: Dict, contexts: List[str]) -> Dict:
        prompt = f"""
        These relationships appear to conflict:
        Relation 1: {rel1}
        Relation 2: {rel2}

        Source contexts:
        {contexts}

        Determine which is correct based on context, or if both are valid in different contexts.

        Return JSON:
        {{
            "resolution": "KEEP_REL1|KEEP_REL2|KEEP_BOTH|MERGE",
            "merged_relation": {{...}} if MERGE,
            "confidence": 0.0-1.0,
            "reasoning": "..."
        }}
        """
        return self.llm.generate(prompt)
```

---

### 5.5 Context Verification for Relationships

**Verify relationships are supported by source text**:

```python
class RelationshipVerifier:
    def verify_relationship(self, subject: str, relation: str, object: str, source_chunk: str) -> Dict:
        # Use LLM to verify relationship exists in context
        prompt = f"""
        Source text: "{source_chunk}"

        Verify if this relationship is explicitly or implicitly supported:
        {subject} --[{relation}]--> {object}

        Return JSON:
        {{"supported": true/false, "evidence": "quote from text", "confidence": 0.0-1.0}}
        """

        result = self.llm.generate(prompt)
        return {
            "verified": result["supported"],
            "evidence": result["evidence"],
            "confidence": result["confidence"]
        }
```

---

### 5.6 Cardinality & Constraints

**Constraint Definitions**:
```cypher
// Uniqueness constraints
CREATE CONSTRAINT entity_name_unique IF NOT EXISTS
FOR (e:Entity) REQUIRE e.name IS UNIQUE;

CREATE CONSTRAINT project_id_unique IF NOT EXISTS
FOR (p:Project) REQUIRE p.id IS UNIQUE;

// Property constraints
CREATE CONSTRAINT voltage_positive IF NOT EXISTS
FOR (e:Equipment) REQUIRE e.rated_voltage_kv >= 0;
```

**Cardinality Rules**:
| Relationship | Cardinality | Validation |
|-------------|-------------|------------|
| Project-[:LOCATED_IN]->Country | N:1 | Max 1 country per project |
| Equipment-[:PART_OF]->Equipment | N:1 | No circular references |
| Document-[:MENTIONS]->Entity | N:M | Unlimited |
| Project-[:CONTRACTED_BY]->Org | N:M | Multiple contractors allowed |

---

### 5.7 Confidence Scoring System - LLM Multi-Factor Analysis

**LLM-Based Confidence Scorer**:
```python
class LLMConfidenceScorer:
    def score_extraction(self, entity: str, relation: str, context: str, metadata: Dict) -> Dict:
        prompt = f"""
        Score the confidence of this extracted knowledge:

        Entity/Relation: {entity} / {relation}
        Source Context: "{context}"
        RELIK Model Score: {metadata.get('model_score', 0.5)}
        Co-occurrence Count: {metadata.get('cooccurrence', 1)}

        Evaluate based on:
        1. Is the entity clearly mentioned in context? (0-0.3)
        2. Is the relationship explicitly stated or strongly implied? (0-0.3)
        3. Does it fit power grid domain knowledge? (0-0.2)
        4. Is the extraction unambiguous? (0-0.2)

        Return JSON:
        {{
            "total_score": 0.0-1.0,
            "confidence_level": "HIGH|MEDIUM|LOW",
            "breakdown": {{
                "context_clarity": 0.0-0.3,
                "relationship_evidence": 0.0-0.3,
                "domain_fit": 0.0-0.2,
                "unambiguity": 0.0-0.2
            }},
            "concerns": ["list any issues"],
            "recommendation": "ACCEPT|FLAG|REJECT"
        }}
        """
        return self.llm.generate(prompt)

CONFIDENCE_THRESHOLDS = {
    "HIGH": 0.8,    # Automatically accept
    "MEDIUM": 0.5,  # Accept with flag for review
    "LOW": 0.3      # Manual review required
}
```

---

### 5.8 Anomaly Detection - LLM Analysis

**LLM-Based Anomaly Analyzer**:
```python
class LLMAnomalyDetector:
    def analyze_orphan_node(self, entity: Dict, similar_entities: List[str]) -> Dict:
        prompt = f"""
        This entity has no relationships in the graph:
        Entity: {entity['name']} (type: {entity['label']})
        Mention count: {entity['mention_count']}

        Similar entities that DO have relationships:
        {similar_entities[:10]}

        Determine:
        1. Should this entity be linked to any similar entities?
        2. Is this a valid standalone entity?
        3. Should it be deleted as noise?

        Return JSON:
        {{
            "action": "LINK_TO|KEEP_STANDALONE|DELETE",
            "link_targets": ["entity names to link to"],
            "reasoning": "...",
            "confidence": 0.0-1.0
        }}
        """
        return self.llm.generate(prompt)

    def analyze_weak_cluster(self, cluster_entities: List[str], cluster_relations: List[Dict]) -> Dict:
        prompt = f"""
        This is a small isolated cluster in the knowledge graph:
        Entities: {cluster_entities}
        Relations: {cluster_relations}

        The main graph has entities like: [list of main entities]

        Should this cluster:
        1. Be merged into the main graph? (find connection points)
        2. Remain separate? (valid isolated concept)
        3. Be deleted? (noise or irrelevant)

        Return JSON:
        {{
            "action": "MERGE|KEEP|DELETE",
            "merge_points": ["connections to main graph"],
            "reasoning": "...",
            "confidence": 0.0-1.0
        }}
        """
        return self.llm.generate(prompt)
```

---

### 5.9 Entity Normalization - LLM Semantic Understanding

#### Node-Level Normalization (LLM)

**LLM-Based Entity Normalizer**:
```python
class LLMEntityNormalizer:
    def normalize_entity_name(self, entity_name: str, entity_type: str, context: str) -> Dict:
        prompt = f"""
        Normalize this entity name for a power grid knowledge graph:

        Entity: "{entity_name}"
        Type: {entity_type}
        Context: "{context}"

        Consider:
        1. Is this an abbreviation? (e.g., "XFMR" -> "Transformer")
        2. Is this a variant spelling? (e.g., "Syncon" -> "SynchronousCondenser")
        3. Is this a brand name that should be generalized?
        4. Should organization names be standardized?

        Power Grid Standard Terms:
        - Equipment: Transformer, HVDCConverter, BESS, SynchronousCondenser, Cable
        - Organizations: Keep official names (Siemens, ABB, etc.)
        - Locations: Use ISO country codes + official city names

        Return JSON:
        {{
            "normalized_name": "standardized name",
            "original_name": "{entity_name}",
            "normalization_type": "ABBREVIATION|SPELLING|SYNONYM|UNCHANGED",
            "confidence": 0.0-1.0,
            "reasoning": "..."
        }}
        """
        return self.llm.generate(prompt)

    def find_canonical_form(self, variants: List[str]) -> Dict:
        prompt = f"""
        These entity names may refer to the same concept:
        {variants}

        In power grid domain, determine:
        1. The canonical (standard) form
        2. Which variants map to it
        3. Any that are actually different entities

        Return JSON:
        {{
            "canonical": "standard name",
            "confirmed_variants": ["list of synonyms"],
            "different_entities": ["any that are NOT the same"],
            "confidence": 0.0-1.0
        }}
        """
        return self.llm.generate(prompt)
```

#### Property-Level Normalization (LLM)

**LLM-Based Unit Normalizer**:
```python
class LLMUnitNormalizer:
    def normalize_technical_value(self, value_string: str, property_name: str) -> Dict:
        prompt = f"""
        Parse and normalize this technical value for power grid data:

        Value String: "{value_string}"
        Property: {property_name}

        Standard Units:
        - Voltage: kV (kilovolts)
        - Power: MW (megawatts)
        - Reactive Power: MVAr
        - Energy: MWh
        - Current: kA
        - Frequency: Hz

        Examples:
        - "1.2 GW" -> {{"value": 1200, "unit": "MW"}}
        - "320kV" -> {{"value": 320, "unit": "kV"}}
        - "500 MVA" -> {{"value": 500, "unit": "MVA"}}

        Return JSON:
        {{
            "parsed_value": numeric value,
            "normalized_unit": "standard unit",
            "original_string": "{value_string}",
            "conversion_applied": "description of conversion",
            "confidence": 0.0-1.0
        }}
        """
        return self.llm.generate(prompt)
```

---

## Implementation Files for Graph Quality (LLM-Based)

| File | Purpose |
|------|---------|
| `graph_quality/llm_schema_classifier.py` | LLM-based entity/relation type classification |
| `graph_quality/llm_duplicate_detector.py` | LLM semantic duplicate detection |
| `graph_quality/llm_relationship_validator.py` | LLM context verification for relationships |
| `graph_quality/llm_confidence_scorer.py` | LLM multi-factor confidence scoring |
| `graph_quality/llm_anomaly_detector.py` | LLM analysis of orphans and weak clusters |
| `graph_quality/llm_entity_normalizer.py` | LLM semantic entity normalization |
| `graph_quality/llm_unit_normalizer.py` | LLM technical value parsing |
| `graph_quality/llm_base.py` | Base LLM client (Ollama qwen3:14b) |
| `scripts/run_llm_graph_quality.py` | Run all LLM-based quality checks |

### LLM Model Configuration
```python
LLM_CONFIG = {
    "model": "qwen3:14b",           # Primary model for quality checks
    "fallback_model": "qwen3:8b",    # Fallback for high volume
    "temperature": 0.1,              # Low temp for consistent results
    "timeout": 30,                   # Seconds per request
    "batch_size": 50,                # Entities per batch
    "ollama_url": "http://localhost:11434"
}
```

---

## Success Criteria

- [ ] RELIK extracts entities from all 214K chunks
- [ ] Neo4j has ontology schema with relationships
- [ ] 4-Judge system routes queries correctly
- [ ] Graph path finds entity relationships
- [ ] Response time < 3s for hybrid queries
- [ ] Duplicate nodes < 1% after normalization
- [ ] Confidence scoring: >80% HIGH confidence
- [ ] Orphan nodes < 5% of total entities
- [ ] All relationships context-verified
- [ ] Unit normalization 100% consistent
