#!/usr/bin/env python3
"""
Fix vector database for chat_graphrag.py script
"""

import sys
import json
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from embeddings import VectorGenerator
import chromadb

def main():
    print("🔄 Fixing vector database for chat system...")

    try:
        # Load chunks
        chunks_file = project_root / "data" / "graphrag_complete" / "graphrag_chunks.json"
        if not chunks_file.exists():
            print(f"❌ Chunks file not found: {chunks_file}")
            return False

        with open(chunks_file) as f:
            chunks = json.load(f)

        print(f"✓ Loaded {len(chunks):,} chunks")

        # Initialize components
        vector_generator = VectorGenerator(model_name="BAAI/bge-large-en-v1.5")
        output_dir = project_root / "data" / "graphrag_complete"
        chroma_client = chromadb.PersistentClient(path=str(output_dir / "chroma_db"))

        # Remove and recreate collection
        try:
            chroma_client.delete_collection("graphrag_chunks")
            print("✓ Removed old collection")
        except:
            pass

        collection = chroma_client.create_collection(
            name="graphrag_chunks",
            metadata={"description": "HDVC/SYNCON for chat"}
        )
        print("✓ Created new collection")

        # Generate embeddings
        print("🧠 Generating embeddings...")
        embeddings = vector_generator.embed_chunks(chunks)

        # Prepare data
        chunk_ids = [f"chunk_{i}" for i in range(len(chunks))]
        chunk_texts = [chunk['text'] for chunk in chunks]
        metadatas = [{
            'project': chunk.get('project', ''),
            'category': chunk.get('category', ''),
            'source': chunk.get('source', ''),
            'page': str(chunk.get('page', 0))
        } for chunk in chunks]

        # Add to collection
        batch_size = 100
        for i in range(0, len(chunk_ids), batch_size):
            end_idx = min(i + batch_size, len(chunk_ids))
            collection.add(
                ids=chunk_ids[i:end_idx],
                documents=chunk_texts[i:end_idx],
                metadatas=metadatas[i:end_idx],
                embeddings=embeddings[i:end_idx].tolist()
            )
            print(f"  📥 Batch {i//batch_size + 1} added")

        print(f"✅ Ready! Collection has {collection.count():,} documents")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🚀 Now run: python scripts/chat_graphrag.py --interactive --deployment gpt-4")
    exit(0 if success else 1)