#!/usr/bin/env python3
"""
Prepare the vector database for chat_graphrag.py script
Create the collection with the name expected by the chat script
"""

import sys
import json
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

try:
    from embeddings import VectorGenerator
    import chromadb

    def main():
        print("🔄 Preparing vector database for chat system...")

        # Load our existing chunks
        chunks_file = project_root / "data" / "graphrag_complete" / "graphrag_chunks.json"
        if not chunks_file.exists():
            print(f"❌ Chunks file not found: {chunks_file}")
            return False

        with open(chunks_file) as f:
            chunks = json.load(f)

        print(f"✓ Loaded {len(chunks):,} chunks")

        # Initialize vector generator
        vector_generator = VectorGenerator(model_name="BAAI/bge-large-en-v1.5")

        # Connect to our existing ChromaDB
        output_dir = project_root / "data" / "graphrag_complete"
        chroma_client = chromadb.PersistentClient(path=str(output_dir / "chroma_db"))

        # Remove old collection with different name if it exists
        try:
            chroma_client.delete_collection("graphrag_chunks")
        except:
            pass

        # Create collection with the name expected by chat script
        collection = chroma_client.create_collection(
            name="graphrag_chunks",
            metadata={"description": "HDVC/SYNCON GraphRAG chunks for chat"}
        )

        print("✓ Created collection 'graphrag_chunks'")

        # Generate embeddings with BGE
        print("🧠 Generating BGE embeddings...")
        embeddings = vector_generator.embed_chunks(chunks)

        # Prepare data
        chunk_ids = [f"chunk_{i}" for i in range(len(chunks))]
        chunk_texts = [chunk['text'] for chunk in chunks]
        chunk_metadatas = []

        for chunk in chunks:
            chunk_metadatas.append({
                'project': chunk.get('project', 'unknown'),
                'category': chunk.get('category', 'unknown'),
                'source': chunk.get('source', 'unknown'),
                'page': str(chunk.get('page', 0)),
                'document_type': chunk.get('document_type', 'other'),
                'char_count': str(chunk.get('char_count', 0))
            })

        # Add to collection in batches
        batch_size = 100
        for i in range(0, len(chunk_ids), batch_size):
            end_idx = min(i + batch_size, len(chunk_ids))

            collection.add(
                ids=chunk_ids[i:end_idx],
                documents=chunk_texts[i:end_idx],
                metadatas=chunk_metadatas[i:end_idx],
                embeddings=embeddings[i:end_idx].tolist()
            )

            print(f"  📥 Added batch {i//batch_size + 1}/{(len(chunk_ids) + batch_size - 1)//batch_size}")

        # Verify collection
        count = collection.count()
        print(f"✅ Collection ready with {count:,} documents")

        # Test a quick query
        test_query = "HVDC converter"
        results = collection.query(
            query_texts=[test_query],
            n_results=3
        )

        print(f"\n🔍 Test query '{test_query}':")
        for i, doc in enumerate(results['documents'][0]):
            metadata = results['metadatas'][0][i]
            print(f"  {i+1}. [{metadata['category'].upper()}] {metadata['project'][:30]}...")

        print("\n✅ Vector database is ready for chat_graphrag.py!")
        return True

    except Exception as e:
        print(f"❌ Error preparing database: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()

    if success:
        print("\n🚀 Ready to run:")
        print("python scripts/chat_graphrag.py --interactive --deployment gpt-4")

    exit(0 if success else 1)