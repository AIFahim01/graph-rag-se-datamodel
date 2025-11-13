#!/usr/bin/env python3
"""
Background Embedding Generator Worker
Generates embeddings for a batch of chunks and saves to file
"""

import sys
import json
import argparse
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer

PROJECT_ROOT = Path(__file__).parent.parent.parent

def generate_batch_embeddings(batch_file: Path, output_file: Path, model_name: str = "BAAI/bge-large-en-v1.5"):
    """
    Generate embeddings for batch of chunks

    Args:
        batch_file: JSON file with chunk data
        output_file: Where to save embeddings (.npy)
        model_name: Embedding model to use
    """
    print(f"[Worker] Loading batch from: {batch_file}")

    # Load chunks
    with open(batch_file) as f:
        chunks = json.load(f)

    print(f"[Worker] Loaded {len(chunks)} chunks")
    print(f"[Worker] Loading embedding model: {model_name}")

    # Load model
    model = SentenceTransformer(model_name)

    # Extract texts
    texts = [chunk['text'][:512] for chunk in chunks]  # Limit to 512 chars

    print(f"[Worker] Generating embeddings...")

    # Generate embeddings
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)

    # Save to file
    np.save(output_file, embeddings)

    print(f"[Worker] Saved {len(embeddings)} embeddings to: {output_file}")
    print(f"[Worker] Embedding shape: {embeddings.shape}")
    print(f"[Worker] Complete!")

    return len(embeddings)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate embeddings for batch of chunks')
    parser.add_argument('--batch-file', required=True, help='Input JSON file with chunks')
    parser.add_argument('--output-file', required=True, help='Output .npy file for embeddings')
    parser.add_argument('--model', default='BAAI/bge-large-en-v1.5', help='Embedding model')

    args = parser.parse_args()

    try:
        count = generate_batch_embeddings(
            Path(args.batch_file),
            Path(args.output_file),
            args.model
        )
        print(f"[Worker] SUCCESS: Generated {count} embeddings")
        sys.exit(0)

    except Exception as e:
        print(f"[Worker] ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
