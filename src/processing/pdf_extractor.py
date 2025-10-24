"""
PDF text extraction with page-level granularity
"""

import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Dict
from loguru import logger


class PDFExtractor:
    """
    Extract text from PDF files with metadata preservation

    Extracts text page-by-page, preserving structure and tracking source information.
    """

    def __init__(self):
        self.logger = logger

    def extract(self, pdf_path: str) -> List[Dict]:
        """
        Extract text from PDF with page-level granularity

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of dicts with page text and metadata
        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        doc = fitz.open(pdf_path)
        pages_data = []

        for page_num, page in enumerate(doc, start=1):
            text = page.get_text("text")

            if text.strip():  # Only include pages with text
                pages_data.append({
                    "page_number": page_num,
                    "text": text,
                    "char_count": len(text),
                    "source_file": pdf_path.name,
                    "source_path": str(pdf_path)
                })

        doc.close()

        self.logger.info(f"Extracted {len(pages_data)} pages from {pdf_path.name}")
        return pages_data

    def extract_batch(self, pdf_dir: str) -> Dict[str, List[Dict]]:
        """
        Extract text from all PDFs in a directory

        Args:
            pdf_dir: Directory containing PDF files

        Returns:
            Dict mapping PDF names to extracted page data
        """
        pdf_dir = Path(pdf_dir)
        results = {}

        for pdf_file in pdf_dir.glob("*.pdf"):
            try:
                results[pdf_file.name] = self.extract(str(pdf_file))
            except Exception as e:
                self.logger.error(f"Failed to extract {pdf_file.name}: {e}")

        self.logger.info(f"Extracted {len(results)} PDF files from {pdf_dir}")
        return results
