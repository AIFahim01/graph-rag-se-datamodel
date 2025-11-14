from pathlib import Path
from typing import List

import logging

class FileFilter:
    def __init__(self, extensions: List[str]):
        self.supported_extensions = extensions if extensions else [".pdf"]

    def scan_folder(self, folder_path: Path) -> List[Path]:
        """Returns list of supported files in folder."""
        if not folder_path.is_dir():
            logging.error(f"Invalid folder path: '{folder_path}'.")
            return []

        exts = {ext.lower() for ext in self.supported_extensions}
        supported_files: List[Path] = []

        for item in folder_path.iterdir():
            if item.is_file() and item.suffix.lower() in exts:
                supported_files.append(item)
            elif item.is_dir() and not item.name.startswith('.'):
                supported_files.extend(self.scan_folder(item))

        return supported_files