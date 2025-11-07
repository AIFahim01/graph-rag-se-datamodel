"""
Load Knowledge Graph into Neo4j

Loads unified knowledge graph with entities and relationships.
"""

import sys
import json
from pathlib import Path
from loguru import logger

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from storage.neo4j_store import Neo4jGraphStore


def main():
    datasets_dir = PROJECT_ROOT / "datasets"
    kg_dir = datasets_dir / "knowledge_graphs"
    unified_kg_file = kg_dir / "unified_knowledge_graph.json"

    print("\n" + "=" * 80)
    print("NEO4J KNOWLEDGE GRAPH LOADER")
    print("=" * 80)

    # Load unified KG
    print("\n📦 Loading unified knowledge graph...")
    with open(unified_kg_file, 'r') as f:
        unified_kg = json.load(f)

    print(f"✓ Loaded KG:")
    print(f"  Projects: {unified_kg['num_projects']}")
    print(f"  Entities: {unified_kg['num_total_entities']}")
    print(f"  Triplets: {unified_kg['num_total_triplets']}")

    # Connect to Neo4j
    print("\n🔗 Connecting to Neo4j...")
    store = Neo4jGraphStore()

    # Clear existing data
    print("\n🗑️  Clearing existing data...")
    store.clear_database()

    # Create indexes
    print("\n📇 Creating indexes...")
    store.create_indexes()

    # Insert KG
    print(f"\n💾 Inserting knowledge graph...")
    store.insert_knowledge_graph(unified_kg)

    # Close connection
    store.close()

    print("\n" + "=" * 80)
    print("✅ Neo4j loaded successfully!")
    print("=" * 80)
    print(f"Projects: {unified_kg['num_projects']}")
    print(f"Entities: {unified_kg['num_total_entities']}")
    print(f"Relationships: {unified_kg['num_total_triplets']}")
    print("=" * 80)
    print("\n🌐 Access Neo4j Browser:")
    print("   http://localhost:7474")
    print("   User: neo4j")
    print("   Password: graphrag_password123")
    print("\n✅ Ready for graph queries!")


if __name__ == "__main__":
    main()
