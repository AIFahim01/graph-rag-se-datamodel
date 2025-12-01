"""
Configuration for Graph RAG System
"""

import os
from pathlib import Path

# Project paths
BASE_DIR = Path(__file__).parent
DATA_SOURCE = Path("/home/ib3/Documents/test_bp/knowledge_graph_vector_GC_Data/output copy/GC_2021")
OUTPUT_DIR = BASE_DIR / "output"
CHUNKS_FILE = OUTPUT_DIR / "chunks.json"
KNOWLEDGE_GRAPH_FILE = OUTPUT_DIR / "knowledge_graph.json"

# Create output directory
OUTPUT_DIR.mkdir(exist_ok=True)

# Neo4j Configuration
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "siemensenergy"  # Match docker NEO4J_AUTH=neo4j/siemensenergy
NEO4J_DATABASE = "neo4j"

# ReLiK Configuration
RELIK_MODEL = "relik-ie/relik-relation-extraction-small"
BATCH_SIZE = 8
USE_GPU = True
USE_SIMPLE_EXTRACTOR = True  # Set to True to use simple extractor (no ReLiK)

# LLM Configuration (Llama)
LLM_MODEL = "qwen3:8b"  # Ollama model name (qwen3:8b is available)
OLLAMA_API_URL = "http://localhost:11434/api/generate"

# Chunking Configuration
CHUNK_SIZE = 1000  # Characters per chunk
CHUNK_OVERLAP = 200  # Overlap between chunks

# Processing Configuration
MAX_DOCUMENTS = None  # None = process all, or set a number for testing
SAMPLE_MODE = False  # Set True to process only first 10 documents
