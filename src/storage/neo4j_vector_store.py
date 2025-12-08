"""
Neo4j Vector Store for HVDC/SynCon Knowledge Base
Stores document chunks with embeddings and rich metadata
"""

import time
from typing import List, Dict, Optional
import numpy as np
from neo4j import GraphDatabase
from loguru import logger


class Neo4jVectorStore:
    """Neo4j vector storage with metadata support"""

    def __init__(self, uri: str = "bolt://localhost:7687", auth=None):
        """
        Initialize Neo4j vector store

        Args:
            uri: Neo4j connection URI
            auth: Authentication tuple (username, password) or None
        """
        self.driver = GraphDatabase.driver(uri, auth=auth)
        logger.info(f"Connected to Neo4j at {uri}")

    def close(self):
        """Close driver connection"""
        self.driver.close()

    def create_vector_index(self, index_name: str = "chunk_embeddings",
                           dimensions: int = 1024):
        """
        Create vector index for similarity search

        Args:
            index_name: Name of the vector index
            dimensions: Embedding dimensions (1024 for BGE-large)
        """
        with self.driver.session() as session:
            # Drop if exists
            try:
                session.run(f"DROP INDEX {index_name} IF EXISTS")
            except:
                pass

            # Create vector index
            session.run(f"""
                CREATE VECTOR INDEX {index_name}
                FOR (c:Chunk)
                ON (c.embedding)
                OPTIONS {{
                    indexConfig: {{
                        `vector.dimensions`: {dimensions},
                        `vector.similarity_function`: 'cosine'
                    }}
                }}
            """)

            logger.info(f"Created vector index: {index_name}")

            # Wait for index to be online
            max_wait = 60
            for i in range(max_wait):
                time.sleep(1)
                result = session.run(f"""
                    SHOW INDEXES
                    YIELD name, state
                    WHERE name = '{index_name}'
                    RETURN state
                """)
                record = result.single()
                if record and record['state'] == 'ONLINE':
                    logger.info(f"Vector index online (took {i+1}s)")
                    return True

            logger.warning("Vector index creation timeout")
            return False

    def create_metadata_indexes(self):
        """Create indexes on metadata fields for fast filtering"""
        with self.driver.session() as session:
            # Create indexes
            session.run("CREATE INDEX chunk_project IF NOT EXISTS FOR (c:Chunk) ON (c.project_id)")
            session.run("CREATE INDEX chunk_customer IF NOT EXISTS FOR (c:Chunk) ON (c.customer_normalized)")
            session.run("CREATE INDEX chunk_category IF NOT EXISTS FOR (c:Chunk) ON (c.category)")
            session.run("CREATE INDEX chunk_technology IF NOT EXISTS FOR (c:Chunk) ON (c.technology)")

            logger.info("Created metadata indexes")

    def store_chunk_batch(self, chunks: List[Dict], embeddings: np.ndarray):
        """
        Store batch of chunks with embeddings and metadata

        Args:
            chunks: List of chunk dictionaries with metadata
            embeddings: Numpy array of embeddings (shape: [n, 1024])
        """
        with self.driver.session() as session:
            for chunk, embedding in zip(chunks, embeddings):
                session.run("""
                    CREATE (c:Chunk {
                        chunk_id: $chunk_id,
                        text: $text,
                        embedding: $embedding,

                        project_id: $project_id,
                        project_name: $project_name,
                        project_type: $project_type,
                        customer: $customer,
                        customer_normalized: $customer_normalized,
                        category: $category,
                        technology: $technology,
                        document_type: $document_type,

                        source_file: $source_file,
                        page: $page,
                        char_count: $char_count
                    })
                """,
                    chunk_id=chunk['chunk_id'],
                    text=chunk['text'],
                    embedding=embedding.tolist(),

                    project_id=chunk.get('project_id', 'Unknown'),
                    project_name=chunk.get('project_name', 'Unknown'),
                    project_type=chunk.get('project_type', 'Unknown'),
                    customer=chunk.get('customer', 'Unknown'),
                    customer_normalized=chunk.get('customer_normalized', 'unknown'),
                    category=chunk.get('category', 'unknown'),
                    technology=chunk.get('technology', 'Unknown'),
                    document_type=chunk.get('document_type', 'other'),

                    source_file=chunk.get('source', 'Unknown'),
                    page=chunk.get('page', 0),
                    char_count=chunk.get('char_count', len(chunk.get('text', '')))
                )

        logger.info(f"Stored {len(chunks)} chunks with embeddings and metadata")

    def vector_search(self, query_embedding: np.ndarray, top_k: int = 5,
                     filters: Optional[Dict] = None) -> List[Dict]:
        """
        Perform vector similarity search with optional metadata filters

        Args:
            query_embedding: Query vector (1024-dim)
            top_k: Number of results
            filters: Optional metadata filters (e.g., {'customer': 'TenneT'})

        Returns:
            List of matching chunks with scores
        """
        with self.driver.session() as session:
            # Build WHERE clause for filters
            where_clauses = []
            if filters:
                if 'customer' in filters:
                    where_clauses.append(f"node.customer_normalized = '{filters['customer'].lower()}'")
                if 'category' in filters:
                    where_clauses.append(f"node.category = '{filters['category']}'")
                if 'project_id' in filters:
                    where_clauses.append(f"node.project_id = '{filters['project_id']}'")

            where_clause = " AND ".join(where_clauses) if where_clauses else "true"

            # Query with filters
            result = session.run(f"""
                CALL db.index.vector.queryNodes('chunk_embeddings', $top_k, $query_embedding)
                YIELD node, score
                WHERE {where_clause}
                RETURN node.chunk_id AS chunk_id,
                       node.text AS text,
                       node.project_id AS project_id,
                       node.customer AS customer,
                       node.category AS category,
                       node.source_file AS source,
                       score
                ORDER BY score DESC
                LIMIT $top_k
            """,
                query_embedding=query_embedding.tolist(),
                top_k=top_k
            )

            return [dict(record) for record in result]

    def count_projects_by_customer(self, customer: str) -> Dict:
        """
        Query: How many projects have customer X?

        Args:
            customer: Customer name (e.g., 'TenneT')

        Returns:
            {'count': 15, 'projects': ['GC25_084', ...]}
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:Chunk)
                WHERE toLower(c.customer_normalized) = toLower($customer)
                RETURN DISTINCT c.project_id AS project_id,
                       c.project_name AS project_name
                ORDER BY c.project_id
            """,
                customer=customer
            )

            projects = [(r['project_id'], r['project_name']) for r in result]

            return {
                'count': len(projects),
                'projects': [p[0] for p in projects],
                'details': projects
            }

    def clear_all_chunks(self):
        """Clear all chunk nodes (for testing/reset)"""
        with self.driver.session() as session:
            result = session.run("MATCH (c:Chunk) DETACH DELETE c RETURN count(c) AS deleted")
            deleted = result.single()['deleted']
            logger.info(f"Deleted {deleted} chunks")
            return deleted
