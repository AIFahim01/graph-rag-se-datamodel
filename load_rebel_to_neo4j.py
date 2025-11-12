#!/usr/bin/env python3
"""
Load pre-built REBEL knowledge graph into Neo4j
"""

import sys
import json
from pathlib import Path
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from neo4j import GraphDatabase

def load_rebel_kg_to_neo4j():
    """Load REBEL knowledge graph from JSON into Neo4j"""

    print("\n" + "=" * 80)
    print("📦 LOADING REBEL KNOWLEDGE GRAPH TO NEO4J")
    print("=" * 80)

    # Load the saved knowledge graph
    kg_file = PROJECT_ROOT / "data" / "graphrag_complete" / "rebel_knowledge_graph.json"
    print(f"\n📄 Loading from: {kg_file}")

    with open(kg_file) as f:
        kg_data = json.load(f)

    print(f"✅ Loaded knowledge graph:")
    print(f"   • {len(kg_data['entities'])} entities")
    print(f"   • {len(kg_data['relationships'])} relationships")
    print(f"   • {len(kg_data['projects'])} projects")

    # Connect to Neo4j
    driver = GraphDatabase.driver(
        "bolt://localhost:7687",
        auth=("neo4j", "password")
    )

    with driver.session() as session:
        # Clear existing graph
        print("\n🧹 Clearing existing knowledge graph...")
        session.run("MATCH (n) DETACH DELETE n")

        # Create constraints
        print("📋 Creating constraints...")
        try:
            session.run("CREATE CONSTRAINT entity_name IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE")
            session.run("CREATE CONSTRAINT project_name IF NOT EXISTS FOR (p:Project) REQUIRE p.name IS UNIQUE")
        except Exception as e:
            print(f"   Note: {e}")

        # Load entities
        print(f"\n📥 Loading {len(kg_data['entities'])} entities...")
        for entity, data in tqdm(kg_data['entities'].items(), desc="Entities"):
            session.run("""
                MERGE (e:Entity {name: $name})
                SET e.mentions = $mentions,
                    e.num_projects = $num_projects
            """, name=entity, mentions=data['mentions'], num_projects=len(data['projects']))

        # Load projects
        print(f"\n📥 Loading {len(kg_data['projects'])} projects...")
        for project in tqdm(kg_data['projects'], desc="Projects"):
            session.run("""
                MERGE (p:Project {name: $name})
            """, name=project)

        # Load relationships
        print(f"\n📥 Loading {len(kg_data['relationships'])} relationships...")
        success_count = 0
        for rel in tqdm(kg_data['relationships'], desc="Relationships"):
            try:
                # Create relationship between entities
                session.run("""
                    MATCH (s:Entity {name: $subject})
                    MATCH (o:Entity {name: $object})
                    MERGE (s)-[r:RELATED {type: $relation}]->(o)
                    SET r.source = 'REBEL'
                """, subject=rel['subject'], object=rel['object'], relation=rel['relation'])

                # Connect entities to projects
                session.run("""
                    MATCH (p:Project {name: $project})
                    MATCH (e:Entity {name: $entity})
                    MERGE (p)-[:MENTIONS]->(e)
                """, project=rel['project'], entity=rel['subject'])

                session.run("""
                    MATCH (p:Project {name: $project})
                    MATCH (e:Entity {name: $entity})
                    MERGE (p)-[:MENTIONS]->(e)
                """, project=rel['project'], entity=rel['object'])

                success_count += 1
            except Exception as e:
                # Skip relationships with missing entities
                continue

    driver.close()

    print("\n✅ REBEL knowledge graph loaded to Neo4j successfully!")
    print(f"   • Loaded {success_count:,} relationships")
    print("\n" + "=" * 80)

if __name__ == "__main__":
    print("\n" + "🚀" * 40)
    print("REBEL KNOWLEDGE GRAPH LOADER")
    print("🚀" * 40 + "\n")

    load_rebel_kg_to_neo4j()

    print("\n✨ Done! Your GraphRAG system now uses REBEL-extracted knowledge graph!")
    print("\nTest it with:")
    print("  python ollama_graphrag_chat.py --interactive --model mistral")
    print("  python true_graphrag_chat.py --interactive")
