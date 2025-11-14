import json
from datetime import datetime
from pathlib import Path
from typing import List
from .document_processor import DocumentExtractedResponse
from PIL.Image import Image

class OutputManager:
    def __init__(self, output_base_path: Path, input_base_path: Path):
        self.output_base_path = Path(output_base_path)
        self.input_base_path = Path(input_base_path)
    
    def save_processed_file(self, file_content: DocumentExtractedResponse) -> tuple[bool, str]:
        """Save a single processed file. Returns success status."""
        try:
            relative_path = file_content.file_path.relative_to(self.input_base_path)

            relative_parents = list(relative_path.parts[:-1])

            output_file_dir = self.output_base_path
            for parent in relative_parents:
                output_file_dir /= parent

            output_file_dir /= file_content.file_path.stem

            output_full_file = output_file_dir / f"{file_content.file_path.stem} - full_content.md"
            output_full_file.parent.mkdir(parents=True, exist_ok=True)
            output_full_file.write_text(file_content.full_content, encoding='utf-8')

            self._save_pages(output_file_dir, file_content.file_path, file_content.content_pages)

            self._save_images(output_file_dir, file_content.file_path, "page", file_content.pages)
            self._save_images(output_file_dir, file_content.file_path, "picture", file_content.pictures)
            self._save_images(output_file_dir, file_content.file_path, "table", file_content.tables)

            self._save_file_metadata(output_file_dir, relative_parents, file_content)

            return True, "Successfully saved processed file."
        except Exception as e:
            print(f"Error saving processed file {file_content.file_path}: {e}")
            return False, str(e)

    def _save_pages(self, output_file_dir: Path, file_path: Path, pages: List[str]):
        idx = 1
        for page in pages:
            output_page_file = output_file_dir / f"{file_path.stem} - page {idx}.md"
            output_page_file.parent.mkdir(parents=True, exist_ok=True)
            output_page_file.write_text(page, encoding='utf-8')
            idx += 1

    def _save_images(self, output_file_dir: Path, file_path: Path, alias: str, images: List[Image]):
        idx = 1
        for pil_image in images:
            output_image_file = output_file_dir / f"{alias}s" / f"{file_path.stem} - {alias} {idx}.png"
            output_image_file.parent.mkdir(parents=True, exist_ok=True)
            with output_image_file.open("wb") as fp:
                pil_image.save(fp, format="PNG")
            idx += 1

    def _save_file_metadata(self, output_file_dir: Path, relative_parents: List[str], file_content: DocumentExtractedResponse):
        metadata_file = output_file_dir / f"{file_content.file_path.stem} - metadata.json"
        metadata_file.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "file_name": file_content.file_path.name,
            "file_path": str(file_content.file_path),
            "file_type": file_content.file_path.suffix,
            "extracted_at": datetime.now().isoformat(),
            "pages": len(file_content.content_pages),
            "images": len(file_content.pictures),
            "tables": len(file_content.tables),
            "relative_parents": relative_parents,
            "caption_texts": file_content.caption_texts,
            "annotation_texts": file_content.annotation_texts
        }
        with metadata_file.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)