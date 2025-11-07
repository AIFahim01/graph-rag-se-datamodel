"""
Neo4j Graph Storage

Stores knowledge graph entities and relationships in Neo4j.
"""

import os
from typing import List, Dict
from loguru import logger
from neo4j import GraphDatabase


class Neo4jGraphStore:
    """Neo4j storage for knowledge graphs"""

    def __init__(self, uri: str = None, user: str = None, password: str = None):
        """
        Initialize Neo4j connection

        Args:
            uri: Neo4j URI (from .env if None)
            user: Neo4j username (from .env if None)
            password: Neo4j password (from .env if None)
        """
        self.uri = uri or os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        self.user = user or os.getenv('NEO4J_USER', 'neo4j')
        self.password = password or os.getenv('NEO4J_PASSWORD', 'neo4j')

        logger.info(f"Connecting to Neo4j at {self.uri}")

        # Connect with or without auth
        if self.user and self.password:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
        else:
            self.driver = GraphDatabase.driver(self.uri)

        # Test connection
        self.driver.verify_connectivity()
        logger.info("✓ Connected to Neo4j")

    def close(self):
        """Close driver connection"""
        if self.driver:
            self.driver.close()

    def clear_database(self):
        """Clear all nodes and relationships"""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            logger.info("✓ Database cleared")

    def create_indexes(self):
        """Create indexes for better query performance"""
        with self.driver.session() as session:
            # Entity name index
            session.run(
                "CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.name)"
            )
            # Project name index
            session.run(
                "CREATE INDEX project_name IF NOT EXISTS FOR (p:Project) ON (p.name)"
            )
            # Chunk ID index
            session.run(
                "CREATE INDEX chunk_id IF NOT EXISTS FOR (c:Chunk) ON (c.chunk_id)"
            )
            logger.info("✓ Indexes created")

    def insert_knowledge_graph(self, unified_kg: Dict):
        """
        Insert unified knowledge graph into Neo4j

        Args:
            unified_kg: Unified KG data from JSON
        """
        with self.driver.session() as session:
            # Insert projects
            for project_name in unified_kg['project_names']:
                session.run(
                    """
                    MERGE (p:Project {name: $name})
                    SET p.num_entities = $num_entities
                    """,
                    name=project_name,
                    num_entities=len([
                        e for e, d in unified_kg['entities'].items()
                        if project_name in d['projects']
                    ])
                )

            logger.info(f"✓ Inserted {len(unified_kg['project_names'])} projects")

            # Insert entities
            for entity_name, entity_data in unified_kg['entities'].items():
                is_cross_project = entity_data['project_count'] > 1

                session.run(
                    """
                    MERGE (e:Entity {name: $name})
                    SET e.project_count = $project_count,
                        e.total_mentions = $total_mentions,
                        e.is_cross_project = $is_cross_project,
                        e.projects = $projects
                    """,
                    name=entity_name,
                    project_count=entity_data['project_count'],
                    total_mentions=entity_data['total_mentions'],
                    is_cross_project=is_cross_project,
                    projects=entity_data['projects']
                )

            logger.info(f"✓ Inserted {len(unified_kg['entities'])} entities")

            # Insert within-project triplets
            for triplet in unified_kg['triplets']['within_project']:
                session.run(
                    """
                    MATCH (h:Entity {name: $head})
                    MATCH (t:Entity {name: $tail})
                    MERGE (h)-[r:RELATES {type: $relation}]->(t)
                    SET r.project = $project
                    """,
                    head=triplet['head'],
                    tail=triplet['tail'],
                    relation=triplet['relation'],
                    project=triplet['project']
                )

            logger.info(f"✓ Inserted {len(unified_kg['triplets']['within_project'])} relationships")

            # Insert project-entity connections
            for triplet in unified_kg['triplets']['project_level']:
                if triplet['type'] == 'project_to_entity':
                    session.run(
                        """
                        MATCH (p:Project {name: $project})
                        MATCH (e:Entity {name: $entity})
                        MERGE (p)-[r:MENTIONS]->(e)
                        """,
                        project=triplet['head'],
                        entity=triplet['tail']
                    )

            logger.info(f"✓ Inserted project-entity connections")

    def query_entity_neighbors(self, entity_name: str, max_hops: int = 2) -> List[Dict]:
        """
        Get neighbors of an entity within N hops
        Supports both exact and partial matching.

        Args:
            entity_name: Entity to start from
            max_hops: Maximum number of hops

        Returns:
            List of related entities with paths
        """
        with self.driver.session() as session:
            # Try exact match first
            result = session.run(
                """
                MATCH path = (start:Entity {name: $entity})-[*1..""" + str(max_hops) + """]->(end:Entity)
                RETURN DISTINCT end.name as entity, length(path) as distance
                ORDER BY distance
                LIMIT 20
                """,
                entity=entity_name
            )

            neighbors = [{'entity': record['entity'], 'distance': record['distance']}
                        for record in result]

            # If no exact match, try partial match (contains)
            if not neighbors and len(entity_name) > 3:
                result = session.run(
                    """
                    MATCH path = (start:Entity)-[*1..""" + str(max_hops) + """]->(end:Entity)
                    WHERE start.name CONTAINS $entity OR $entity CONTAINS start.name
                    RETURN DISTINCT end.name as entity, length(path) as distance
                    ORDER BY distance
                    LIMIT 20
                    """,
                    entity=entity_name
                )

                neighbors = [{'entity': record['entity'], 'distance': record['distance']}
                            for record in result]

            logger.info(f"Found {len(neighbors)} neighbors for '{entity_name}'")
            return neighbors

    def find_path_between_entities(self, entity1: str, entity2: str) -> List[Dict]:
        """Find shortest path between two entities"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH path = shortestPath((e1:Entity {name: $entity1})-[*]-(e2:Entity {name: $entity2}))
                RETURN [node in nodes(path) | node.name] as path_nodes,
                       [rel in relationships(path) | type(rel)] as path_relations
                """,
                entity1=entity1,
                entity2=entity2
            )

            paths = [dict(record) for record in result]
            return paths
