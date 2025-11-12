#!/usr/bin/env python3
"""
Setup Neo4j Full-Text Indexes for Entity Pre-Retrieval
Enables fuzzy matching and fast entity search for Text-to-Cypher
"""

from neo4j import GraphDatabase

def setup_fulltext_indexes():
    """Create full-text indexes on Entity and Project nodes"""

    print("\n" + "=" * 80)
    print("SETTING UP NEO4J FULL-TEXT INDEXES")
    print("=" * 80)

    driver = GraphDatabase.driver(
        "bolt://localhost:7687",
        auth=("neo4j", "password")
    )

    with driver.session() as session:
        # Drop existing indexes if they exist
        print("\n🧹 Removing old indexes (if any)...")
        try:
            session.run("DROP INDEX entity_fulltext IF EXISTS")
            session.run("DROP INDEX project_fulltext IF EXISTS")
            print("   Dropped old indexes")
        except Exception as e:
            print(f"   No old indexes to drop")

        # Create full-text index for Entity names
        print("\n📋 Creating full-text index for Entity.name...")
        try:
            session.run("""
                CREATE FULLTEXT INDEX entity_fulltext IF NOT EXISTS
                FOR (e:Entity)
                ON EACH [e.name]
            """)
            print("   ✅ Entity full-text index created")
        except Exception as e:
            print(f"   Note: {e}")

        # Create full-text index for Project names
        print("\n📋 Creating full-text index for Project.name...")
        try:
            session.run("""
                CREATE FULLTEXT INDEX project_fulltext IF NOT EXISTS
                FOR (p:Project)
                ON EACH [p.name]
            """)
            print("   ✅ Project full-text index created")
        except Exception as e:
            print(f"   Note: {e}")

        # Test the indexes
        print("\n🧪 Testing full-text search...")

        # Test Entity search
        result = session.run("""
            CALL db.index.fulltext.queryNodes('entity_fulltext', 'HVDC~')
            YIELD node, score
            RETURN node.name as entity, score
            LIMIT 5
        """)

        print("\n   Entity search results for 'HVDC~':")
        for record in result:
            print(f"   - {record['entity']} (score: {record['score']:.3f})")

        # Test Project search
        result = session.run("""
            CALL db.index.fulltext.queryNodes('project_fulltext', 'Tennet~')
            YIELD node, score
            RETURN node.name as project, score
            LIMIT 5
        """)

        print("\n   Project search results for 'Tennet~':")
        for record in result:
            print(f"   - {record['project']} (score: {record['score']:.3f})")

        # Get index statistics
        print("\n📊 Index Statistics:")
        result = session.run("""
            SHOW INDEXES
            YIELD name, type, entityType, labelsOrTypes, properties, state
            WHERE name IN ['entity_fulltext', 'project_fulltext']
            RETURN name, type, labelsOrTypes, properties, state
        """)

        for record in result:
            print(f"\n   Index: {record['name']}")
            print(f"   Type: {record['type']}")
            print(f"   Labels: {record['labelsOrTypes']}")
            print(f"   Properties: {record['properties']}")
            print(f"   State: {record['state']}")

    driver.close()

    print("\n" + "=" * 80)
    print("✅ FULL-TEXT INDEXES SETUP COMPLETE!")
    print("=" * 80)
    print("\nNow you can use fuzzy entity search in Text-to-Cypher:")
    print("  - CALL db.index.fulltext.queryNodes('entity_fulltext', 'search~')")
    print("  - CALL db.index.fulltext.queryNodes('project_fulltext', 'search~')")
    print("\nThe '~' suffix enables fuzzy matching (handles typos)")

if __name__ == "__main__":
    setup_fulltext_indexes()
