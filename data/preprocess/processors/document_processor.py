from pathlib import Path
from typing import Optional

class DocumentProcessor:
    def process_file(self, file_path: Path) -> tuple[str, bool]:
        """Process file and return (markdown_content, success)"""
        if not file_path.exists():
            return "", False

        ext = file_path.suffix.lower()

        if ext == '.pdf':
            return self._process_pdf(file_path)
        elif ext == '.docx':
            return self._process_docx(file_path)
        elif ext in {'.png', '.jpg', '.jpeg'}:
            return self._process_image(file_path)

        return "", False

    def _process_pdf(self, file_path: Path) -> tuple[str, bool]:
        """Extract PDF content using Docling with page numbers preserved"""
        try:
            from docling.document_converter import DocumentConverter
            from docling_core.types.doc import TextItem, TableItem

            print(f"   Processing PDF with Docling: {file_path.name}")
            converter = DocumentConverter()
            result = converter.convert(str(file_path))

            # Extract with page number tracking using iterate_items()
            markdown_parts = []
            current_page = 0

            for item, level in result.document.iterate_items():
                # Get page number from provenance metadata
                page_no = None
                if hasattr(item, 'prov') and len(item.prov) > 0:
                    page_no = item.prov[0].page_no

                # Add page marker when page changes
                if page_no and page_no != current_page:
                    markdown_parts.append(f"\n\n<!-- PAGE {page_no} -->\n\n")
                    current_page = page_no

                # Add content based on item type
                if isinstance(item, TextItem):
                    markdown_parts.append(item.text + "\n")
                elif isinstance(item, TableItem):
                    df = item.export_to_dataframe()
                    markdown_parts.append(df.to_markdown() + "\n")

            markdown_content = "".join(markdown_parts)

            print(f"   ✅ Extracted {len(markdown_content)} characters from {current_page} pages")
            return markdown_content, True

        except Exception as e:
            print(f"   ❌ Docling failed: {e}")
            import traceback
            traceback.print_exc()
            return f"# PDF: {file_path.name}\n\nDocling error: {e}", False

    def _process_docx(self, file_path: Path) -> tuple[str, bool]:
        # TODO: Implement Docling integration
        return f"# DOCX: {file_path.name}\n\n[DOCX processing placeholder]", True

    def _process_image(self, file_path: Path) -> tuple[str, bool]:
        # TODO: Implement DeepSeek-OCR integration
        return f"# Image: {file_path.name}\n\n[OCR processing placeholder]", True
