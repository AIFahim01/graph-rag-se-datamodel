"""
Neo4j Knowledge Graph Loader
"""

import json
from pathlib import Path
from typing import Dict
from neo4j import GraphDatabase
from tqdm import tqdm


class Neo4jLoader:
    """Load knowledge graph into Neo4j"""

    def __init__(self, uri: str, user: str, password: str, database: str = "neo4j"):
        """
        Initialize Neo4j connection

        Args:
            uri: Neo4j URI (e.g., bolt://localhost:7687)
            user: Username
            password: Password
            database: Database name
        """
        print(f"🔌 Connecting to Neo4j...")
        print(f"   URI: {uri}")

        try:
            # Handle auth - if password is empty/None, try without auth
            if password == "" or password is None:
                self.driver = GraphDatabase.driver(uri, auth=None)
            else:
                self.driver = GraphDatabase.driver(uri, auth=(user, password))
            self.database = database

            # Test connection
            with self.driver.session(database=database) as session:
                result = session.run("RETURN 1 as test")
                result.single()

            print(f"✅ Connected to Neo4j successfully!")

        except Exception as e:
            print(f"❌ Failed to connect to Neo4j: {e}")
            print(f"   Make sure Neo4j is running: docker ps | grep neo4j")
            raise

    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()

    def clear_graph(self):
        """Clear all nodes and relationships"""
        print(f"\n🧹 Clearing existing graph data...")

        with self.driver.session(database=self.database) as session:
            # Delete all nodes and relationships
            session.run("MATCH (n) DETACH DELETE n")

        print(f"✅ Graph cleared!")

    def create_indexes(self):
        """Create indexes for better performance"""
        print(f"\n📑 Creating indexes...")

        with self.driver.session(database=self.database) as session:
            # Index on entity name
            session.run("""
                CREATE INDEX entity_name_index IF NOT EXISTS
                FOR (e:Entity) ON (e.name)
            """)

            # Index on chunk ID
            session.run("""
                CREATE INDEX chunk_id_index IF NOT EXISTS
                FOR (c:Chunk) ON (c.chunk_id)
            """)

            # Index on project type
            session.run("""
                CREATE INDEX project_type_index IF NOT EXISTS
                FOR (p:Project) ON (p.type)
            """)

        print(f"✅ Indexes created!")

    def load_knowledge_graph(self, kg: Dict):
        """
        Load knowledge graph into Neo4j

        Args:
            kg: Knowledge graph dictionary
        """
        print(f"\n📥 Loading knowledge graph to Neo4j...")

        extraction_results = kg['extraction_results']
        entity_index = kg['entity_index']

        with self.driver.session(database=self.database) as session:
            # Create project nodes
            print(f"\n📁 Creating project nodes...")
            projects = set()
            for result in extraction_results:
                project_type = result.get('project_type', 'unknown')
                project_id = result.get('project_id', 'unknown')
                projects.add((project_id, project_type))

            for project_id, project_type in tqdm(projects, desc="Projects"):
                session.run("""
                    MERGE (p:Project {id: $project_id})
                    SET p.type = $project_type
                """, project_id=project_id, project_type=project_type)

            # Create chunk nodes
            print(f"\n📄 Creating chunk nodes...")
            for result in tqdm(extraction_results, desc="Chunks"):
                session.run("""
                    CREATE (c:Chunk {
                        chunk_id: $chunk_id,
                        project_id: $project_id,
                        project_type: $project_type,
                        text_length: $text_length,
                        entity_count: $entity_count,
                        relation_count: $relation_count
                    })
                """,
                    chunk_id=result['chunk_id'],
                    project_id=result.get('project_id', 'unknown'),
                    project_type=result.get('project_type', 'unknown'),
                    text_length=result.get('text_length', 0),
                    entity_count=len(result['entities']),
                    relation_count=len(result['relations'])
                )

            # Create entity nodes
            print(f"\n🏷️  Creating entity nodes...")
            for entity_text, chunk_ids in tqdm(entity_index.items(), desc="Entities"):
                session.run("""
                    MERGE (e:Entity {name: $name})
                    SET e.mention_count = $mention_count,
                        e.chunk_ids = $chunk_ids
                """,
                    name=entity_text,
                    mention_count=len(chunk_ids),
                    chunk_ids=chunk_ids
                )

            # Create relationships
            print(f"\n🔗 Creating relationships...")
            relation_count = 0
            for result in tqdm(extraction_results, desc="Relations"):
                chunk_id = result['chunk_id']
                project_id = result.get('project_id', 'unknown')

                for relation in result['relations']:
                    session.run("""
                        MATCH (s:Entity {name: $subject})
                        MATCH (o:Entity {name: $object})
                        MATCH (c:Chunk {chunk_id: $chunk_id})
                        CREATE (s)-[r:RELATION {
                            type: $relation_type,
                            chunk_id: $chunk_id,
                            project_id: $project_id,
                            confidence: $confidence
                        }]->(o)
                        CREATE (c)-[:MENTIONS]->(s)
                        CREATE (c)-[:MENTIONS]->(o)
                    """,
                        subject=relation['subject'],
                        object=relation['object'],
                        relation_type=relation['relation'],
                        chunk_id=chunk_id,
                        project_id=project_id,
                        confidence=relation.get('confidence', 1.0)
                    )
                    relation_count += 1

        print(f"\n✅ Knowledge graph loaded successfully!")
        print(f"   Projects: {len(projects)}")
        print(f"   Chunks: {len(extraction_results)}")
        print(f"   Entities: {len(entity_index)}")
        print(f"   Relations: {relation_count}")

    def get_statistics(self) -> Dict:
        """Get graph statistics"""
        with self.driver.session(database=self.database) as session:
            # Count nodes
            result = session.run("MATCH (n) RETURN labels(n)[0] as label, count(*) as count")
            node_counts = {record['label']: record['count'] for record in result}

            # Count relationships
            result = session.run("MATCH ()-[r]->() RETURN type(r) as type, count(*) as count")
            rel_counts = {record['type']: record['count'] for record in result}

            return {
                'nodes': node_counts,
                'relationships': rel_counts
            }


def main():
    """Test the loader"""
    from config import (KNOWLEDGE_GRAPH_FILE, NEO4J_URI, NEO4J_USER,
                       NEO4J_PASSWORD, NEO4J_DATABASE)

    # Load knowledge graph
    print(f"📄 Loading knowledge graph from: {KNOWLEDGE_GRAPH_FILE}")
    with open(KNOWLEDGE_GRAPH_FILE, 'r') as f:
        kg = json.load(f)

    # Load to Neo4j
    loader = Neo4jLoader(
        uri=NEO4J_URI,
        user=NEO4J_USER,
        password=NEO4J_PASSWORD,
        database=NEO4J_DATABASE
    )

    loader.clear_graph()
    loader.create_indexes()
    loader.load_knowledge_graph(kg)

    # Print statistics
    stats = loader.get_statistics()
    print(f"\n📊 Graph Statistics:")
    print(f"   Nodes: {stats['nodes']}")
    print(f"   Relationships: {stats['relationships']}")

    loader.close()


if __name__ == "__main__":
    main()
