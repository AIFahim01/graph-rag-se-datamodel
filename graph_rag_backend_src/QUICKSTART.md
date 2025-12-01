# Quick Start Guide

Get up and running with PDF-to-GraphRAG in minutes.

## Prerequisites

- Python 3.10+
- GPU recommended (NVIDIA with CUDA)
- 16GB+ RAM
- 100GB+ free disk space

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/your-org/pdf-to-graphrag.git
cd pdf-to-graphrag
```

### 2. Create Virtual Environment

```bash
python3.10 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup Ollama (Local LLM)

```bash
bash scripts/setup_ollama.sh
```

Or manual setup:
```bash
# Install Ollama
curl https://ollama.ai/install.sh | sh

# Download Llama model
ollama pull llama3.1:70b

# Start server
ollama serve
```

### 5. Setup Neo4j (Optional)

```bash
bash scripts/setup_neo4j.sh
```

Or use ChromaDB (no setup required - file-based).

### 6. Configure

```bash
cp config/.env.example .env
# Edit .env with your settings
```

## Basic Usage

### Step 1: Prepare Your PDFs

```bash
mkdir -p data/pdfs
# Copy your PDF files to data/pdfs/
```

### Step 2: Extract and Chunk

```bash
python examples/01_process_pdfs.py
```

**Output**: `data/processed/chunks.json`

### Step 3: Train Custom Embeddings

```bash
python examples/02_train_embeddings.py
```

**Output**: `models/custom_embeddings/` (trained model)

**Note**: This takes time! (hours on GPU)

### Step 4: Build Knowledge Graph

```bash
# Implement graph building first (see src/graph/)
python examples/03_build_graph.py
```

### Step 5: Query

```bash
python examples/04_query_system.py "Your question here"
```

## Minimal Example

```python
from src.processing import PDFExtractor, DocumentChunker
from src.training import TrainingPairGenerator, ContrastiveTrainer

# 1. Process PDFs
extractor = PDFExtractor()
chunker = DocumentChunker()

pages = extractor.extract("path/to/document.pdf")
chunks = chunker.chunk_pages(pages)

# 2. Generate training pairs
pair_gen = TrainingPairGenerator()
pairs = pair_gen.generate_from_structure(chunks)

# 3. Train custom model
trainer = ContrastiveTrainer(base_model="BAAI/bge-large-en-v1.5")
model = trainer.train(
    training_pairs=pairs,
    output_path="./models/custom",
    epochs=3,
    batch_size=32
)

# 4. Use model
embeddings = model.encode(["text to embed"])
```

## Verify Installation

```bash
# Check Python version
python --version  # Should be 3.10+

# Check PyTorch (GPU)
python -c "import torch; print(f'PyTorch: {torch.__version__}, CUDA: {torch.cuda.is_available()}')"

# Check Ollama
curl http://localhost:11434/api/tags

# Check sentence-transformers
python -c "from sentence_transformers import SentenceTransformer; print('OK')"
```

## Troubleshooting

**"No module named 'src'"**:
```bash
# Install in editable mode
pip install -e .
```

**"CUDA out of memory"**:
```bash
# Reduce batch size in examples/02_train_embeddings.py
# Change batch_size=32 to batch_size=16 or batch_size=8
```

**"Ollama connection refused"**:
```bash
# Start Ollama
ollama serve

# Verify running
ps aux | grep ollama
```

## Next Steps

1. Read [Architecture Documentation](docs/architecture.md)
2. Understand [Contrastive Learning](docs/contrastive-learning.md)
3. Learn about [GraphRAG](docs/graphrag.md)
4. Explore [Examples](examples/README.md)
5. Implement remaining blocks (4-8) as needed

## Support

- Issues: [GitHub Issues](https://github.com/your-org/pdf-to-graphrag/issues)
- Discussions: [GitHub Discussions](https://github.com/your-org/pdf-to-graphrag/discussions)
- Documentation: [docs/](docs/)

---

**Happy building!** 🚀
