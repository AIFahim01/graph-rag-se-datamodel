import json
from pathlib import Path
from typing import List, Set

class OutputManager:
    def __init__(self, output_base_path: Path):
        self.output_base_path = Path(output_base_path)
        self.processed_offers_file = self.output_base_path / "processed_offers.json"
        self.processed_offers = self._load_processed_offers()
    
    def is_offer_processed(self, offer_name: str) -> bool:
        return offer_name in self.processed_offers
    
    def save_offer_documents(self, offer_name: str, files_content: List[tuple[Path, str, bool]]) -> bool:
        """Save documents for an offer. Returns success status."""
        offer_folder = self._create_offer_structure(offer_name)
        
        success_count = 0
        for file_path, content, success in files_content:
            if success and content:
                output_file = offer_folder / f"{file_path.stem}.md"
                try:
                    output_file.write_text(content, encoding='utf-8')
                    success_count += 1
                except Exception:
                    pass
        
        if success_count > 0:
            self.processed_offers.add(offer_name)
            self._save_processed_offers()
            return True
        
        return False
    
    def _create_offer_structure(self, offer_name: str) -> Path:
        offer_folder = self.output_base_path / offer_name
        offer_folder.mkdir(parents=True, exist_ok=True)
        return offer_folder
    
    def _load_processed_offers(self) -> Set[str]:
        if self.processed_offers_file.exists():
            try:
                with open(self.processed_offers_file, 'r') as f:
                    return set(json.load(f))
            except Exception:
                pass
        return set()
    
    def _save_processed_offers(self):
        try:
            self.output_base_path.mkdir(parents=True, exist_ok=True)
            with open(self.processed_offers_file, 'w') as f:
                json.dump(list(self.processed_offers), f)
        except Exception:
            pass