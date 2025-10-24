# GraphRAG: Graph-Based Retrieval

## What is GraphRAG?

**GraphRAG** = Graph-based Retrieval-Augmented Generation

Combines:
- Vector embeddings (semantic similarity)
- Knowledge graphs (explicit relationships)
- Multi-level search (global + local)
- LLM generation (answer synthesis)

## Why GraphRAG?

### Standard RAG Limitations

```
Query → Vector Search → Top K chunks → LLM → Answer

Problems:
- Only finds directly similar chunks
- Misses implicit connections
- No relationship understanding
```

### GraphRAG Advantages

```
Query → Multi-Level Search:
        ├─ Global (communities)
        ├─ Entity (concepts)
        ├─ Local (chunks)
        └─ Graph (relationships)
     → Comprehensive results → Better answers
```

## Multi-Level Retrieval

### Level 1: Global Search
- Search community summaries
- Provides high-level context
- Good for broad queries

### Level 2: Entity Search
- Search entity embeddings
- Identifies key concepts
- Discovers related entities

### Level 3: Local Search
- Search chunk embeddings
- Retrieves detailed content
- Provides specific information

### Level 4: Graph Traversal
- Multi-hop reasoning through relationships
- Discovers implicit connections
- Builds complete dependency chains

## Multi-Hop Example

```
Query: "What safety equipment is needed for 690V?"

Direct vector search:
└─ Finds: Chunks mentioning "690V" + "safety"

GraphRAG adds:
├─ Find: "690V" entity
├─ Traverse: 690V → REQUIRES → Circuit Breaker
├─ Continue: Circuit Breaker → COMPLIES_WITH → IEC 61508
├─ Continue: IEC 61508 → SPECIFIES → SIL2
└─ Result: Complete safety requirements across multiple docs!
```

## Community Detection

### Purpose
Automatically organize entities into topic clusters

### Algorithm
Leiden (hierarchical clustering):
- Finds densely connected subgraphs
- Optimizes modularity
- Creates hierarchical levels

### Example Hierarchy
```
Level 3: "Industrial Systems"
  └─ Level 2: "Electrical Power"
      └─ Level 1: "Voltage Specifications"
          └─ Level 0: [690V, 400V, AC, DC]
```

## Result Fusion

Combines all levels with weighted scoring:

```
Score = 0.4 × chunk_similarity +
        0.3 × entity_match +
        0.2 × community_relevance +
        0.1 × graph_proximity
```

## Research Foundation

### Microsoft GraphRAG (2024)

**GitHub**: https://github.com/microsoft/graphrag

**Website**: https://microsoft.github.io/graphrag/

**Key Contributions**:
- Multi-level retrieval architecture
- Community-based summarization
- Hierarchical knowledge organization

**Performance**: 15-30% improvement over standard RAG

## Implementation

See `src/retrieval/graphrag_retriever.py` for complete implementation.

## Further Reading

- [Microsoft GraphRAG Blog](https://www.microsoft.com/en-us/research/blog/graphrag-new-tool-for-complex-data-discovery-now-on-github/)
- [GraphRAG-Local-Ollama](https://github.com/TheAiSingularity/graphrag-local-ollama)
- [Neo4j Vector Search](https://neo4j.com/docs/cypher-manual/current/indexes-for-vector-search/)
