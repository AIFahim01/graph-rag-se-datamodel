# REBEL Knowledge Graph Implementation Guide

## What We've Built

I've implemented a complete REBEL-based knowledge graph extraction system for your SE Datamodel GraphRAG project, following the article "Building Knowledge Graphs: REBEL, LlamaIndex, and REBEL + LlamaIndex" by Saurav Joshi.

## ✅ What's Been Created

### 1. REBEL Extraction Script (`scripts/build_knowledge_graph_rebel.py`)
Extracts relation triplets from your PDF documents using the REBEL model:
- Processes PDFs from `datasets/projects/`
- Extracts (entity1, relation, entity2) triplets
- Saves knowledge graphs as JSON
- Supports batch processing
- Auto-detects GPU/CPU

### 2. Visualization Script (`scripts/visualize_knowledge_graph.py`)
Creates visual representations of your knowledge graphs:
- Full graph visualizations
- Subgraph views for top entities
- Statistical reports
- NetworkX-based rendering

### 3. Documentation (`docs/knowledge-graph-extraction.md`)
Complete guide with:
- Usage instructions
- Output formats
- Integration with GraphRAG
- Troubleshooting tips

## 🚀 Quick Start

### Step 1: Build Knowledge Graphs

```bash
# Process all projects
python scripts/build_knowledge_graph_rebel.py --all

# Or process one project
python scripts/build_knowledge_graph_rebel.py --project alpha_erp_system
```

**What happens:**
- Downloads REBEL model (~1.5GB, first time only)
- Extracts text from PDFs
- Generates relation triplets
- Saves to `datasets/knowledge_graphs/`

### Step 2: Visualize Results

```bash
# Create visualizations
python scripts/visualize_knowledge_graph.py --all

# With subgraphs for top entities
python scripts/visualize_knowledge_graph.py --all --subgraphs
```

## 📊 What You Get

### Knowledge Graph Files

```
datasets/knowledge_graphs/
├── alpha_erp_system_knowledge_graph.json    # Full KG with metadata
├── alpha_erp_system_triplets.json           # Simple triplet list
├── alpha_erp_system_stats.json              # Statistics
│
├── alpha_erp_system_visualizations/
│   ├── alpha_erp_system_full_graph.png      # Visual graph
│   ├── alpha_erp_system_statistics.txt      # Detailed stats
│   └── subgraphs/                           # Entity-focused views
│
├── beta_cloud_migration_knowledge_graph.json
├── gamma_analytics_platform_knowledge_graph.json
└── ...
```

### Example Triplet

```json
{
  "head": "SAP S/4HANA",
  "relation": "is_a",
  "tail": "ERP System"
}
```

## 🔍 What REBEL Extracts

From your project PDFs, REBEL identifies:

### Entities
- Technologies: SAP, AWS, Kubernetes, Kafka, etc.
- Organizations: ABC Corporation, XYZ Tech, etc.
- Concepts: ERP, Cloud Migration, Analytics, etc.
- Products: S/4HANA, PostgreSQL, TensorFlow, etc.

### Relations
- **Identity**: is_a, type_of
- **Composition**: part_of, contains, includes
- **Properties**: has_property, located_in
- **Actions**: requires, implements, provides
- **Temporal**: precedes, follows
- **Organizational**: member_of, works_for

## 📈 Example Output

For **alpha_erp_system** project:

```
KNOWLEDGE GRAPH STATISTICS
==========================

Project: alpha_erp_system
PDFs Processed:          4
Text Segments:           18
Total Triplets:          243
Unique Triplets:         187
Unique Entities:         142
Unique Relations:        24

Sample Triplets:
• SAP S/4HANA --[is_a]--> ERP System
• ABC Corporation --[requires]--> inventory management
• Manufacturing --[uses]--> production planning
• REST APIs --[part_of]--> Integration Layer
• HANA Database --[stores]--> transaction data
```

## 🎯 Use Cases

### 1. Entity Discovery
Find all technologies mentioned across projects:
- Which ERP systems are used?
- What cloud platforms appear?
- Which databases are referenced?

### 2. Relationship Mapping
Understand connections:
- What does SAP S/4HANA provide?
- What components are part of the analytics platform?
- Which systems integrate with each other?

### 3. Cross-Project Analysis
Compare across projects:
- Common technologies used
- Similar architectural patterns
- Reusable components
- Best practices

### 4. GraphRAG Integration
Enhanced retrieval:
- Multi-hop reasoning
- Entity-based search
- Context-aware responses
- Relationship traversal

## ⚙️ Configuration

### Batch Size

Control memory usage:
```bash
# Default (2 texts per batch)
python scripts/build_knowledge_graph_rebel.py --all

# Smaller batches (if OOM errors)
python scripts/build_knowledge_graph_rebel.py --all --batch-size 1

# Larger batches (if you have lots of RAM/VRAM)
python scripts/build_knowledge_graph_rebel.py --all --batch-size 4
```

### Model Selection

```bash
# Use large model (default, more accurate)
python scripts/build_knowledge_graph_rebel.py --all --model Babelscape/rebel-large

# Use base model (faster, less accurate)
python scripts/build_knowledge_graph_rebel.py --all --model Babelscape/rebel-base
```

## 🔧 Current Status

**Your dataset:**
- ✅ 3 projects: alpha_erp_system, beta_cloud_migration, gamma_analytics_platform
- ✅ 10 PDFs total with domain-specific content
- ✅ All projects have metadata

**What's running now:**
- 🔄 REBEL model downloading (~1.5GB)
- 🔄 Extracting triplets from all projects
- ⏳ Estimated time: 5-15 minutes (depending on hardware)

## 📝 Next Steps

### 1. Review Knowledge Graphs

Once extraction completes:
```bash
# View statistics
cat datasets/knowledge_graphs/alpha_erp_system_statistics.txt

# Check JSON output
head -50 datasets/knowledge_graphs/alpha_erp_system_knowledge_graph.json
```

### 2. Create Visualizations

```bash
python scripts/visualize_knowledge_graph.py --all --subgraphs
```

### 3. Integrate with GraphRAG

Options:
- Load into Neo4j/NebulaGraph
- Use with LlamaIndex Knowledge Graph Index
- Build hybrid vector+graph retrieval system

### 4. Query Your Knowledge Graphs

Example queries you can answer:
- "Show all technologies used in alpha_erp_system"
- "What relationships exist between SAP and other systems?"
- "Find common components across all projects"
- "What does AWS provide in the cloud migration project?"

## 🐛 Troubleshooting

### Model Download Slow/Failed

```bash
# Download manually first
python -c "from transformers import AutoModelForSeq2SeqLM; AutoModelForSeq2SeqLM.from_pretrained('Babelscape/rebel-large')"
```

### Out of Memory

```bash
# Reduce batch size
python scripts/build_knowledge_graph_rebel.py --all --batch-size 1

# Or process one project at a time
python scripts/build_knowledge_graph_rebel.py --project alpha_erp_system
```

### Process Taking Too Long

- GPU recommended (10x faster than CPU)
- First run downloads model (~1.5GB)
- Subsequent runs are much faster
- Process one project to test: `--project alpha_erp_system`

## 📚 Technical Details

### REBEL Model
- **Paper**: "REBEL: Relation Extraction By End-to-end Language generation" (Cabot & Navigli, 2021)
- **Base**: BART (seq2seq transformer)
- **Training**: 200+ relation types from Wikipedia/Wikidata
- **Size**: ~1.5GB (rebel-large), ~420MB (rebel-base)

### Processing Pipeline
1. **PDF Extraction**: PyMuPDF extracts text page-by-page
2. **Batching**: Texts grouped for efficient processing
3. **Tokenization**: BERT-based tokenizer (max 512 tokens)
4. **Generation**: REBEL generates triplet sequences
5. **Parsing**: Extract structured triplets from generated text
6. **Deduplication**: Remove duplicate triplets
7. **Save**: JSON format for easy integration

## 🌟 Key Features

- ✅ **No Manual Annotation**: Automatic extraction from raw text
- ✅ **Multi-Document**: Processes all PDFs in a project
- ✅ **GPU Acceleration**: Automatic GPU detection and usage
- ✅ **Batch Processing**: Efficient handling of multiple texts
- ✅ **Rich Metadata**: Tracks source PDFs, pages, timestamps
- ✅ **Multiple Formats**: JSON, visualizations, statistics
- ✅ **Deduplication**: Removes redundant triplets
- ✅ **Visualization**: NetworkX-based graph rendering

## 📖 References

- [REBEL Paper (arXiv)](https://arxiv.org/abs/2104.08821)
- [REBEL Model (HuggingFace)](https://huggingface.co/Babelscape/rebel-large)
- [Original Article by Saurav Joshi](https://medium.com/@zilliz_learn/building-knowledge-graphs-rebel-llamaindex-and-rebel-llamaindex-2ab1c6a5dc4b)
- [Project Documentation](docs/knowledge-graph-extraction.md)

## 💡 Tips

1. **Start Small**: Test with one project first
2. **Check Logs**: Review `datasets/knowledge_graph_extraction.log`
3. **GPU Recommended**: 10x faster than CPU processing
4. **Batch Size**: Lower if memory issues, higher if plenty of RAM
5. **Visualize**: Use `--subgraphs` to see entity-centered views

---

**Your knowledge graph extraction is currently running in the background!**

Check progress with:
```bash
tail -f datasets/knowledge_graph_extraction.log
```

Or wait for completion message showing statistics for all projects.
