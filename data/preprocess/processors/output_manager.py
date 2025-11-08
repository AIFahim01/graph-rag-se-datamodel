import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

class OutputManager:
    def __init__(self, output_base_path: Path):
        self.output_base_path = Path(output_base_path)
        self.processed_offers_file = self.output_base_path / "processed_offers.json"
        self.processed_offers = self._load_processed_offers()
    
    def is_offer_processed(self, offer_name: str) -> bool:
        return offer_name in self.processed_offers
    
    def save_offer_documents(self, offer_name: str, start_time: float, files_content: List[tuple[Path, str, bool]]) -> bool:
        """Save documents for an offer. Returns success status."""
        offer_folder = self._create_offer_structure(offer_name)
        
        success_count = 0
        processed_files: List[str] = []

        for file_path, content, success in files_content:
            if success and content:
                output_file = offer_folder / f"{file_path.stem}.md"
                try:
                    output_file.write_text(content, encoding='utf-8')
                    success_count += 1
                    processed_files.append(file_path.name)
                except Exception:
                    pass
        
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
    
    def _create_offer_structure(self, offer_name: str) -> Path:
        offer_folder = self.output_base_path / offer_name
        offer_folder.mkdir(parents=True, exist_ok=True)
        return offer_folder
    
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