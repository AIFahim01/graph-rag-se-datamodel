"""
Display statistics about the dataset

Shows number of PDFs per project and overall statistics.
Simple flat structure - all PDFs directly in project folders.
"""

import json
from pathlib import Path
from typing import Dict, List


class DatasetStats:
    """Calculate and display dataset statistics"""

    def __init__(self, datasets_dir: Path):
        self.datasets_dir = Path(datasets_dir)
        self.projects_dir = self.datasets_dir / "projects"
        self.processed_dir = self.datasets_dir / "processed"

    def count_pdfs_in_dir(self, directory: Path) -> int:
        """Count PDF files in a directory"""
        if not directory.exists():
            return 0
        return len(list(directory.glob("*.pdf")))

    def get_project_stats(self, project_dir: Path) -> Dict:
        """Get statistics for a single project"""
        stats = {
            "name": project_dir.name,
            "total_pdfs": 0,
            "has_metadata": False,
            "has_processed": False
        }

        # Count PDFs
        stats["total_pdfs"] = self.count_pdfs_in_dir(project_dir)

        # Check for metadata
        if (project_dir / "project_info.json").exists():
            stats["has_metadata"] = True
            # Load project name from metadata
            try:
                with open(project_dir / "project_info.json", "r") as f:
                    metadata = json.load(f)
                    stats["project_name"] = metadata.get("project_name", project_dir.name)
            except:
                stats["project_name"] = project_dir.name
        else:
            stats["project_name"] = project_dir.name

        # Check if processed
        if (self.processed_dir / project_dir.name).exists():
            stats["has_processed"] = True

        return stats

    def get_all_stats(self) -> List[Dict]:
        """Get statistics for all projects"""
        if not self.projects_dir.exists():
            return []

        project_dirs = [p for p in self.projects_dir.iterdir() if p.is_dir()]
        return [self.get_project_stats(p) for p in project_dirs]

    def display_stats(self):
        """Display formatted statistics"""
        all_stats = self.get_all_stats()

        if not all_stats:
            print("❌ No projects found in datasets/projects/")
            print(f"   Create projects in: {self.projects_dir}")
            return

        print("\n" + "=" * 90)
        print(" " * 32 + "DATASET STATISTICS")
        print("=" * 90)

        # Per-project stats
        print("\nPER-PROJECT STATISTICS")
        print("─" * 90)
        print(f"{'Project Folder':<25} {'Project Name':<30} {'PDFs':<8} {'Status':<15}")
        print("─" * 90)

        total_pdfs = 0

        for stats in all_stats:
            # Format status
            status_parts = []
            if stats["has_metadata"]:
                status_parts.append("📋")
            if stats["has_processed"]:
                status_parts.append("✓")
            if stats["total_pdfs"] == 0:
                status_parts.append("⚠️ empty")
            if not status_parts:
                status_parts.append("-")
            status_str = " ".join(status_parts)

            print(f"{stats['name']:<25} {stats.get('project_name', '-'):<30} "
                  f"{stats['total_pdfs']:<8} {status_str:<15}")

            total_pdfs += stats['total_pdfs']

        print("─" * 90)

        # Overall statistics
        print("\nOVERALL STATISTICS")
        print("─" * 90)
        print(f"Total Projects:     {len(all_stats)}")
        print(f"Total PDFs:         {total_pdfs}")
        print(f"Average per Project: {total_pdfs / len(all_stats):.1f}" if all_stats else "0")

        # Projects status
        with_meta = sum(1 for s in all_stats if s["has_metadata"])
        processed = sum(1 for s in all_stats if s["has_processed"])
        empty = sum(1 for s in all_stats if s["total_pdfs"] == 0)
        with_pdfs = len(all_stats) - empty

        print(f"\nProject Status:")
        print(f"  With PDFs:          {with_pdfs}/{len(all_stats)}")
        print(f"  With metadata:      {with_meta}/{len(all_stats)}")
        print(f"  Processed:          {processed}/{len(all_stats)}")
        print(f"  Empty (no PDFs):    {empty}/{len(all_stats)}")

        print("=" * 90)

        # Recommendations
        if empty > 0:
            print("\n💡 RECOMMENDATIONS:")
            print(f"   {empty} project(s) have no PDFs. Add PDFs to:")
            for stats in all_stats:
                if stats["total_pdfs"] == 0:
                    print(f"     - datasets/projects/{stats['name']}/")

        if with_meta < len(all_stats):
            print("\n💡 TIP: Add project_info.json to projects for better tracking")

        if with_pdfs > processed:
            print(f"\n💡 NEXT STEP: Process {with_pdfs - processed} unprocessed project(s)")
            print("   Run: python scripts/process_project.py --all")

        print("\nSTATUS LEGEND: 📋 = has metadata, ✓ = processed, ⚠️ = empty\n")

    def export_json(self, output_file: Path):
        """Export statistics to JSON"""
        all_stats = self.get_all_stats()

        summary = {
            "total_projects": len(all_stats),
            "total_pdfs": sum(s['total_pdfs'] for s in all_stats),
            "projects": all_stats
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        print(f"✓ Statistics exported to: {output_file}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Display dataset statistics"
    )
    parser.add_argument(
        "--datasets-dir",
        type=str,
        default="./datasets",
        help="Path to datasets directory (default: ./datasets)"
    )
    parser.add_argument(
        "--export",
        type=str,
        help="Export statistics to JSON file"
    )

    args = parser.parse_args()

    stats = DatasetStats(args.datasets_dir)
    stats.display_stats()

    if args.export:
        stats.export_json(Path(args.export))


if __name__ == "__main__":
    main()
