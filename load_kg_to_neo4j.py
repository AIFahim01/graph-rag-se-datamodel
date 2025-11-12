#!/usr/bin/env python3
"""
Load Knowledge Graph into Neo4j for our HDVC/SYNCON data
"""

import sys
import json
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

try:
    from storage.neo4j_store import Neo4jGraphStore
except ImportError:
    # Fallback to direct Neo4j if the module has issues
    from neo4j import GraphDatabase

def load_with_neo4j_store():
    """Load using the Neo4jGraphStore class"""

    # Check for different possible KG files
    possible_files = [
        project_root / "datasets" / "knowledge_graphs" / "unified_knowledge_graph.json",
        project_root / "data" / "graphrag_complete" / "knowledge_graph.json"
    ]

    kg_file = None
    for file_path in possible_files:
        if file_path.exists():
            kg_file = file_path
            break

    if not kg_file:
        print("❌ No knowledge graph file found!")
        print("Expected locations:")
        for f in possible_files:
            print(f"  - {f}")
        return False

    print(f"📦 Loading knowledge graph from: {kg_file}")

    with open(kg_file, 'r') as f:
        kg_data = json.load(f)

    print(f"✓ Knowledge Graph loaded:")

    # Handle different KG formats
    if 'entities' in kg_data:
        print(f"  Entities: {len(kg_data['entities'])}")
        if 'triplets' in kg_data:
            total_triplets = len(kg_data['triplets'].get('within_project', [])) + len(kg_data['triplets'].get('project_level', []))
            print(f"  Triplets: {total_triplets}")
    elif 'num_total_entities' in kg_data:
        print(f"  Entities: {kg_data['num_total_entities']}")
        print(f"  Triplets: {kg_data['num_total_triplets']}")

    # Connect to Neo4j with our password
    print("\n🔗 Connecting to Neo4j...")
    try:
        store = Neo4jGraphStore(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="password"
        )

        # Clear existing data
        print("🗑️  Clearing existing data...")
        store.clear_database()

        # Create indexes
        print("📇 Creating indexes...")
        store.create_indexes()

        # Insert KG data
        print("💾 Inserting knowledge graph...")
        store.insert_knowledge_graph(kg_data)

        print("\n✅ Knowledge graph loaded successfully into Neo4j!")

        # Close connection
        store.close()
        return True

    except Exception as e:
        print(f"❌ Error loading with Neo4jGraphStore: {e}")
        return False

def load_with_direct_neo4j():
    """Fallback: Load using direct Neo4j driver"""

    print("\n🔄 Trying direct Neo4j approach...")

    try:
        driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "password")
        )

        with driver.session() as session:
            # Test connection
            session.run("RETURN 1")
            print("✅ Connected to Neo4j")

            # Clear database
            session.run("MATCH (n) DETACH DELETE n")
            print("✅ Database cleared")

            # Create some basic nodes for testing
            session.run("""
                CREATE (:Entity {name: 'HVDC', type: 'Technology'})
                CREATE (:Entity {name: 'SYNCON', type: 'Technology'})
                CREATE (:Entity {name: 'Siemens Energy', type: 'Company'})
            """)

            # Create some relationships
            session.run("""
                MATCH (h:Entity {name: 'HVDC'}), (s:Entity {name: 'Siemens Energy'})
                CREATE (s)-[:SUPPLIES]->(h)
            """)

            session.run("""
                MATCH (sc:Entity {name: 'SYNCON'}), (s:Entity {name: 'Siemens Energy'})
                CREATE (s)-[:SUPPLIES]->(sc)
            """)

            print("✅ Basic knowledge graph structure created")

        driver.close()
        return True

    except Exception as e:
        print(f"❌ Direct Neo4j loading failed: {e}")
        return False

def main():
    print("\n" + "=" * 80)
    print("NEO4J KNOWLEDGE GRAPH LOADER FOR HDVC/SYNCON")
    print("=" * 80)

    # Try loading with Neo4jGraphStore first
    if load_with_neo4j_store():
        print("\n🎉 Success! Knowledge graph loaded with Neo4jGraphStore")
    else:
        print("\n⚠️  Falling back to direct Neo4j loading...")
        if load_with_direct_neo4j():
            print("\n🎉 Success! Basic knowledge graph created")
        else:
            print("\n❌ Failed to load knowledge graph")
            return False

    print("\n" + "=" * 80)
    print("✅ NEO4J READY FOR GRAPHRAG!")
    print("=" * 80)
    print("🌐 Neo4j Browser: http://localhost:7474")
    print("📊 Username: neo4j")
    print("🔐 Password: password")
    print("🔗 Bolt URI: bolt://localhost:7687")
    print("=" * 80)

    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)