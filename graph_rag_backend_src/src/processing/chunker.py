"""
Document chunking with overlap and metadata preservation
"""

from typing import List, Dict
from loguru import logger


class DocumentChunker:
    """
    Create overlapping chunks from extracted text with metadata

    Preserves page numbers, source information, and creates appropriate
    overlaps for better context retention.
    """

    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        """
        Initialize chunker

        Args:
            chunk_size: Target size of each chunk in characters
            overlap: Overlap between chunks in characters
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.logger = logger

    def chunk_pages(self, pages_data: List[Dict]) -> List[Dict]:
        """
        Create chunks from extracted pages

        Args:
            pages_data: List of page dicts from PDFExtractor

        Returns:
            List of chunk dicts with metadata
        """
        all_chunks = []
        chunk_id = 0

        for page_data in pages_data:
            text = page_data['text']
            page_num = page_data['page_number']
            source = page_data['source_file']

            # Chunk the page text
            start = 0
            while start < len(text):
                end = start + self.chunk_size
                chunk_text = text[start:end]

                # Try to break at sentence boundary
                if end < len(text):
                    last_period = chunk_text.rfind('. ')
                    if last_period > self.chunk_size * 0.7:  # At least 70% of chunk
                        end = start + last_period + 2
                        chunk_text = text[start:end]

                if chunk_text.strip():  # Only add non-empty chunks
                    all_chunks.append({
                        "chunk_id": f"chunk_{chunk_id}",
                        "text": chunk_text.strip(),
                        "page": page_num,
                        "source": source,
                        "source_path": page_data.get('source_path', ''),
                        "position": chunk_id,
                        "char_count": len(chunk_text.strip())
                    })
                    chunk_id += 1

                start = end - self.overlap

        self.logger.info(f"Created {len(all_chunks)} chunks from {len(pages_data)} pages")
        return all_chunks

    def chunk_document(self, pdf_path: str) -> List[Dict]:
        """
        Extract and chunk a single PDF

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of chunks with metadata
        """
        from .pdf_extractor import PDFExtractor

        extractor = PDFExtractor()
        pages = extractor.extract(pdf_path)
        return self.chunk_pages(pages)
