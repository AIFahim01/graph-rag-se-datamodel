import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from .document_processor import DocumentExtractedResponse

class OutputManager:
    def __init__(self, output_base_path: Path):
        self.output_base_path = Path(output_base_path)
        self.processed_offers_file = self.output_base_path / "processed_offers.json"
        self.processed_offers = self._load_processed_offers()
    
    def is_offer_processed(self, offer_name: str) -> bool:
        return offer_name in self.processed_offers
    
    def save_offer_documents(self, offer_name: str, start_time: float, files_contents: List[DocumentExtractedResponse]) -> bool:
        """Save documents for an offer. Returns success status."""
        offer_folder = self.output_base_path / offer_name
        offer_folder.mkdir(parents=True, exist_ok=True)
        
        success_count = 0
        processed_files: List[str] = []

        for fc in files_contents:
            if not (fc.success and fc.content):
                continue

            subdir = self._relative_subdir(offer_name, fc.file_path)
            output_file_dir = offer_folder / subdir / f"{fc.file_path.stem}"
            output_full_file = output_file_dir / f"{fc.file_path.stem}-full.md"
            output_full_file.parent.mkdir(parents=True, exist_ok=True)
            output_full_file.write_text(fc.content, encoding='utf-8')

            idx = 1
            for page in fc.pages:
                output_page_file = output_file_dir / f"{fc.file_path.stem} - page {idx}.md"
                output_page_file.parent.mkdir(parents=True, exist_ok=True)
                output_page_file.write_text(page, encoding='utf-8')
                idx += 1

            idx = 1
            for pil_image in fc.images:
                output_image_file = output_file_dir / "images" / f"{fc.file_path.stem} - image {idx}.png"
                output_image_file.parent.mkdir(parents=True, exist_ok=True)
                with output_image_file.open("wb") as fp:
                    pil_image.save(fp, format="PNG")
                idx += 1

            idx = 1
            for pil_table in fc.tables:
                output_table_file = output_file_dir / "tables" / f"{fc.file_path.stem} - table {idx}.png"
                output_table_file.parent.mkdir(parents=True, exist_ok=True)
                with output_table_file.open("wb") as fp:
                    pil_table.save(fp, format="PNG")
                idx += 1
            
            success_count += 1
            processed_files.append(fc.file_path.name)
        
        if success_count > 0:
            duration = time.perf_counter() - start_time
            self.processed_offers[offer_name] = {
                "last_processed": datetime.now().isoformat(),
                "duration_seconds": round(duration, 3),
                "file_count": success_count,
                "files": processed_files,
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