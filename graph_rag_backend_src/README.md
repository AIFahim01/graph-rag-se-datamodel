# HVDC/SynCon Knowledge Graph with ReLiK Extraction

Advanced knowledge graph system for HVDC (High Voltage Direct Current) and Synchronous Condenser electrical grid documentation using state-of-the-art ReLiK entity extraction.

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![PyTorch](https://img.shields.io/badge/PyTorch-2.3+-red.svg)
![CUDA](https://img.shields.io/badge/CUDA-12.1+-green.svg)
![ReLiK](https://img.shields.io/badge/ReLiK-GPU_Optimized-orange.svg)

## Overview

Extract structured knowledge from HVDC and SynCon technical documentation using GPU-accelerated ReLiK extraction:
- **ReLiK Entity Extraction**: Clean, artifact-free entity and relationship extraction
- **Chunk-Level Provenance**: Track every fact back to source chunks and projects
- **GPU-Optimized Processing**: 2.67 chunks/sec on NVIDIA RTX 4500 Ada
- **Neo4j Knowledge Graph**: 10,924+ document chunks with full metadata
- **Smart Cypher GraphRAG**: 100% query success rate with Ollama integration

## Key Features

- ✅ **3x Better Extraction**: ReLiK extracts 367 relations vs REBEL's 125 per 100 chunks
- ✅ **0% Noise**: Zero XML artifacts vs REBEL's 100% noisy output
- ✅ **GPU-Accelerated**: Full CUDA support with automatic optimization
- ✅ **Chunk-Level Tracking**: Complete provenance from chunk to entity
- ✅ **Production Scale**: Processes 10,924 chunks in ~68 minutes on GPU

## Architecture

The system processes HVDC/SynCon technical documents through a multi-stage pipeline:

1. **PDF Processing** → Extract and chunk 10,924 documents from GC 2025 projects
2. **ReLiK Extraction** → GPU-accelerated entity and relationship extraction
3. **Neo4j Storage** → Store knowledge graph with chunk-level provenance
4. **Smart Cypher Query** → Ollama-powered natural language to Cypher translation
5. **GraphRAG Retrieval** → Multi-hop graph traversal with vector similarity

See [Architecture Documentation](docs/architecture/) for details.

## Repository Structure

```
graph-rag-se-datamodel/
├── scripts/
│   ├── build/         (9 files)  - Knowledge graph builders (ReLiK, REBEL)
│   ├── chat/          (5 files)  - Chat interfaces (Ollama, Smart Cypher)
│   ├── setup/         (7 files)  - Environment and database setup
│   ├── utils/         (3 files)  - PDF processing, data copying
│   ├── legacy/        (12 files) - Deprecated REBEL-based scripts
│   └── visualization/ (7 files)  - Graph visualization tools
│
├── tests/            (10 files) - All tests with pytest configuration
├── docs/
│   ├── setup/        - Installation and setup guides
│   ├── performance/  - Benchmark results and comparisons
│   ├── reference/    - Query examples and summaries
│   └── architecture/ - System design documentation
│
├── src/              - Core library code
├── data/             - Processed data and knowledge graphs
└── dataset_samples/  - Sample PDFs from HVDC/SynCon projects
```

## Quick Start

### 1. Environment Setup

```bash
# Clone repository
git clone https://github.com/InfinitiBit/graph-rag-se-datamodel.git
cd graph-rag-se-datamodel

# Create conda environment
conda env create -f environment_vectordb.yml
conda activate hdvc_syncon_vectordb

# Install ReLiK
pip install relik

# Setup services
bash scripts/setup/setup_ollama.sh
bash scripts/setup/setup_neo4j.sh
```

### 2. Build Knowledge Graph with ReLiK

```bash
# Test on 100 chunks first (verify GPU is working)
python scripts/build/build_chunk_level_relik_kg.py --test --sample-size 100

# Process all 10,924 chunks (~68 minutes on GPU)
python scripts/build/build_chunk_level_relik_kg.py

# Load to Neo4j with provenance
python scripts/build/build_chunk_level_relik_kg.py --load-neo4j
```

### 3. Query with Smart Cypher GraphRAG

```bash
# Start interactive chat (100% query success rate)
python scripts/chat/ollama_smart_cypher_graphrag.py

# Example queries:
# - "What HVDC projects involve TenneT?"
# - "Show all converter stations in Germany"
# - "What are the voltage specifications for GC25_002?"
```

See [Quick Start Guide](docs/setup/QUICKSTART.md) for detailed instructions.

## Documentation

### Setup Guides
- **[Ollama Setup](docs/setup/OLLAMA_SETUP.md)**: Configure Ollama for local LLM queries
- **[Vector DB Instructions](docs/setup/RUN_VECTORDB_INSTRUCTIONS.md)**: ChromaDB and vector storage setup

### Performance & Results
- **[ReLiK vs REBEL Comparison](docs/performance/GRAPH_COMPARISON_RECOMMENDATIONS.md)**: Detailed model comparison
- **[Test Results](docs/performance/test_results_relik_vs_rebel.json)**: Benchmark data (367 vs 125 relations)
- **[Smart Cypher Results](docs/performance/SMART_CYPHER_RESULTS.md)**: Query performance metrics
- **[Performance Guide](docs/performance/GRAPHRAG_PERFORMANCE_GUIDE.md)**: Optimization tips

### Reference
- **[Neo4j Queries](docs/reference/neo4j_queries.md)**: Example Cypher queries for HVDC data
- **[Dataset Summary](docs/reference/HDVC_SYNCON_SUBSET_SUMMARY.md)**: GC 2025 projects overview
- **[Implementation Status](docs/reference/IMPLEMENTATION_STATUS.md)**: Current development status

## Available Scripts

### Build Scripts (`scripts/build/`)
- `build_chunk_level_relik_kg.py` - **Recommended**: GPU-optimized chunk-level extraction
- `build_relik_kg.py` - Standard ReLiK extraction
- `build_complete_graphrag.py` - Complete pipeline (vector DB + KG)
- `build_rebel_kg.py` - REBEL extraction (legacy comparison)
- `load_kg_to_neo4j.py` - Load knowledge graph to Neo4j

### Chat Scripts (`scripts/chat/`)
- `ollama_smart_cypher_graphrag.py` - **Recommended**: Smart Cypher with 100% success rate
- `chat_hdvc_syncon.py` - Basic GraphRAG chat interface
- `true_graphrag_chat.py` - Advanced GraphRAG queries

### Test Scripts (`tests/`)
Run all tests: `pytest tests/`
- `test_relik_vs_rebel.py` - Compare extraction models
- `test_relik_relation.py` - Verify ReLiK functionality
- `test_neo4j_connection.py` - Test database connectivity

## ReLiK vs REBEL Comparison

| Metric | REBEL | ReLiK | Winner |
|--------|-------|-------|--------|
| Relations/100 chunks | 125 | 367 | **ReLiK (3x)** |
| Clean extraction | 0% | 100% | **ReLiK** |
| XML artifacts | 100% | 0% | **ReLiK** |
| Processing speed | Fast | 2.67 chunks/sec | REBEL |
| **Recommendation** | ❌ Deprecated | ✅ **Production Use** | **ReLiK** |

See [comparison details](docs/performance/GRAPH_COMPARISON_RECOMMENDATIONS.md) for full analysis.

## Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| **Entity Extraction** | **ReLiK** | relik-ie/relik-relation-extraction-small |
| GPU Acceleration | CUDA | 12.1+ |
| PDF Processing | PyMuPDF | Latest |
| Local LLM | Ollama (Llama 3.1 70B) | Latest |
| Graph Database | Neo4j | 5.x |
| Vector Database | ChromaDB | Latest |
| Python | 3.10 | 3.10+ |
| PyTorch | 2.3 | 2.0+ |

## Requirements

### Hardware (Tested Configuration)
- **GPU**: NVIDIA RTX 4500 Ada (25.76 GB) or equivalent
- **RAM**: 32GB+ recommended
- **Storage**: 500GB+ for full dataset

### Software Dependencies
```bash
Python 3.10+
PyTorch 2.3.1 with CUDA 12.1+
relik (pip install relik)
transformers 4.41.2
neo4j 5.15
chromadb
ollama (for Smart Cypher queries)
```

See `environment_vectordb.yml` for complete environment specification.

## Performance Metrics

### ReLiK Extraction Performance
- **Processing Speed**: 2.67 chunks/sec on NVIDIA RTX 4500 Ada
- **Extraction Quality**: 5.7 relations per chunk average
- **Relation Types**: 45+ unique relationship types
- **Top Relations**: country, headquarters location, manufacturer, diplomatic relation

### Dataset Statistics
- **Total Chunks**: 10,924 from GC 2025 HVDC/SynCon projects
- **Expected Output**: ~62,000 relationships with full provenance
- **Processing Time**: ~68 minutes for complete dataset on GPU
- **Storage**: ~15-20MB for chunk-level knowledge graph JSON

## Project Structure Highlights

### Active Development
- **scripts/build/** - Production ReLiK extraction pipeline
- **scripts/chat/** - Smart Cypher GraphRAG interface
- **tests/** - Comprehensive test suite

### Legacy (Preserved for Reference)
- **scripts/legacy/** - Original REBEL-based implementations
- Kept for comparison and fallback purposes

## Contributing

Contributions welcome! This is an R&D project for HVDC/SynCon knowledge extraction.

Please:
1. Fork the repository
2. Create a feature branch (e.g., `feature/improved-extraction`)
3. Test thoroughly with sample data
4. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## Research Foundation

This project builds on state-of-the-art entity extraction research:

- **ReLiK** (SapienzaNLP, 2024): Retrieval-based entity linking and relation extraction
  - Model: relik-ie/relik-relation-extraction-small
  - Zero XML artifacts, clean extraction
  - Paper: https://arxiv.org/abs/2408.00103

- **REBEL** (Babelscape, 2021): Relation extraction baseline
  - Used for comparison purposes
  - Replaced due to noisy output (100% XML artifacts)

- **GraphRAG** (Microsoft Research, 2024): Graph-based retrieval architecture
  - Smart Cypher integration for natural language queries
  - GitHub: https://github.com/microsoft/graphrag




