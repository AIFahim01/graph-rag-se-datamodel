"""
Load Embeddings into ChromaDB

Loads chunk embeddings and metadata into ChromaDB for vector retrieval.
"""

import sys
import json
import numpy as np
from pathlib import Path
from loguru import logger

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from storage.chroma_store import ChromaVectorStore


def main():
    datasets_dir = PROJECT_ROOT / "datasets"
    embeddings_dir = datasets_dir / "embeddings"

    print("\n" + "=" * 80)
    print("CHROMADB LOADER")
    print("=" * 80)

    # Load embeddings
    print("\n📦 Loading embeddings...")
    embeddings_file = embeddings_dir / "all_chunks_embeddings.npy"
    chunks_file = embeddings_dir / "chunks_with_indices.json"

    embeddings = np.load(embeddings_file)
    with open(chunks_file, 'r') as f:
        chunks = json.load(f)

    print(f"✓ Loaded {len(chunks)} chunks with {embeddings.shape[1]}-dim embeddings")

    # Connect to ChromaDB
    print("\n🔗 Connecting to ChromaDB...")
    store = ChromaVectorStore()

    # Insert chunks
    print(f"\n💾 Inserting into ChromaDB collection 'graphrag_chunks'...")
    store.insert_chunks(
        collection_name='graphrag_chunks',
        chunks=chunks,
        embeddings=embeddings.tolist()
    )

    print("\n" + "=" * 80)
    print("✅ ChromaDB loaded successfully!")
    print("=" * 80)
    print(f"Collection: graphrag_chunks")
    print(f"Chunks: {len(chunks)}")
    print(f"Embedding dim: {embeddings.shape[1]}")
    print("=" * 80)
    print("\n✅ Ready for vector search!")


if __name__ == "__main__":
    main()
