# Vector Database Creation Instructions

## Step 1: Create Conda Environment

**Option 1: Double-click the batch file**
1. Navigate to the project directory in Windows Explorer
2. Double-click `setup_vectordb_env.bat`
3. Wait for the environment to be created

**Option 2: Run from Command Prompt**
```cmd
cd "C:\Users\z0051yym\Desktop\test_bp_code\knowledge_graph_vector_GC_Data\graph-rag-se-datamodel"
setup_vectordb_env.bat
```

**Option 3: Manual conda commands**
```cmd
conda env create -f environment_vectordb.yml
conda activate hdvc_syncon_vectordb
```

## Step 2: Activate Environment and Run

```cmd
conda activate hdvc_syncon_vectordb
python build_vectordb_hdvc_syncon.py
```

## What the Script Will Do

1. **Process PDF Documents** from your HDVC/SYNCON subset
2. **Extract Text** from all PDF files using PyMuPDF
3. **Create Chunks** with 1000 characters each, 200 character overlap
4. **Generate Embeddings** using BGE-large-en-v1.5 model
5. **Create ChromaDB** for vector similarity search
6. **Test Search** with sample queries

## Expected Processing Time

- **Environment setup**: 5-10 minutes
- **Vector database creation**: 15-30 minutes (depending on document count)
- **Total documents**: ~32 project folders with multiple PDFs each

## Expected Outputs

```
data/vectordb/
├── hdvc_syncon_chunks.json      # Text chunks with metadata
├── hdvc_syncon_embeddings.npy   # Vector embeddings
├── hdvc_syncon_embeddings.json  # Embedding metadata
├── chroma_db/                   # ChromaDB vector database
└── processing_stats.json       # Processing statistics
```

## Environment Details

- **Python**: 3.10
- **Key packages**:
  - PyMuPDF: PDF text extraction
  - sentence-transformers: BGE model for embeddings
  - ChromaDB: Vector database
  - loguru: Logging
  - python-docx: Word document support

## Troubleshooting

### Environment creation fails
- Ensure Anaconda/Miniconda is installed
- Check internet connection for package downloads
- Try running as administrator

### PDF processing errors
- Check that PDFs are not corrupted
- Verify file permissions
- Some PDFs may be image-only (no extractable text)

### Out of memory
- Reduce batch size in the script
- Close other applications
- Ensure sufficient disk space (2-3GB recommended)

## After Completion

You'll have a fully functional vector database that can:
- Search HDVC/SYNCON documents by similarity
- Find relevant technical content
- Support knowledge graph queries
- Enable Q&A systems

Run the script and it will automatically test the database with sample queries!