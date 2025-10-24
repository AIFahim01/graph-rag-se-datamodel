"""
Example: Train custom embeddings with contrastive learning

This example shows how to generate training pairs from document structure
and train a custom embedding model.
"""

from pathlib import Path
import sys
import json

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from training import TrainingPairGenerator, ContrastiveTrainer


def main():
    # Load chunks from previous step
    chunks_file = Path("./data/processed/chunks.json")

    if not chunks_file.exists():
        print("Error: chunks.json not found. Run 01_process_pdfs.py first.")
        return

    with open(chunks_file) as f:
        chunks = json.load(f)

    print(f"Loaded {len(chunks)} chunks")

    # Generate training pairs
    print("\nGenerating training pairs from document structure...")
    pair_generator = TrainingPairGenerator()
    training_pairs = pair_generator.generate_from_structure(chunks)

    print(f"Generated {len(training_pairs)} positive pairs")

    # Show sample pairs
    print("\nSample training pairs:")
    for i, pair in enumerate(training_pairs[:3]):
        print(f"\nPair {i+1} ({pair['rule']}, confidence: {pair['confidence']:.2f}):")
        print(f"  Chunk A: {pair['chunk_a']['text'][:100]}...")
        print(f"  Chunk B: {pair['chunk_b']['text'][:100]}...")

    # Train custom model
    print("\n" + "="*60)
    print("Starting embedding training (this will take time)...")
    print("="*60)

    trainer = ContrastiveTrainer(base_model="BAAI/bge-large-en-v1.5")

    output_path = "./models/custom_embeddings"

    custom_model = trainer.train(
        training_pairs=training_pairs,
        output_path=output_path,
        epochs=3,
        batch_size=32,
        learning_rate=2e-5,
        warmup_steps=100
    )

    print(f"\n✓ Training complete!")
    print(f"✓ Custom model saved to: {output_path}")

    # Test the model
    print("\nTesting custom model...")
    test_texts = [
        "690V voltage rating specifications",
        "Circuit breaker for 690V systems"
    ]

    embeddings = custom_model.encode(test_texts)
    print(f"Embedding dimensions: {embeddings.shape}")
    print("Custom model ready for use!")


if __name__ == "__main__":
    main()
