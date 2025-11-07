# Knowledge Graph Concepts - Quick Reference

## Document Analysis Summary

This guide synthesizes key concepts from:
1. **Neo4j GraphRAG Documentation** - Technical implementation
2. **"How to Build a Knowledge Graph" (Academic)** - Theoretical framework

---

## Core Concepts Explained

### 1. What is a Knowledge Graph?

**Simple Definition:**
A Knowledge Graph is a structured representation of information where:
- **Nodes** = Entities (things like Person, Document, Organization)
- **Edges** = Relationships (connections like "works_for", "mentions")
- **Properties** = Attributes (data like name, date, description)

**Visual Example:**
```
(Person: "John Smith")
         |
         | [WORKS_FOR]
         ▼
(Organization: "Acme Corp")
         |
         | [LOCATED_IN]
         ▼
(Location: "New York")
```

### 2. Why Use Knowledge Graphs with Vector Search?

| Feature | Vector Search (ChromaDB) | Knowledge Graph (Neo4j) | Combined (Best) |
|---------|-------------------------|------------------------|-----------------|
| **Query Type** | "Find similar documents" | "Find all employees of X" | "Find similar documents about employees of X" |
| **Strength** | Semantic similarity | Structured relationships | Both |
| **Example** | "machine learning papers" | "Papers → Authors → Institutions" | Similarity + Connections |
| **Limitations** | No relationships | No fuzzy matching | None |

**Real-World Example:**
- **Vector Search**: "Find documents about AI" → Returns anything semantically similar
- **Graph Query**: "Find documents written by authors who work at Stanford" → Precise
- **Hybrid**: "Find AI documents written by Stanford authors" → Powerful!

---

## Knowledge Graph Pipeline (4-Stage Process)

### Stage 1: Knowledge Creation
**What:** Extract and structure information from raw data

**Key Components:**
```
PDF Document
    ↓
Text Extraction (Your existing PDFExtractor)
    ↓
Entity Recognition (LLM-based)
    ↓
Relationship Extraction (LLM-based)
    ↓
Structured Data (Nodes + Relationships)
```

**Tools for Your Project:**
- ✅ **Already have**: PDF text extraction (`app/services/contents_extraction/`)
- 🔧 **Need to add**: `LLMEntityRelationExtractor` from neo4j-graphrag
- 🔧 **Need to configure**: LLM prompts for domain-specific entities

### Stage 2: Knowledge Hosting
**What:** Store the structured data in a graph database

**Your Implementation:**
```
Neo4j Database
  ├── Nodes (Entities)
  │   ├── Document nodes
  │   ├── Chunk nodes (linked to ChromaDB)
  │   ├── Person nodes
  │   ├── Organization nodes
  │   └── Concept nodes
  │
  └── Relationships
      ├── CONTAINS_CHUNK
      ├── MENTIONS
      ├── WORKS_FOR
      └── RELATED_TO
```

**Storage Strategy:**
- **Neo4j**: Stores entities and their relationships
- **ChromaDB**: Stores text chunks and embeddings (unchanged)
- **Link**: Each chunk node has an `embedding_id` property pointing to ChromaDB

### Stage 3: Knowledge Curation
**What:** Improve quality through cleaning and enrichment

**Three Sub-Processes:**

#### 3.1 Knowledge Assessment
- **Validate**: Does annotation match the source content?
- **Verify**: Does it conform to schema rules?
- **Your Tool**: `semantify.it` evaluator pattern (build similar validator)

#### 3.2 Knowledge Cleaning
- **Entity Resolution**: Merge duplicate entities
  ```
  Before:
  (Person: "J. Smith") ──┐
  (Person: "John Smith") ┼─→ After: (Person: "John Smith")
  (Person: "Smith, John")─┘
  ```

- **Error Correction**: Fix extraction mistakes
- **Your Tool**: Use `SinglePropertyExactMatchResolver` or `FuzzyMatchResolver`

#### 3.3 Knowledge Enrichment
- **Completion**: Fill missing properties
- **Linking**: Connect entities across documents
- **Your Tool**: Custom enrichment scripts + APOC procedures

### Stage 4: Knowledge Deployment
**What:** Make the graph accessible and usable

**FAIR Principles:**
- **F**indable: Create indexes and search endpoints
- **A**ccessible: Provide REST APIs (your FastAPI routes)
- **I**nteroperable: Use standard formats (Cypher, GraphQL)
- **R**eusable: Document schema and query patterns

---

## Schema Design Patterns

### Pattern 1: Lexical Graph (Document Structure)

**Purpose:** Preserve document hierarchy

```
(Document)
    |
    ├─[CONTAINS_CHUNK]→ (Chunk #1)
    |                        |
    ├─[CONTAINS_CHUNK]→ (Chunk #2) ──[NEXT_CHUNK]→ (Chunk #3)
    |                        |
    └─[CONTAINS_CHUNK]→ (Chunk #3)
                             |
                      [MENTIONS]
                             ↓
                        (Entities...)
```

**Why Important:**
- Maintains document context
- Enables "show me the next paragraph" queries
- Links back to original source

### Pattern 2: Entity Graph (Semantic Layer)

**Purpose:** Represent real-world relationships

```
(Person: "Marie Curie")
         |
         ├─[WORKS_FOR]→ (Org: "University of Paris")
         |
         ├─[DISCOVERED]→ (Concept: "Radium")
         |
         └─[MENTIONED_IN]→ (Chunk) ──[PART_OF]→ (Document: "physics_paper.pdf")
```

**Why Important:**
- Answers "who," "what," "where" questions
- Connects information across documents
- Enables complex traversals

### Pattern 3: Hybrid Graph (Vector + Graph)

**Purpose:** Best of both worlds

```
ChromaDB Embedding                     Neo4j Graph
      │                                      │
      ▼                                      ▼
[Vector: 0.23, 0.45, ...]  ←─[embedding_id]─→ (Chunk {chunk_id: "abc123"})
                                                      |
                                                [MENTIONS]
                                                      ↓
                                                 (Entities...)
```

**Query Flow:**
1. **Vector search** finds semantically similar chunks
2. **Graph traversal** enriches with relationships
3. **Combined results** show similarity + context

---

## Schema Definition Explained

### Node Types (Entities)

**Format:**
```python
{
    "label": "NodeType",           # Required: Node label
    "description": "What it is",   # Optional: Helps LLM understand
    "properties": [                # Optional: Expected attributes
        {
            "name": "property_name",
            "type": "STRING|INTEGER|DATE|BOOLEAN",
            "required": True|False
        }
    ]
}
```

**Example:**
```python
{
    "label": "Person",
    "description": "An individual mentioned in documents",
    "properties": [
        {"name": "name", "type": "STRING", "required": True},
        {"name": "role", "type": "STRING", "required": False},
        {"name": "email", "type": "STRING", "required": False}
    ]
}
```

### Relationship Types

**Format:**
```python
{
    "label": "RELATIONSHIP_NAME",
    "description": "What this relationship means",
    "properties": [...]  # Optional: Relationship attributes
}
```

**Example:**
```python
{
    "label": "WORKS_FOR",
    "description": "Employment relationship",
    "properties": [
        {"name": "since", "type": "DATE"},
        {"name": "position", "type": "STRING"}
    ]
}
```

### Patterns (Valid Connections)

**Format:**
```python
("SourceNode", "RELATIONSHIP", "TargetNode")
```

**Examples:**
```python
PATTERNS = [
    ("Person", "WORKS_FOR", "Organization"),      # People work for orgs
    ("Person", "AUTHORED", "Document"),           # People write docs
    ("Document", "REFERENCES", "Document"),       # Docs cite other docs
    ("Organization", "LOCATED_IN", "Location"),   # Orgs have locations
]
```

**What Patterns Do:**
- Guide LLM during extraction
- Define valid graph structure
- Enable graph pruning (remove invalid connections)

---

## Entity Extraction Process

### How LLM Extracts Entities

**Input to LLM:**
```
Text: "Marie Curie worked at the University of Paris and discovered radium in 1898."

Schema:
- Person (name, role)
- Organization (name, type)
- Concept (name, description)
- Date (value, context)

Relationships:
- WORKS_FOR
- DISCOVERED
- OCCURRED_ON

Patterns:
- (Person, WORKS_FOR, Organization)
- (Person, DISCOVERED, Concept)
- (Event, OCCURRED_ON, Date)
```

**Output from LLM (JSON):**
```json
{
  "nodes": [
    {"id": "1", "label": "Person", "properties": {"name": "Marie Curie", "role": "scientist"}},
    {"id": "2", "label": "Organization", "properties": {"name": "University of Paris", "type": "university"}},
    {"id": "3", "label": "Concept", "properties": {"name": "Radium", "description": "chemical element"}},
    {"id": "4", "label": "Date", "properties": {"value": "1898", "context": "discovery"}}
  ],
  "relationships": [
    {"type": "WORKS_FOR", "start_node_id": "1", "end_node_id": "2"},
    {"type": "DISCOVERED", "start_node_id": "1", "end_node_id": "3", "properties": {"year": "1898"}},
    {"type": "OCCURRED_ON", "start_node_id": "discovery_event", "end_node_id": "4"}
  ]
}
```

**Neo4j Storage (Cypher):**
```cypher
CREATE (p:Person {name: "Marie Curie", role: "scientist"})
CREATE (o:Organization {name: "University of Paris", type: "university"})
CREATE (c:Concept {name: "Radium", description: "chemical element"})
CREATE (d:Date {value: "1898", context: "discovery"})
CREATE (p)-[:WORKS_FOR]->(o)
CREATE (p)-[:DISCOVERED {year: "1898"}]->(c)
```

### Customizing Extraction

**1. Domain-Specific Prompts:**
```python
custom_prompt = """
You are extracting entities from scientific research papers.
Focus on:
- Researchers and their affiliations
- Methodologies and techniques
- Results and findings
- Citations and references

Text: {text}
Schema: {schema}
"""

extractor = LLMEntityRelationExtractor(llm=llm, prompt=custom_prompt)
```

**2. Few-Shot Learning:**
```python
examples = """
Example 1:
Input: "The study by Johnson et al. used BERT for classification."
Output: {
  "nodes": [
    {"label": "Researcher", "name": "Johnson"},
    {"label": "Method", "name": "BERT"},
    {"label": "Task", "name": "classification"}
  ],
  "relationships": [
    {"type": "USED_METHOD", "from": "Researcher", "to": "Method"},
    {"type": "FOR_TASK", "from": "Method", "to": "Task"}
  ]
}
"""

extractor = LLMEntityRelationExtractor(llm=llm, examples=examples)
```

---

## Error Handling Strategies

### On Error Behaviors

**1. IGNORE (Recommended for production):**
```python
kg_pipeline = SimpleKGPipeline(
    on_error="IGNORE"  # Skip failed chunks, continue processing
)
```
- **Pro**: Robust, won't fail entire document
- **Con**: May lose some information
- **Use when**: Processing large batches

**2. RAISE (Good for development):**
```python
kg_pipeline = SimpleKGPipeline(
    on_error="RAISE"  # Stop on first error
)
```
- **Pro**: Catches issues immediately
- **Con**: One bad chunk fails everything
- **Use when**: Testing, debugging

### Validation vs Verification

**Validation** = Does annotation match the source content?
```
PDF says: "Phone: 555-1234"
Annotation says: "phone": "555-1234" ✓
Annotation says: "phone": "555-9999" ✗ (validation error)
```

**Verification** = Does annotation follow schema rules?
```
Schema says: Person needs "name" property
Annotation: {"label": "Person", "name": "John"} ✓
Annotation: {"label": "Person", "age": 30} ✗ (verification error - missing required "name")
```

**Your Implementation:**
```python
# Verification (built-in with neo4j-graphrag)
kg_pipeline = SimpleKGPipeline(schema={...})  # Auto-verifies against schema

# Validation (you need to build)
class KGValidator:
    def validate_extraction(self, pdf_text: str, extracted_graph: Neo4jGraph):
        # Compare entities in graph with mentions in original text
        for node in extracted_graph.nodes:
            if node.properties.get('name') not in pdf_text:
                self.logger.warning(f"Entity {node} not found in source text")
```

---

## Entity Resolution Deep Dive

### The Problem

**Before Resolution:**
```
Document 1 extracts: (Person: "Dr. John Smith")
Document 2 extracts: (Person: "J. Smith")
Document 3 extracts: (Person: "John Smith, PhD")
```

**These are the same person!** But the graph has 3 separate nodes.

### Resolution Strategies

#### 1. Exact Match (Fast, Simple)
```python
from neo4j_graphrag.experimental.components.resolver import SinglePropertyExactMatchResolver

resolver = SinglePropertyExactMatchResolver(
    driver,
    filter_query="WHERE entity:Person"  # Only resolve Person nodes
)
```

**Logic:**
- Merge nodes with same label AND same `name` property
- Case-sensitive by default
- Fast: O(n log n)

**Result:**
- (Person: "John Smith") ← merges exact matches only
- (Person: "J. Smith") ← separate
- (Person: "john smith") ← separate (different case)

#### 2. Fuzzy Match (Medium Speed, Good Accuracy)
```python
from neo4j_graphrag.experimental.components.resolver import FuzzyMatchResolver

resolver = FuzzyMatchResolver(
    driver,
    threshold=0.85  # 85% similarity required
)
```

**Logic:**
- Uses Levenshtein distance
- Compares string similarity
- Threshold: 0.0 (no match) to 1.0 (exact match)

**Result:**
- "John Smith" ≈ "Jon Smith" (typo) → merge at 0.9 similarity
- "John Smith" ≈ "J. Smith" → might not merge (low similarity)

#### 3. Semantic Match (Slow, Highest Accuracy)
```python
from neo4j_graphrag.experimental.components.resolver import SpaCySemanticMatchResolver

resolver = SpaCySemanticMatchResolver(
    driver,
    similarity_threshold=0.95
)
```

**Logic:**
- Uses spaCy embeddings
- Compares semantic meaning
- Understands context

**Result:**
- "Dr. John Smith" ≈ "John Smith, PhD" → merge (same semantic meaning)
- "John Smith" ≠ "Jane Smith" → don't merge (different people)

### Custom Resolution Logic

```python
# Advanced: Combine multiple strategies
class CustomEntityResolver:
    async def resolve(self, entities: List[Entity]):
        # Step 1: Exact match on email (if exists)
        await self.exact_match_by_property("email")

        # Step 2: Fuzzy match on name (high threshold)
        await self.fuzzy_match_by_property("name", threshold=0.95)

        # Step 3: Manual review for medium similarity (0.8-0.95)
        ambiguous = await self.find_similar_entities(threshold=0.8)
        for entity_pair in ambiguous:
            decision = await self.human_review(entity_pair)
            if decision == "merge":
                await self.merge_entities(entity_pair)
```

---

## Querying Patterns

### Basic Cypher Queries

**1. Find all entities of a type:**
```cypher
MATCH (p:Person)
RETURN p.name, p.role
LIMIT 10
```

**2. Find relationships:**
```cypher
MATCH (p:Person)-[r:WORKS_FOR]->(o:Organization)
RETURN p.name, type(r), o.name
```

**3. Traverse multiple hops:**
```cypher
// Find collaborators (people who work at same org)
MATCH (p1:Person)-[:WORKS_FOR]->(o:Organization)<-[:WORKS_FOR]-(p2:Person)
WHERE p1 <> p2
RETURN p1.name, p2.name, o.name
```

**4. Find document mentions:**
```cypher
MATCH (d:Document)-[:CONTAINS_CHUNK]->(c:Chunk)-[:MENTIONS]->(e:Entity)
WHERE d.doc_id = "abc123"
RETURN DISTINCT labels(e)[0] as entity_type, count(e) as count
```

### Hybrid Query Pattern (Vector + Graph)

**Python Implementation:**
```python
async def hybrid_search(query: str, entity_filter: str = None):
    # Step 1: Vector search in ChromaDB
    vector_results = chromadb_collection.query(
        query_texts=[query],
        n_results=20  # Get more candidates
    )

    chunk_ids = vector_results['ids'][0]

    # Step 2: Graph filter in Neo4j
    cypher_query = """
    MATCH (c:Chunk)-[:MENTIONS]->(e:Person)
    WHERE c.chunk_id IN $chunk_ids
      AND e.name = $entity_filter
    RETURN c.chunk_id, c.text, e.name
    ORDER BY c.relevance_score DESC
    """

    graph_results = await neo4j_session.run(cypher_query, {
        "chunk_ids": chunk_ids,
        "entity_filter": entity_filter
    })

    # Step 3: Combine and re-rank
    return graph_results
```

**Example Usage:**
```python
# Find documents about "machine learning" mentioning "Google"
results = await hybrid_search(
    query="machine learning algorithms",
    entity_filter="Google"
)
```

---

## Performance Optimization

### 1. Create Indexes

```cypher
-- Before running queries, create these indexes
CREATE INDEX doc_id_idx FOR (d:Document) ON (d.doc_id);
CREATE INDEX chunk_id_idx FOR (c:Chunk) ON (c.chunk_id);
CREATE INDEX person_name_idx FOR (p:Person) ON (p.name);
CREATE INDEX org_name_idx FOR (o:Organization) ON (o.name);

-- Full-text search index
CREATE FULLTEXT INDEX entity_search FOR (n:Person|Organization|Concept) ON EACH [n.name, n.description];
```

**Impact:**
- Without index: O(n) scan of all nodes
- With index: O(log n) lookup
- **10x-100x speedup** on large graphs

### 2. Batch Processing

```python
# BAD: One transaction per node
for node in nodes:
    await session.run("CREATE (n:Node {data: $data})", data=node)

# GOOD: Batch in single transaction
await session.run("""
    UNWIND $batch as node_data
    CREATE (n:Node)
    SET n = node_data
""", batch=nodes)
```

**Impact:**
- Reduces transaction overhead
- **5x-10x speedup** on bulk inserts

### 3. Limit Result Sets

```cypher
-- BAD: Return everything
MATCH (p:Person)-[:WORKS_FOR]->(o:Organization)
RETURN p, o

-- GOOD: Limit and paginate
MATCH (p:Person)-[:WORKS_FOR]->(o:Organization)
RETURN p, o
LIMIT 100
SKIP $offset
```

### 4. Use EXPLAIN and PROFILE

```cypher
-- See query plan
EXPLAIN
MATCH (p:Person {name: "John Smith"})
RETURN p

-- See actual execution stats
PROFILE
MATCH (p:Person {name: "John Smith"})
RETURN p
```

---

## Common Pitfalls and Solutions

### Pitfall 1: Schema Too Broad
**Problem:** Defining every possible entity type
```python
# DON'T DO THIS
NODE_TYPES = [
    "Person", "Organization", "Location", "Date", "Time",
    "Event", "Product", "Service", "Technology", "Method",
    "Result", "Finding", "Hypothesis", "Theory", ...  # 50+ types
]
```

**Solution:** Start small, iterate
```python
# START WITH THIS
NODE_TYPES = [
    "Document",  # Always needed
    "Chunk",     # Always needed
    "Person",    # Core entity
    "Organization",  # Core entity
    "Concept"    # Catch-all for domain terms
]

# Add more types based on actual needs
```

### Pitfall 2: Not Linking to Vector DB
**Problem:** Graph and vector DB disconnected

**Solution:** Always create the link
```python
# When creating chunk node
chunk_node = {
    "chunk_id": str(uuid.uuid4()),
    "text": chunk_text,
    "embedding_id": chromadb_id,  # ← CRITICAL: Link to vector DB
    "page_number": page_num
}
```

### Pitfall 3: Ignoring Entity Resolution
**Problem:** Graph bloated with duplicate entities

**Solution:** Always run entity resolution
```python
kg_pipeline = SimpleKGPipeline(
    perform_entity_resolution=True,  # ← Always enable
    ...
)
```

### Pitfall 4: No Monitoring
**Problem:** Don't know if KG build succeeds/fails

**Solution:** Add comprehensive logging
```python
from app.utils.logging import get_logger

logger = get_logger("KG")

async def build_kg(doc_id: str):
    logger.info(f"Starting KG build for {doc_id}")
    start = time.time()

    try:
        result = await kg_builder.build_from_extraction(...)
        logger.info(f"KG build succeeded in {time.time() - start:.2f}s")
        return result

    except Exception as e:
        logger.error(f"KG build failed: {str(e)}")
        raise
```

---

## Quick Reference Commands

### Docker Commands
```bash
# Start Neo4j
docker compose --profile dev up -d neo4j

# View Neo4j logs
docker logs -f neo4j-kg

# Access Neo4j Browser
open http://localhost:7474
```

### Neo4j Browser Commands
```cypher
-- See schema
CALL db.schema.visualization()

-- Count nodes by type
MATCH (n)
RETURN labels(n)[0] as type, count(*) as count
ORDER BY count DESC

-- Count relationships by type
MATCH ()-[r]->()
RETURN type(r) as relationship, count(*) as count
ORDER BY count DESC

-- Delete everything (CAREFUL!)
MATCH (n)
DETACH DELETE n
```

### Python Quick Start
```python
# Import
from app.services.knowledge_graph.kg_builder import KnowledgeGraphBuilder
from app.services.knowledge_graph.kg_query import KnowledgeGraphQuery

# Build KG
kg_builder = KnowledgeGraphBuilder()
result = await kg_builder.build_from_extraction(extraction_result)

# Query KG
kg_query = KnowledgeGraphQuery()
entities = await kg_query.find_entities(entity_type="Person")
```

---

## Decision Tree: When to Use What

```
Is your data structured?
├─ YES → Do you need relationships?
│         ├─ YES → Use Knowledge Graph (Neo4j)
│         └─ NO → Use Relational DB (PostgreSQL)
│
└─ NO → Is it text-based?
          ├─ YES → Need semantic search?
          │        ├─ YES → Need relationships too?
          │        │        ├─ YES → Use BOTH (Vector + Graph) ✓
          │        │        └─ NO → Use Vector DB (ChromaDB)
          │        └─ NO → Use Full-text Search (Elasticsearch)
          │
          └─ NO → Use NoSQL (MongoDB)
```

**For Your Project:**
✓ **Use Both**: You have unstructured text (PDFs) AND need relationships (entities across documents)

---

## Next Steps Checklist

- [ ] Read full implementation guide
- [ ] Set up Neo4j locally (docker compose)
- [ ] Test with 1 sample PDF
- [ ] Define schema for your domain
- [ ] Integrate with existing PDF pipeline
- [ ] Create custom query endpoints
- [ ] Monitor and optimize
- [ ] Scale to full corpus

---

**Questions?** Reference the full implementation guide or Neo4j documentation.
