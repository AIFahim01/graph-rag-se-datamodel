# Dataset Samples

This folder contains sample data structures from the GC 2025 projects used for testing the ReLiK knowledge graph extraction.

## Sample Projects Included

1. **GC25_002_HVDC_SE_RnD_POD** - HVDC System Engineering R&D POD documents
2. **GC25_016_SynCon_SEC_Group_1** - Synchronous Condenser SEC Group 1 documentation

## Full Dataset

The complete dataset includes:
- 10,924 document chunks from multiple HVDC and SynCon projects
- Processed JSON files with extracted entities and relationships
- Knowledge graph data in Neo4j-compatible format

## Processed Data Available

- `data/graphrag_complete/graphrag_chunks.json` - All document chunks (10,924 total)
- `data/graphrag_complete/relik_knowledge_graph_test.json` - Test extraction results (100 chunks)
- `data/graphrag_complete/rebel_knowledge_graph.json` - REBEL extraction results for comparison

## Usage

To process the full dataset with ReLiK:
```bash
python build_relik_kg.py
```

To run a test on 100 chunks:
```bash
python build_relik_kg.py --test --sample-size 100
```