"""
Generate Embeddings for All Chunks

Reads all processed chunks and generates vector embeddings.
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from loguru import logger

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from embeddings import VectorGenerator


def main():
    # Paths
    datasets_dir = PROJECT_ROOT / "datasets"
    processed_dir = datasets_dir / "processed"
    embeddings_dir = datasets_dir / "embeddings"
    embeddings_dir.mkdir(exist_ok=True)

    print("\n" + "=" * 80)
    print("EMBEDDING GENERATOR")
    print("=" * 80)

    # Initialize vector generator
    print("\n📦 Loading embedding model...")
    generator = VectorGenerator(model_name="BAAI/bge-large-en-v1.5")

    # Process each project
    all_chunks = []
    project_metadata = {}

    for project_dir in processed_dir.iterdir():
        if not project_dir.is_dir():
            continue

        project_name = project_dir.name
        chunks_file = project_dir / "chunks.json"

        if not chunks_file.exists():
            continue

        # Load chunks
        with open(chunks_file, 'r') as f:
            chunks = json.load(f)

        print(f"\n📄 {project_name}: {len(chunks)} chunks")

        # Add project info to chunks
        for chunk in chunks:
            chunk['project'] = project_name

        all_chunks.extend(chunks)
        project_metadata[project_name] = {
            'num_chunks': len(chunks),
            'chunk_ids': [c['chunk_id'] for c in chunks]
        }

    print(f"\n✓ Total chunks to embed: {len(all_chunks)}")

    # Generate embeddings
    print("\n🔮 Generating embeddings...")
    embeddings = generator.embed_chunks(all_chunks)

    # Save embeddings
    print("\n💾 Saving embeddings...")
    output_path = embeddings_dir / "all_chunks_embeddings.npy"

    metadata = {
        'timestamp': datetime.now().isoformat(),
        'model_name': generator.model_name,
        'embedding_dim': generator.embedding_dim,
        'total_chunks': len(all_chunks),
        'projects': project_metadata,
        'chunk_ids': [c['chunk_id'] for c in all_chunks]
    }

    generator.save_embeddings(embeddings, output_path, metadata)

    # Also save chunks with their indices
    chunks_with_indices = []
    for idx, chunk in enumerate(all_chunks):
        chunk['embedding_index'] = idx
        chunks_with_indices.append(chunk)

    chunks_index_file = embeddings_dir / "chunks_with_indices.json"
    with open(chunks_index_file, 'w') as f:
        json.dump(chunks_with_indices, f, indent=2)

    print(f"✓ Saved chunk index to: {chunks_index_file}")

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Chunks embedded:        {len(all_chunks)}")
    print(f"Embedding dimension:    {generator.embedding_dim}")
    print(f"Output file:            {output_path}")
    print(f"Model used:             {generator.model_name}")
    print("=" * 80)
    print("\n✅ Embeddings ready for storage!")


if __name__ == "__main__":
    main()
