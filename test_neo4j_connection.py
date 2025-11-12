#!/usr/bin/env python3
"""
Test Neo4j connection
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

try:
    import neo4j
    from neo4j import GraphDatabase

    # Test basic Neo4j connection
    print("🧪 Testing Neo4j connection...")

    driver = GraphDatabase.driver(
        "bolt://localhost:7687",
        auth=("neo4j", "password")
    )

    # Test connectivity
    driver.verify_connectivity()

    # Test a simple query
    with driver.session() as session:
        result = session.run("RETURN 'Hello Neo4j!' as message")
        record = result.single()
        print(f"✅ {record['message']}")

    # Check database stats
    with driver.session() as session:
        result = session.run("CALL dbms.components() YIELD name, versions")
        for record in result:
            print(f"   {record['name']}: {record['versions'][0]}")

    driver.close()
    print("✅ Neo4j connection test successful!")

except Exception as e:
    print(f"❌ Neo4j connection failed: {e}")
    print("\nTroubleshooting:")
    print("1. Make sure Neo4j container is running: docker ps | grep neo4j")
    print("2. Check Neo4j logs: docker logs neo4j-graphrag")
    print("3. Wait a few more seconds for Neo4j to fully start")