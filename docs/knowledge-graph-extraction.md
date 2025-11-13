# Knowledge Graph Extraction with REBEL

This document explains how to extract knowledge graphs from PDF documents using the REBEL model (Relation Extraction By End-to-end Language generation).

## Overview

REBEL is a seq2seq model that extracts relation triplets from text. A triplet consists of:
- **Head**: The subject entity
- **Relation**: The relationship type
- **Tail**: The object entity

Example triplet: `(SAP S/4HANA, is_a, ERP System)`

## Implementation

Based on the article:
**"Building Knowledge Graphs: REBEL, LlamaIndex, and REBEL + LlamaIndex"** by Saurav Joshi

## Usage

### 1. Build Knowledge Graphs

Extract relation triplets from all project PDFs:

```bash
# Process all projects
python scripts/build_knowledge_graph_rebel.py --all

# Process specific project
python scripts/build_knowledge_graph_rebel.py --project alpha_erp_system

# Adjust batch size (lower if OOM errors occur)
python scripts/build_knowledge_graph_rebel.py --all --batch-size 1
```

### 2. Visualize Knowledge Graphs

Create visual representations of the extracted graphs:

```bash
# Visualize all knowledge graphs
python scripts/visualize_knowledge_graph.py --all

# Visualize specific project
python scripts/visualize_knowledge_graph.py --project alpha_erp_system

# Include subgraph visualizations for top entities
python scripts/visualize_knowledge_graph.py --all --subgraphs
```

## Outputs

After processing, you'll find outputs in `datasets/knowledge_graphs/`:

```
datasets/knowledge_graphs/
├── alpha_erp_system_knowledge_graph.json    # Full KG with metadata
├── alpha_erp_system_triplets.json           # Simple triplet list
├── alpha_erp_system_stats.json              # Statistics summary
│
├── alpha_erp_system_visualizations/         # Visualizations
│   ├── alpha_erp_system_full_graph.png      # Complete graph
│   ├── alpha_erp_system_statistics.txt      # Detailed stats
│   └── subgraphs/                           # Entity-centered views
│       ├── subgraph_01_SAP_S4HANA.png
│       └── ...
│
├── beta_cloud_migration_knowledge_graph.json
├── gamma_analytics_platform_knowledge_graph.json
└── ...
```

## Knowledge Graph Structure

### JSON Format

```json
{
  "project_name": "alpha_erp_system",
  "num_pdfs": 4,
  "num_text_segments": 18,
  "num_total_triplets": 243,
  "num_unique_triplets": 187,
  "timestamp": "2025-01-29T10:30:00",
  "triplets": [
    {
      "head": "SAP S/4HANA",
      "relation": "is_a",
      "tail": "ERP System"
    },
    {
      "head": "ABC Corporation",
      "relation": "requires",
      "tail": "inventory management"
    },
    ...
  ]
}
```

### Triplet Types

Common relation types extracted:
- **Identity**: `is_a`, `type_of`
- **Composition**: `part_of`, `contains`, `includes`
- **Properties**: `has_property`, `located_in`
- **Actions**: `requires`, `implements`, `provides`
- **Temporal**: `precedes`, `follows`, `during`
- **Organizational**: `member_of`, `works_for`, `subsidiary_of`

## Model Details

### REBEL Model

- **Model**: `Babelscape/rebel-large`
- **Base**: BART (seq2seq transformer)
- **Training Data**: Wikipedia + Wikidata (200+ relation types)
- **Size**: ~1.5GB
- **Device**: Automatically uses GPU if available, otherwise CPU

### Performance

- **Speed**: ~2-5 seconds per text segment (GPU) / ~10-20 seconds (CPU)
- **Memory**: 4-8GB RAM recommended
- **Accuracy**: High precision on factual relations, may miss implicit connections

## Use Cases

### 1. Entity Recognition

Identify key entities in documents:
- Technologies (SAP, AWS, Kubernetes)
- Organizations (ABC Corporation, XYZ Tech)
- Concepts (ERP, Cloud Migration, Analytics)

### 2. Relationship Discovery

Find connections between entities:
- Technical dependencies
- Organizational structures
- Process flows
- Requirements relationships

### 3. Document Understanding

Gain insights across documents:
- Cross-project technology usage
- Common patterns and approaches
- Reusable components
- Knowledge transfer

### 4. Graph-based Retrieval (GraphRAG)

Use knowledge graphs for enhanced retrieval:
- Multi-hop reasoning
- Entity-based search
- Relationship-aware queries
- Context-enriched responses

## Integration with GraphRAG

The extracted knowledge graphs can be used with:

1. **Vector + Graph Hybrid Search**
   - Combine semantic similarity (vectors) with structural relationships (graph)
   - Better context retrieval for complex queries

2. **LlamaIndex Knowledge Graph Index**
   - Import REBEL triplets into LlamaIndex
   - Query using natural language
   - Automatic graph traversal

3. **Neo4j / NebulaGraph**
   - Load triplets into graph database
   - Run Cypher/nGQL queries
   - Perform graph analytics

## Performance Optimization

### Reduce Memory Usage

```bash
# Use smaller batch size
python scripts/build_knowledge_graph_rebel.py --all --batch-size 1

# Process one project at a time
python scripts/build_knowledge_graph_rebel.py --project alpha_erp_system
```

### Speed Up Processing

```bash
# Use GPU if available (automatic)
# Reduce model size (trade-off with accuracy)
python scripts/build_knowledge_graph_rebel.py --all --model Babelscape/rebel-base
```

## Troubleshooting

### Model Download Issues

If model download fails:
```bash
# Download manually
python -c "from transformers import AutoModel; AutoModel.from_pretrained('Babelscape/rebel-large')"
```

### Out of Memory

Reduce batch size:
```bash
python scripts/build_knowledge_graph_rebel.py --all --batch-size 1
```

### Slow Processing

- Enable GPU if available
- Process projects individually
- Use smaller model variant

## Next Steps

After building knowledge graphs:

1. **Analyze Results**
   - Review extracted triplets
   - Check statistics and visualizations
   - Identify key entities and relationships

2. **Integrate with GraphRAG**
   - Load into graph database
   - Build hybrid vector+graph index
   - Implement graph-based retrieval

3. **Query System**
   - Natural language queries
   - Multi-hop reasoning
   - Cross-document insights

## References

- [REBEL Paper](https://arxiv.org/abs/2104.08821) - Cabot & Navigli, 2021
- [Babelscape/rebel-large](https://huggingface.co/Babelscape/rebel-large) - HuggingFace Model
- [Building Knowledge Graphs Article](https://medium.com/@zilliz_learn/building-knowledge-graphs-rebel-llamaindex-and-rebel-llamaindex-2ab1c6a5dc4b) - Saurav Joshi, 2023
- [LlamaIndex Knowledge Graphs](https://docs.llamaindex.ai/en/stable/examples/index_structs/knowledge_graph/) - Official Docs

## Example Workflow

```bash
# Complete workflow
cd /mnt/c/Users/User/PycharmProjects/pdf-to-graphrag

# 1. Check dataset
python scripts/dataset_stats.py

# 2. Build knowledge graphs
python scripts/build_knowledge_graph_rebel.py --all

# 3. Visualize results
python scripts/visualize_knowledge_graph.py --all --subgraphs

# 4. Review outputs
ls datasets/knowledge_graphs/
cat datasets/knowledge_graphs/alpha_erp_system_statistics.txt
```
