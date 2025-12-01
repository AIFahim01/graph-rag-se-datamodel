#!/usr/bin/env python3
"""
Check Graph Data - View what's stored in Neo4j
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE
from neo4j import GraphDatabase


def check_graph_data():
    """Check what data is stored in Neo4j"""

    print("\n" + "="*80)
    print("📊 NEO4J GRAPH DATA INSPECTION")
    print("="*80 + "\n")

    # Connect to Neo4j
    if NEO4J_PASSWORD == "" or NEO4J_PASSWORD is None:
        driver = GraphDatabase.driver(NEO4J_URI, auth=None)
    else:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    with driver.session(database=NEO4J_DATABASE) as session:

        # 1. Count all nodes by type
        print("🔢 NODE COUNTS:")
        print("-" * 80)
        result = session.run("""
            MATCH (n)
            RETURN labels(n)[0] as NodeType, count(n) as Count
            ORDER BY Count DESC
        """)

        total_nodes = 0
        for record in result:
            node_type = record['NodeType']
            count = record['Count']
            total_nodes += count
            print(f"   {node_type:20s} : {count:,}")

        print(f"\n   {'TOTAL NODES':20s} : {total_nodes:,}")

        # 2. Count all relationships by type
        print("\n\n🔗 RELATIONSHIP COUNTS:")
        print("-" * 80)
        result = session.run("""
            MATCH ()-[r]->()
            RETURN type(r) as RelationType, count(r) as Count
            ORDER BY Count DESC
        """)

        total_rels = 0
        for record in result:
            rel_type = record['RelationType']
            count = record['Count']
            total_rels += count
            print(f"   {rel_type:20s} : {count:,}")

        print(f"\n   {'TOTAL RELATIONSHIPS':20s} : {total_rels:,}")

        # 3. Show all projects
        print("\n\n📁 PROJECTS IN GRAPH:")
        print("-" * 80)
        result = session.run("""
            MATCH (p:Project)
            RETURN p.id as ProjectID, p.type as ProjectType
            ORDER BY p.type, p.id
        """)

        projects = list(result)
        if projects:
            for record in projects:
                print(f"   • {record['ProjectID']} ({record['ProjectType']})")
        else:
            print("   (No projects found)")

        # 4. Show sample entities
        print("\n\n🏷️  TOP ENTITIES (by mention count):")
        print("-" * 80)
        result = session.run("""
            MATCH (e:Entity)
            RETURN e.name as EntityName, e.mention_count as Mentions
            ORDER BY e.mention_count DESC
            LIMIT 10
        """)

        entities = list(result)
        if entities:
            for record in entities:
                print(f"   • {record['EntityName']:30s} : {record['Mentions']} mentions")
        else:
            print("   (No entities found)")

        # 5. Show sample relationships
        print("\n\n🔀 SAMPLE RELATIONSHIPS:")
        print("-" * 80)
        result = session.run("""
            MATCH (s:Entity)-[r:RELATION]->(o:Entity)
            RETURN s.name as Subject, r.type as Relation, o.name as Object
            LIMIT 10
        """)

        relations = list(result)
        if relations:
            for record in relations:
                print(f"   {record['Subject']} --[{record['Relation']}]--> {record['Object']}")
        else:
            print("   (No relationships found)")

        # 6. Show chunks info
        print("\n\n📄 CHUNKS INFO:")
        print("-" * 80)
        result = session.run("""
            MATCH (c:Chunk)
            RETURN c.project_type as ProjectType, count(c) as ChunkCount
            ORDER BY ChunkCount DESC
        """)

        chunks = list(result)
        if chunks:
            for record in chunks:
                print(f"   • {record['ProjectType']:20s} : {record['ChunkCount']} chunks")
        else:
            print("   (No chunks found)")

    driver.close()

    print("\n" + "="*80)
    print("✅ Graph inspection complete!")
    print("\n💡 To explore more, visit: http://localhost:7474")
    print("   Username: neo4j")
    print("   Password: siemensenergy")
    print("="*80 + "\n")


if __name__ == "__main__":
    try:
        check_graph_data()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Make sure Neo4j is running:")
        print("   docker ps | grep neo4j")
        print("   If not running: ./setup_neo4j.sh")
