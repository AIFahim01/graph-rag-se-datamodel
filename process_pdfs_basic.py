#!/usr/bin/env python3
"""
Basic PDF Processing for HDVC/SYNCON Documents
This script extracts text and creates chunks without embeddings (to test the data processing pipeline)
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# Add src to path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

try:
    from processing import PDFExtractor, DocumentChunker
    from loguru import logger

    # Setup logging
    logger.remove()
    logger.add(sys.stderr, level="INFO", format="{time} | {level} | {message}")

except ImportError as e:
    print(f"Missing dependencies: {e}")
    sys.exit(1)


def find_pdf_files(base_dir: Path, max_files: int = 10) -> List[Path]:
    """Find PDF files (limited for testing)"""
    pdf_files = []

    for pdf_path in base_dir.rglob("*.pdf"):
        if pdf_path.stat().st_size > 1024:  # > 1KB
            pdf_files.append(pdf_path)
            if len(pdf_files) >= max_files:
                break

    return sorted(pdf_files)


def add_project_metadata(chunks: List[Dict], project_name: str, category: str) -> List[Dict]:
    """Add project metadata to chunks"""
    for chunk in chunks:
        chunk['project'] = project_name
        chunk['category'] = category

        # Determine document type
        source_lower = chunk['source'].lower()
        if any(keyword in source_lower for keyword in ['pricing', 'commercial', 'offer']):
            chunk['document_type'] = 'commercial'
        elif any(keyword in source_lower for keyword in ['technical', 'spec', 'study', 'analysis']):
            chunk['document_type'] = 'technical'
        else:
            chunk['document_type'] = 'other'

    return chunks


def main():
    """Process a sample of PDFs to test the pipeline"""
    data_dir = project_root / "data" / "pdfs"
    output_dir = project_root / "data" / "processed_sample"
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("🧪 Testing PDF Processing Pipeline (Sample)")
    logger.info("=" * 60)

    # Initialize components
    pdf_extractor = PDFExtractor()
    chunker = DocumentChunker(chunk_size=1000, overlap=200)

    all_chunks = []
    stats = {
        'start_time': datetime.now(),
        'files_processed': 0,
        'chunks_created': 0,
        'categories': {}
    }

    # Process a sample from each category
    for category in ['hdvc', 'syncon']:
        category_dir = data_dir / category
        if not category_dir.exists():
            continue

        logger.info(f"\n📁 Processing {category.upper()} sample...")

        # Get first project directory
        project_dirs = [d for d in category_dir.iterdir() if d.is_dir()]
        if not project_dirs:
            continue

        project_dir = project_dirs[0]  # Just process first project
        project_name = project_dir.name
        logger.info(f"  📄 Sample project: {project_name}")

        # Find some PDFs (limited for testing)
        pdf_files = find_pdf_files(project_dir, max_files=3)
        if not pdf_files:
            logger.warning(f"    No PDF files found in {project_name}")
            continue

        project_chunks = []

        for pdf_file in pdf_files:
            try:
                logger.info(f"    📖 Processing: {pdf_file.name}")

                # Extract pages
                pages = pdf_extractor.extract(str(pdf_file))
                if not pages:
                    logger.warning(f"      No text extracted from {pdf_file.name}")
                    continue

                # Create chunks
                file_chunks = chunker.chunk_pages(pages)

                # Add metadata
                file_chunks = add_project_metadata(file_chunks, project_name, category)

                project_chunks.extend(file_chunks)
                stats['files_processed'] += 1

                logger.info(f"      ✓ {len(file_chunks)} chunks created")

                # Show sample chunk
                if file_chunks:
                    sample_chunk = file_chunks[0]
                    logger.info(f"      📄 Sample text: {sample_chunk['text'][:100]}...")

            except Exception as e:
                logger.error(f"      ❌ Error processing {pdf_file.name}: {e}")
                continue

        if project_chunks:
            all_chunks.extend(project_chunks)
            stats['categories'][category] = {
                'chunks': len(project_chunks),
                'files': stats['files_processed']
            }
            logger.info(f"    ✅ {category.upper()} sample: {len(project_chunks)} chunks")

    if not all_chunks:
        logger.error("❌ No chunks created from sample PDFs")
        return False

    stats['chunks_created'] = len(all_chunks)
    stats['end_time'] = datetime.now()

    # Save sample chunks
    sample_file = output_dir / "sample_chunks.json"
    logger.info(f"\n💾 Saving {len(all_chunks)} sample chunks to {sample_file}")

    with open(sample_file, 'w') as f:
        json.dump(all_chunks, f, indent=2)

    # Show statistics
    logger.info("\n" + "📊" * 50)
    logger.info("SAMPLE PROCESSING COMPLETE!")
    logger.info("📊" * 50)
    logger.info(f"Files processed: {stats['files_processed']}")
    logger.info(f"Chunks created: {stats['chunks_created']}")
    logger.info(f"Processing time: {stats['end_time'] - stats['start_time']}")

    for category, data in stats['categories'].items():
        logger.info(f"{category.upper()}: {data['chunks']} chunks from {data['files']} files")

    # Show sample chunks
    if all_chunks:
        logger.info(f"\n📋 Sample chunks:")
        for i, chunk in enumerate(all_chunks[:3]):
            logger.info(f"{i+1}. [{chunk['category'].upper()}] {chunk['project']}")
            logger.info(f"   Source: {chunk['source']} (page {chunk['page']})")
            logger.info(f"   Type: {chunk['document_type']}")
            logger.info(f"   Text: {chunk['text'][:150]}...")
            logger.info("")

    return True


if __name__ == "__main__":
    success = main()

    if success:
        print("\n" + "🎯" * 60)
        print("READY FOR FULL PIPELINE!")
        print("🎯" * 60)
        print("✅ PDF extraction working")
        print("✅ Text chunking working")
        print("✅ Metadata extraction working")
        print("")
        print("Next steps:")
        print("1. Set up conda environment: setup_vectordb_env.bat")
        print("2. Run full pipeline: python build_vectordb_hdvc_syncon.py")
        print("3. This will create BOTH vector database AND knowledge graph")

    exit(0 if success else 1)