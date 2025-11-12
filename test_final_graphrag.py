#!/usr/bin/env python3
"""
Test GraphRAG with explicit Azure credentials
"""

import sys
import os
from pathlib import Path

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Add src to path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from embeddings import VectorGenerator
from qa.azure_qa import AzureQASystem
import chromadb

def main():
    print("🚀 Testing GraphRAG with Azure OpenAI GPT-4.1")
    print("=" * 60)

    try:
        # Initialize BGE embeddings
        vector_generator = VectorGenerator(model_name="BAAI/bge-large-en-v1.5")
        print("✅ BGE model loaded")

        # Connect to ChromaDB
        output_dir = project_root / "data" / "graphrag_complete"
        chroma_client = chromadb.PersistentClient(path=str(output_dir / "chroma_db"))
        collection = chroma_client.get_collection("graphrag_chunks")
        print(f"✅ ChromaDB: {collection.count():,} chunks")

        # Initialize Azure OpenAI with explicit credentials
        azure_api_key = os.getenv('AZURE_API_KEY')
        azure_endpoint = os.getenv('AZURE_API_BASE')
        azure_version = os.getenv('AZURE_API_VERSION')

        if not all([azure_api_key, azure_endpoint, azure_version]):
            print("❌ Missing Azure credentials in .env file")
            return False

        qa_system = AzureQASystem(
            api_key=azure_api_key,
            api_base=azure_endpoint,
            api_version=azure_version,
            deployment="gpt-4.1"
        )
        print("✅ Azure OpenAI GPT-4.1 ready")

        # Test the system
        test_query = "What HVDC protection systems are mentioned?"

        print(f"\n❓ Query: '{test_query}'")
        print("-" * 50)

        # Vector search
        query_embedding = vector_generator.embed_query(test_query)
        results = collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=3
        )

        context = []
        for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
            context.append({
                'text': doc,
                'project': metadata['project'],
                'source': metadata['source'],
                'page': metadata.get('page', 0)
            })
            print(f"{i+1}. [{metadata['category'].upper()}] {metadata['project'][:40]}...")

        # Generate answer
        print(f"\n🤖 Asking GPT-4.1...")
        answer_data = qa_system.answer(test_query, context)

        print(f"\n🎯 ANSWER:")
        print(answer_data['answer'])

        print(f"\n📚 Sources used:")
        for source in answer_data['sources']:
            print(f"  • {source['project']} - {source['document']}")

        print(f"\n✅ SUCCESS! Your ultrathink HDVC/SYNCON knowledge is now AI-powered!")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()