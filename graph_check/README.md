# Graph RAG System - End-to-End Pipeline

Complete pipeline for building and querying a knowledge graph from markdown files using ReLiK extraction and LLM-based querying.

## Architecture

```
Markdown Files (.md)
       ↓
[1] Chunking
       ↓
Text Chunks
       ↓
[2] ReLiK Extraction → Entities + Relations
       ↓
Knowledge Graph (JSON)
       ↓
[3] Load to Neo4j
       ↓
Neo4j Knowledge Graph
       ↓
[4] User Query (Natural Language)
       ↓
LLM (Llama) → Generate Cypher Query
       ↓
Execute Cypher in Neo4j
       ↓
Graph Results
       ↓
LLM → Generate Plain Text Answer
       ↓
Final Answer to User
```

## Setup

### 1. Start Neo4j
```bash
docker start neo4j-vector-test
# Or create new container:
docker run -d \
  --name neo4j-vector-test \
  -p 7474:7474 \
  -p 7687:7687 \
  -e NEO4J_AUTH=none \
  neo4j:5.26-community
```

### 2. Start Ollama (for LLM)
```bash
# Make sure Ollama is running
ollama serve

# Pull Llama model if needed
ollama pull llama3.2
```

### 3. Install Dependencies
```bash
pip install neo4j torch relik tqdm requests
```

## Usage

### Quick Start (Sample Mode - 10 documents)
```bash
cd /home/ib3/Documents/test_bp/knowledge_graph_vector_GC_Data/graph_check

# Run full pipeline with sample data
python3 main.py --mode full --sample
```

### Full Pipeline (All documents)
```bash
# Process all markdown files in GC_2021 folder
python3 main.py --mode full
```

### Run Individual Steps

**Step 1: Chunking**
```bash
python3 main.py --mode chunk --sample
# Output: output/chunks.json
```

**Step 2: ReLiK Extraction**
```bash
python3 main.py --mode extract
# Input: output/chunks.json
# Output: output/knowledge_graph.json
```

**Step 3: Load to Neo4j**
```bash
python3 main.py --mode load
# Input: output/knowledge_graph.json
# Loads data into Neo4j
```

**Step 4: Query Mode**
```bash
python3 main.py --mode query
# Interactive Q&A with the knowledge graph
```

### Skip Steps (Use Cached Data)
```bash
# Skip chunking, use existing chunks.json
python3 main.py --mode full --skip-chunk

# Skip extraction, use existing knowledge_graph.json
python3 main.py --mode full --skip-extract
```

## Example Queries

Once in query mode, try:

- **Quantitative Questions:**
  - "How many HVDC projects are there?"
  - "How many SynCon projects?"
  - "How many entities are in the graph?"

- **List Questions:**
  - "List all project types"
  - "Show me all projects"

- **Exploration:**
  - "What entities are mentioned in HVDC projects?"
  - "Show me relationships in the graph"

## Configuration

Edit `config.py` to customize:

- **Data Source**: Path to markdown files
- **Neo4j**: Connection details
- **ReLiK**: Model settings, GPU usage
- **LLM**: Ollama model (default: llama3.2)
- **Chunking**: Chunk size and overlap

## Project Structure

```
graph_check/
├── config.py              # Configuration
├── main.py                # Main orchestration script
├── README.md              # This file
├── services/
│   ├── markdown_chunker.py       # Step 1: Chunking
│   ├── relik_extractor.py        # Step 2: Entity extraction
│   ├── neo4j_loader.py           # Step 3: Load to Neo4j
│   ├── llm_query_generator.py    # Step 4a: Query generation
│   └── query_executor.py         # Step 4b: Execution & answers
└── output/
    ├── chunks.json               # Generated chunks
    └── knowledge_graph.json      # Extracted knowledge graph
```

## Troubleshooting

### Neo4j Not Running
```bash
docker ps | grep neo4j
# If not running:
docker start neo4j-vector-test
```

### Ollama Not Running
```bash
# Start Ollama
ollama serve

# Check if model is available
ollama list
```

### GPU Not Detected
Check `config.py` and set:
```python
USE_GPU = False  # Use CPU instead
```

### Connection Errors
- Neo4j: Check ports 7474 (HTTP) and 7687 (Bolt)
- Ollama: Check port 11434
- Update credentials in `config.py` if needed

## Performance

- **Sample Mode (10 docs)**: ~2-5 minutes
- **Full Pipeline (all GC_2021)**: ~1-3 hours (depends on document count and GPU)
- **ReLiK**: ~0.5-2 seconds per chunk (GPU), ~5-10 seconds (CPU)
- **Query Time**: ~2-5 seconds per question

## Output

- **chunks.json**: All text chunks with metadata
- **knowledge_graph.json**: Entities, relations, statistics
- **Neo4j Database**: Queryable knowledge graph with:
  - Project nodes
  - Entity nodes
  - Chunk nodes
  - RELATION relationships (entity-to-entity)
  - MENTIONS relationships (chunk-to-entity)
