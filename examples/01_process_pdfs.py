"""
Example: Process PDFs and create chunks

This example shows how to extract text from PDFs and create chunks with metadata.
"""

from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from processing import PDFExtractor, DocumentChunker


def main():
    # Configure paths
    pdf_dir = Path("./data/pdfs")  # Your PDF directory
    output_dir = Path("./data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize components
    extractor = PDFExtractor()
    chunker = DocumentChunker(chunk_size=1000, overlap=200)

    # Extract PDFs
    print(f"Extracting PDFs from {pdf_dir}...")
    pdf_data = extractor.extract_batch(str(pdf_dir))

    # Chunk documents
    all_chunks = []
    for pdf_name, pages in pdf_data.items():
        print(f"Chunking {pdf_name}...")
        chunks = chunker.chunk_pages(pages)
        all_chunks.extend(chunks)

    print(f"\nTotal chunks created: {len(all_chunks)}")
    print(f"From {len(pdf_data)} PDF files")

    # Save chunks
    import json
    output_file = output_dir / "chunks.json"
    with open(output_file, "w") as f:
        json.dump(all_chunks, f, indent=2)

    print(f"\nChunks saved to: {output_file}")

    # Show sample
    if all_chunks:
        print(f"\nSample chunk:")
        sample = all_chunks[0]
        print(f"  ID: {sample['chunk_id']}")
        print(f"  Source: {sample['source']} (Page {sample['page']})")
        print(f"  Text: {sample['text'][:200]}...")


if __name__ == "__main__":
    main()
