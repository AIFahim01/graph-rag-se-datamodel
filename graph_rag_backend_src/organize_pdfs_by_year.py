#!/usr/bin/env python3
"""Organize GC_2024 and GC_2025 PDFs into year-based structure"""

import shutil
from pathlib import Path

# Move GC24 HVDC projects
gc24_dirs = Path('GC_2024').glob('*')
for project in gc24_dirs:
    if not project.is_dir():
        continue

    name = project.name.upper()
    if 'HVDC' in name:
        dest = Path('data/pdfs/gc_2024/hdvc') / project.name
        print(f"Moving {project.name} → gc_2024/hdvc/")
        shutil.move(str(project), str(dest))
    elif 'SYNCON' in name:
        dest = Path('data/pdfs/gc_2024/syncon') / project.name
        print(f"Moving {project.name} → gc_2024/syncon/")
        shutil.move(str(project), str(dest))

print("\n✅ Organization complete!")
print(f"GC24 HVDC: {len(list(Path('data/pdfs/gc_2024/hdvc').glob('*')))} projects")
print(f"GC24 SynCon: {len(list(Path('data/pdfs/gc_2024/syncon').glob('*')))} projects")
print(f"GC25 HVDC: {len(list(Path('data/pdfs/gc_2025/hdvc').glob('*')))} projects")
print(f"GC25 SynCon: {len(list(Path('data/pdfs/gc_2025/syncon').glob('*')))} projects")
