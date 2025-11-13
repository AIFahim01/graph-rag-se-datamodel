#!/usr/bin/env python3
"""
Build Vector Database from HDVC and SYNCON Documents

This script processes the HDVC and SYNCON subset documents to create:
1. Text chunks with metadata
2. Vector embeddings using BGE model
3. ChromaDB vector database for similarity search
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
    from embeddings import VectorGenerator
    import chromadb
    from loguru import logger

    # Setup logging
    logger.remove()
    logger.add(sys.stderr, level="INFO", format="{time} | {level} | {message}")

except ImportError as e:
    print(f"Missing required dependencies: {e}")
    print("Please install: pip install PyMuPDF sentence-transformers chromadb loguru python-docx")
    sys.exit(1)


def find_pdf_files(base_dir: Path) -> List[Path]:
    """Find all PDF files in HDVC and SYNCON directories"""
    pdf_files = []

    for pdf_path in base_dir.rglob("*.pdf"):
        # Skip very small files (likely not useful documents)
        if pdf_path.stat().st_size > 1024:  # > 1KB
            pdf_files.append(pdf_path)

    return sorted(pdf_files)


def add_project_metadata(chunks: List[Dict], project_name: str, category: str) -> List[Dict]:
    """Add project metadata to chunks"""
    for chunk in chunks:
        chunk['project'] = project_name
        chunk['category'] = category

        # Determine if this is a technical or commercial document
        source_lower = chunk['source'].lower()
        if any(keyword in source_lower for keyword in ['pricing', 'commercial', 'offer']):
            chunk['document_type'] = 'commercial'
        elif any(keyword in source_lower for keyword in ['technical', 'spec', 'study', 'analysis']):
            chunk['document_type'] = 'technical'
        else:
            chunk['document_type'] = 'other'

    return chunks


def main():
    """Main processing pipeline"""
    # Configuration
    data_dir = project_root / "data" / "pdfs"
    output_dir = project_root / "data" / "vectordb"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize components
    logger.info("🚀 Starting HDVC/SYNCON Vector Database Creation")
    logger.info("=" * 60)

    pdf_extractor = PDFExtractor()
    chunker = DocumentChunker(chunk_size=1000, overlap=200)
    vector_generator = VectorGenerator(model_name="BAAI/bge-large-en-v1.5")

    # Process each category
    all_chunks = []
    processing_stats = {
        'start_time': datetime.now(),
        'projects_processed': 0,
        'files_processed': 0,
        'chunks_created': 0,
        'categories': {}
    }

    for category in ['hdvc', 'syncon']:
        category_dir = data_dir / category
        if not category_dir.exists():
            logger.warning(f"Category directory not found: {category_dir}")
            continue

        logger.info(f"\n📁 Processing {category.upper()} projects...")
        category_chunks = []
        category_stats = {'projects': 0, 'files': 0, 'chunks': 0}

        # Process each project folder
        for project_dir in category_dir.iterdir():
            if not project_dir.is_dir():
                continue

            project_name = project_dir.name
            logger.info(f"  📄 Processing project: {project_name}")

            # Find all PDFs in the project
            pdf_files = find_pdf_files(project_dir)
            if not pdf_files:
                logger.warning(f"    No PDF files found in {project_name}")
                continue

            project_chunks = []

            for pdf_file in pdf_files:
                try:
                    logger.info(f"    📖 Extracting: {pdf_file.name}")

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
                    category_stats['files'] += 1
                    processing_stats['files_processed'] += 1

                    logger.info(f"      ✓ {len(file_chunks)} chunks created")

                except Exception as e:
                    logger.error(f"      ❌ Error processing {pdf_file.name}: {e}")
                    continue

            if project_chunks:
                category_chunks.extend(project_chunks)
                category_stats['projects'] += 1
                category_stats['chunks'] += len(project_chunks)
                processing_stats['projects_processed'] += 1
                logger.info(f"    ✅ Project {project_name}: {len(project_chunks)} total chunks")

        if category_chunks:
            all_chunks.extend(category_chunks)
            processing_stats['categories'][category] = category_stats
            processing_stats['chunks_created'] += len(category_chunks)

            logger.info(f"✅ {category.upper()} complete: {len(category_chunks)} chunks from {category_stats['projects']} projects")

    if not all_chunks:
        logger.error("❌ No chunks created. Exiting.")
        return False

    logger.info(f"\n🎯 TOTAL: {len(all_chunks)} chunks from {processing_stats['projects_processed']} projects")

    # Save chunks with metadata
    chunks_file = output_dir / "hdvc_syncon_chunks.json"
    logger.info(f"💾 Saving chunks to {chunks_file}")

    # Add embedding indices for later reference
    for i, chunk in enumerate(all_chunks):
        chunk['embedding_index'] = i

    with open(chunks_file, 'w') as f:
        json.dump(all_chunks, f, indent=2)

    # Generate embeddings
    logger.info(f"\n🧠 Generating embeddings for {len(all_chunks)} chunks...")
    embeddings = vector_generator.embed_chunks(all_chunks)

    # Save embeddings
    embeddings_file = output_dir / "hdvc_syncon_embeddings.npy"
    vector_generator.save_embeddings(
        embeddings,
        embeddings_file,
        metadata={
            'model_name': vector_generator.model_name,
            'embedding_dim': vector_generator.embedding_dim,
            'num_chunks': len(all_chunks),
            'creation_date': datetime.now().isoformat(),
            'categories': list(processing_stats['categories'].keys())
        }
    )

    # Create ChromaDB collection
    logger.info(f"\n🔍 Creating ChromaDB collection...")

    # Initialize ChromaDB
    chroma_client = chromadb.PersistentClient(path=str(output_dir / "chroma_db"))

    # Create or get collection
    collection_name = "hdvc_syncon_documents"
    try:
        chroma_client.delete_collection(collection_name)  # Clear existing
    except:
        pass

    collection = chroma_client.create_collection(
        name=collection_name,
        metadata={"description": "HDVC and SYNCON technical documents"}
    )

    # Prepare data for ChromaDB
    chunk_ids = [f"chunk_{i}" for i in range(len(all_chunks))]
    chunk_texts = [chunk['text'] for chunk in all_chunks]
    chunk_metadatas = []

    for chunk in all_chunks:
        metadata = {
            'project': chunk['project'],
            'category': chunk['category'],
            'source': chunk['source'],
            'page': str(chunk['page']),
            'document_type': chunk.get('document_type', 'other'),
            'char_count': str(chunk['char_count'])
        }
        chunk_metadatas.append(metadata)

    # Add to ChromaDB
    logger.info(f"📥 Adding {len(chunk_ids)} documents to ChromaDB...")

    batch_size = 100  # Add in batches to avoid memory issues
    for i in range(0, len(chunk_ids), batch_size):
        end_idx = min(i + batch_size, len(chunk_ids))

        collection.add(
            ids=chunk_ids[i:end_idx],
            documents=chunk_texts[i:end_idx],
            metadatas=chunk_metadatas[i:end_idx],
            embeddings=embeddings[i:end_idx].tolist()
        )

        logger.info(f"  📥 Added batch {i//batch_size + 1}/{(len(chunk_ids) + batch_size - 1)//batch_size}")

    # Final statistics
    processing_stats['end_time'] = datetime.now()
    processing_stats['duration'] = str(processing_stats['end_time'] - processing_stats['start_time'])

    stats_file = output_dir / "processing_stats.json"
    with open(stats_file, 'w') as f:
        json.dump(processing_stats, f, indent=2, default=str)

    logger.info("\n" + "🎉" * 60)
    logger.info("VECTOR DATABASE CREATION COMPLETE!")
    logger.info("🎉" * 60)
    logger.info(f"📊 Projects processed: {processing_stats['projects_processed']}")
    logger.info(f"📄 Files processed: {processing_stats['files_processed']}")
    logger.info(f"🔢 Chunks created: {processing_stats['chunks_created']}")
    logger.info(f"⏱️  Processing time: {processing_stats['duration']}")
    logger.info(f"💾 Chunks saved to: {chunks_file}")
    logger.info(f"🧠 Embeddings saved to: {embeddings_file}")
    logger.info(f"🔍 ChromaDB created at: {output_dir / 'chroma_db'}")
    logger.info(f"📈 Stats saved to: {stats_file}")

    return True


def test_search():
    """Test the vector database with a sample query"""
    logger.info("\n🔍 Testing vector search...")

    output_dir = project_root / "data" / "vectordb"
    chroma_client = chromadb.PersistentClient(path=str(output_dir / "chroma_db"))
    collection = chroma_client.get_collection("hdvc_syncon_documents")

    # Test query
    test_query = "HVDC converter station protection"

    logger.info(f"Query: '{test_query}'")
    results = collection.query(
        query_texts=[test_query],
        n_results=5
    )

    logger.info(f"📋 Top 5 results:")
    for i, doc in enumerate(results['documents'][0]):
        metadata = results['metadatas'][0][i]
        distance = results['distances'][0][i]

        logger.info(f"  {i+1}. [{metadata['category'].upper()}] {metadata['project']}")
        logger.info(f"     Source: {metadata['source']} (page {metadata['page']})")
        logger.info(f"     Similarity: {1-distance:.3f}")
        logger.info(f"     Text preview: {doc[:100]}...")
        logger.info("")


if __name__ == "__main__":
    success = main()

    if success:
        # Test the database
        test_search()

    exit(0 if success else 1)