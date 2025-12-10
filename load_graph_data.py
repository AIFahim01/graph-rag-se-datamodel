#!/usr/bin/env python3
"""
Load graph data (entities and relationships) into Neo4j database
"""
import json
import sys
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Neo4j connection details
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "siemensenergy")

# Paths to data files
EXPORT_DIR = "neo4j_export/export_20251207_091151"
ENTITIES_FILE = f"{EXPORT_DIR}/entities.json"
RELATIONSHIPS_FILE = f"{EXPORT_DIR}/relationships.json"


def load_entities(driver):
    """Load entities (nodes) into Neo4j"""
    print("Loading entities...")

    with open(ENTITIES_FILE, 'r') as f:
        entities = json.load(f)

    with driver.session() as session:
        # Clear existing data
        session.run("MATCH (n) DETACH DELETE n")
        print(f"Cleared existing data")

        # Load entities
        for entity in entities:
            name = entity.get('name')
            label = entity.get('label') or 'Entity'

            if name:
                query = f"""
                CREATE (n:{label} {{name: $name}})
                RETURN n
                """
                try:
                    session.run(query, name=name)
                except Exception as e:
                    # Fallback to generic Entity label if there's an issue
                    session.run("CREATE (n:Entity {name: $name}) RETURN n", name=name)

        print(f"Loaded {len(entities)} entities")


def load_relationships(driver):
    """Load relationships (edges) into Neo4j"""
    print("Loading relationships...")

    with open(RELATIONSHIPS_FILE, 'r') as f:
        relationships = json.load(f)

    with driver.session() as session:
        count = 0
        for rel in relationships:
            source = rel.get('source')
            target = rel.get('target')
            relationship_type = rel.get('type') or 'RELATED_TO'

            if source and target:
                query = f"""
                MATCH (a {{name: $source}})
                MATCH (b {{name: $target}})
                CREATE (a)-[:{relationship_type}]->(b)
                """
                try:
                    session.run(query, source=source, target=target)
                    count += 1
                except Exception as e:
                    print(f"Warning: Could not create relationship {source} -> {target}: {e}")

        print(f"Loaded {count} relationships")


def verify_data(driver):
    """Verify the loaded data"""
    print("\nVerifying data...")

    with driver.session() as session:
        # Count nodes
        result = session.run("MATCH (n) RETURN count(n) as count")
        node_count = result.single()['count']

        # Count relationships
        result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
        rel_count = result.single()['count']

        print(f"✓ Total nodes: {node_count}")
        print(f"✓ Total relationships: {rel_count}")

        # Show sample nodes
        result = session.run("MATCH (n) RETURN n.name as name LIMIT 5")
        print(f"\nSample entities:")
        for record in result:
            print(f"  - {record['name']}")


def main():
    """Main function"""
    try:
        # Connect to Neo4j
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

        # Test connection
        with driver.session() as session:
            result = session.run("RETURN 1")
            if result.single():
                print(f"✓ Connected to Neo4j at {NEO4J_URI}")

        # Load data
        load_entities(driver)
        load_relationships(driver)

        # Verify
        verify_data(driver)

        driver.close()
        print("\n✓ Data loading complete!")

    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
