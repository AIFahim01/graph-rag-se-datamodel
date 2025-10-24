# Examples

Complete workflow examples for PDF-to-GraphRAG system.

## Prerequisites

1. Install dependencies: `pip install -r requirements.txt`
2. Setup Ollama: `bash scripts/setup_ollama.sh`
3. Place PDF files in `./data/pdfs/`

## Example Scripts

### 01_process_pdfs.py
**Purpose**: Extract and chunk PDF documents

**Usage**:
```bash
python examples/01_process_pdfs.py
```

**Output**: `data/processed/chunks.json`

**What it does**:
- Extracts text from all PDFs in `data/pdfs/`
- Creates 1000-char chunks with 200-char overlap
- Preserves metadata (page numbers, source files)

---

### 02_train_embeddings.py
**Purpose**: Train custom embedding model

**Usage**:
```bash
python examples/02_train_embeddings.py
```

**Requirements**: Run `01_process_pdfs.py` first

**Output**: `models/custom_embeddings/` (trained model)

**What it does**:
- Generates training pairs from document structure
- Trains model with contrastive learning (MNRL)
- Saves custom embedding model

**Note**: Training takes time (hours on GPU, longer on CPU)

---

### 03_build_graph.py
**Purpose**: Build knowledge graph from documents

**Prerequisites**:
- Ollama running with llama3.1:70b
- Chunks from step 01

**What it does**:
- Extracts entities using local LLM
- Identifies relationships
- Builds knowledge graph
- Detects communities
- Generates summaries

---

### 04_query_system.py
**Purpose**: Query the GraphRAG system

**Prerequisites**: Complete steps 01-03

**What it does**:
- Loads custom embedding model
- Performs multi-level GraphRAG retrieval
- Generates answers with local LLM

**Usage**:
```bash
python examples/04_query_system.py "What are the voltage requirements?"
```

---

## Quick Start (All Steps)

```bash
# 1. Process PDFs
python examples/01_process_pdfs.py

# 2. Train embeddings (takes time!)
python examples/02_train_embeddings.py

# 3. Build knowledge graph
python examples/03_build_graph.py

# 4. Query system
python examples/04_query_system.py "Your question here"
```

## Sample Data

Place sample PDFs in `./data/pdfs/` or use the provided samples:
- `sample_data/technical_spec.pdf`
- `sample_data/safety_manual.pdf`

## Troubleshooting

**"Module not found" error**:
- Make sure you're running from the repository root
- Install dependencies: `pip install -r requirements.txt`

**"CUDA out of memory"**:
- Reduce batch size in training
- Use CPU (slower): Set `device='cpu'` in trainer

**"Ollama connection refused"**:
- Start Ollama: `ollama serve`
- Check status: `ollama list`

## Next Steps

After running examples, see:
- `docs/architecture.md` for system design
- `docs/contrastive-learning.md` for training details
- `docs/graphrag.md` for retrieval approach
