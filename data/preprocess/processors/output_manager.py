import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from .document_processor import DocumentExtractedResponse
from PIL import Image

class OutputManager:
    def __init__(self, output_base_path: Path):
        self.output_base_path = Path(output_base_path)
        self.processed_offers_file = self.output_base_path / "processed_offers.json"
        self.processed_offers = self._load_processed_offers()
    
    def is_offer_processed(self, offer_name: str) -> bool:
        return offer_name in self.processed_offers
    
    def save_offer_documents(self, start_time: float, offer_name: str, relative_parents: List[str], files_contents: List[DocumentExtractedResponse]) -> bool:
        """Save documents for an offer. Returns success status."""
        offer_folder = self.output_base_path
        relative_offer_name = ''
        for p in relative_parents:
            offer_folder /= p
            relative_offer_name += f"{p} / "

        offer_folder = offer_folder / offer_name
        relative_offer_name += offer_name
        offer_folder.mkdir(parents=True, exist_ok=True)
        
        success_count = 0
        processed_files: List[str] = []

        for fc in files_contents:
            if not (fc.success and fc.full_content):
                continue

            try:
                subdir = self._relative_subdir(offer_name, fc.file_path)
                output_file_dir = offer_folder / subdir / f"{fc.file_path.stem}"
                output_full_file = output_file_dir / f"{fc.file_path.stem} - full_content.md"
                output_full_file.parent.mkdir(parents=True, exist_ok=True)
                output_full_file.write_text(fc.full_content, encoding='utf-8')

                self._save_pages(output_file_dir, fc.file_path, fc.content_pages)

                self._save_images(output_file_dir, fc.file_path, "page", fc.pages)
                self._save_images(output_file_dir, fc.file_path, "picture", fc.pictures)
                self._save_images(output_file_dir, fc.file_path, "table", fc.tables)

                relative_file_parents = relative_parents.copy()
                relative_file_parents.append(offer_name)
                relative_file_parents.extend(list(subdir.parts))
                relative_file_parents.append(fc.file_path.stem)
                self._save_metadata(output_file_dir, offer_name, relative_file_parents, fc)
                
                success_count += 1
                processed_files.append(fc.file_path.name)
            except Exception as e:
                print(f"Error processing {fc.file_path}: {e}")
        
        if success_count > 0:
            duration = time.perf_counter() - start_time
            self.processed_offers[relative_offer_name] = {
                "last_processed": datetime.now().isoformat(),
                "duration_seconds": round(duration, 3),
                "file_count": success_count,
                "files": processed_files,
                "relative_parents": relative_parents
            }
            self._save_processed_offers()
            return True
        
        return False
    
    def _load_processed_offers(self) -> Dict[str, Any]:
        if self.processed_offers_file.exists():
            try:
                with open(self.processed_offers_file, 'r') as f:
                    data = json.load(f)
                    return data
            except Exception:
                pass
        return {}
    
    def _save_processed_offers(self):
        try:
            self.output_base_path.mkdir(parents=True, exist_ok=True)
            with open(self.processed_offers_file, 'w') as f:
                json.dump(self.processed_offers, f, indent=2)
        except Exception:
            pass

    def _relative_subdir(self, offer_name: str, file_path: Path) -> Path:
        for parent in file_path.parents:
            if parent.name == offer_name:
                return file_path.parent.relative_to(parent)
        return Path()

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

    def _save_metadata(self, output_file_dir: Path, offer_name: str, relative_parents: List[str], file_content: DocumentExtractedResponse):
        metadata_file = output_file_dir / f"{file_content.file_path.stem} - metadata.json"
        metadata_file.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "offer_name": offer_name,
            "file_name": file_content.file_path.name,
            "relative_path": str(self._relative_subdir(offer_name, file_content.file_path)),
            "file_path": str(file_content.file_path),
            "file_type": file_content.file_path.suffix,
            "extracted_at": datetime.now().isoformat(),
            "pages": len(file_content.pages),
            "pictures": len(file_content.pictures),
            "tables": len(file_content.tables),
            "relative_parents": relative_parents,
        }
        with metadata_file.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)