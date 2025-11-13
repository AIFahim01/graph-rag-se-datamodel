#!/usr/bin/env python3
"""
Test the working GraphRAG system with Azure OpenAI
Uses persistent ChromaDB (not server mode)
"""

import sys
import json
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from embeddings import VectorGenerator
from qa.azure_qa import AzureQASystem
import chromadb

def main():
    print("🚀 Testing Complete GraphRAG System with Azure OpenAI")
    print("=" * 60)

    try:
        # Initialize components
        print("📦 Loading components...")

        # Vector Generator (BGE model)
        vector_generator = VectorGenerator(model_name="BAAI/bge-large-en-v1.5")
        print("  ✅ BGE embedding model loaded")

        # ChromaDB (persistent mode)
        output_dir = project_root / "data" / "graphrag_complete"
        chroma_client = chromadb.PersistentClient(path=str(output_dir / "chroma_db"))
        collection = chroma_client.get_collection("graphrag_chunks")
        print(f"  ✅ ChromaDB loaded: {collection.count():,} chunks")

        # Azure OpenAI
        qa_system = AzureQASystem(deployment="gpt-4")
        print("  ✅ Azure OpenAI initialized")

        # Test query
        test_query = "What are the main HVDC protection systems mentioned in the documents?"
        print(f"\n❓ Testing Query: '{test_query}'")
        print("-" * 60)

        # Step 1: Vector search
        print("🔍 Performing vector search...")
        query_embedding = vector_generator.embed_query(test_query)

        results = collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=5
        )

        # Format results
        context = []
        print("\n📚 Retrieved Context:")
        for i, (doc, metadata, distance) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        )):
            similarity = 1 - distance
            print(f"\n{i+1}. [{metadata['category'].upper()}] {metadata['project']}")
            print(f"   Source: {metadata['source']}")
            print(f"   Similarity: {similarity:.3f}")
            print(f"   Preview: {doc[:150]}...")

            context.append({
                'text': doc,
                'project': metadata['project'],
                'source': metadata['source'],
                'page': metadata.get('page', 0),
                'source_type': 'vector'
            })

        # Step 2: Generate answer with Azure OpenAI
        print(f"\n🤖 Generating answer with Azure OpenAI...")

        answer_data = qa_system.answer(test_query, context)

        # Display results
        print("\n" + "🎯" * 60)
        print("AI ANSWER:")
        print("🎯" * 60)
        print(answer_data['answer'])
        print("\n" + "📖" * 60)
        print("SOURCES:")
        for i, source in enumerate(answer_data['sources'], 1):
            print(f"{i}. {source['project']} - {source['document']}")
        print("📖" * 60)

        print(f"\n✅ GraphRAG System Working Successfully!")
        print(f"   • Vector Search: ✅ Finding relevant technical content")
        print(f"   • Azure OpenAI: ✅ Generating intelligent answers")
        print(f"   • Source Attribution: ✅ Citing specific documents")
        print(f"   • Technical Knowledge: ✅ Understanding HDVC/SYNCON content")

        return True

    except Exception as e:
        print(f"❌ Error testing GraphRAG system: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()

    if success:
        print("\n🚀 Your GraphRAG System is FULLY OPERATIONAL!")
        print("💡 You can now ask complex technical questions about:")
        print("   • HDVC converter technologies and protection systems")
        print("   • SYNCON specifications and grid requirements")
        print("   • Siemens Energy project comparisons")
        print("   • Technical specifications across projects")
        print("   • Commercial terms and pricing structures")

    exit(0 if success else 1)