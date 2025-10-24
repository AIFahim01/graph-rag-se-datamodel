# System Architecture

## Overview

The PDF-to-GraphRAG system consists of 8 sequential components organized into 2 phases:

**Phase 1: Setup (One-time)** - Blocks 1-6
**Phase 2: Runtime (Per query)** - Blocks 7-8

## Architecture Diagram

![Architecture](images/architecture-diagram.png)

## Component Flow

```
1. PDF Documents (Input)
   ↓
2. Processing Layer (Extract → Chunk)
   ↓
   ├→ 3. Embedding Training (Contrastive Learning)
   └→ 4. Knowledge Graph (Entity & Relation Extraction)
   ↓
5. Vector Generation (Embed all content)
   ↓
6. Storage (Vector DB + Graph DB)
   ↓
7. GraphRAG Query (Multi-level retrieval)
   ↓
8. Q&A System (Local LLM answer generation)
```

## Block Details

### Block 1: PDF Documents
- Input corpus of PDF files
- Multiple PDFs per project supported
- Text-extractable content required

### Block 2: Processing Layer
- **PDF Extraction**: PyMuPDF page-by-page extraction
- **Chunking**: 1000-char chunks with 200-char overlap
- **Metadata**: Page numbers, source files, positions

### Block 3: Embedding Training
- **Pair Generation**: Structure-based (adjacent, same-section, cross-PDF)
- **Base Model**: bge-large-en-v1.5 (BAAI)
- **Training**: Contrastive learning with MNRL loss
- **Output**: Custom domain-adapted embedding model

### Block 4: Knowledge Graph
- **Entity Extraction**: Local Llama 70B identifies concepts
- **Relationship Extraction**: Triplets (Entity1, Relation, Entity2)
- **Graph Building**: NetworkX or Neo4j
- **Community Detection**: Leiden algorithm
- **Summaries**: LLM-generated community descriptions

### Block 5: Vector Generation
- Embed chunks, entities, communities
- Uses custom model from Block 3
- Batch processing for efficiency

### Block 6: Storage
- **Vector Store**: ChromaDB, Qdrant, or Neo4j
- **Graph Store**: Neo4j or NetworkX
- **Unified Option**: Neo4j 5.x for both

### Block 7: GraphRAG Query
- **Multi-level**: Global + Entity + Local search
- **Graph Traversal**: Multi-hop reasoning
- **Fusion**: Combined scoring from all levels

### Block 8: Q&A System
- Local Llama 3.1 70B (pre-trained)
- Context-based answer generation
- Source citations and related concepts

## Technology Stack

See [README.md](../README.md) for complete technology stack details.

## Data Flow

### Training Phase
```
PDFs → Extract → Chunk → {Train Embeddings + Build Graph} → Generate Vectors → Store
```

### Query Phase
```
User Query → GraphRAG Retrieval → LLM Answer Generation → Response
```

## References

- [Contrastive Learning Details](contrastive-learning.md)
- [GraphRAG Details](graphrag.md)
- [Installation Guide](installation.md)
