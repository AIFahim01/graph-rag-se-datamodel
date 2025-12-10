#!/usr/bin/env python3
"""
Script to initialize the Agent-as-Graph schema in Neo4j.

This creates all AGENT, TOOL, and CAPABILITY nodes and their relationships.
"""

from neo4j import GraphDatabase
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "siemensenergy"


def execute_cypher_file(driver, cypher_file_path):
    """Execute statements from a Cypher file"""
    with open(cypher_file_path, 'r') as f:
        content = f.read()

    # Split by semicolon and execute each statement
    statements = [s.strip() for s in content.split(';') if s.strip()]

    # Filter out comments
    statements = [s for s in statements if not s.startswith('//')]

    with driver.session() as session:
        for i, statement in enumerate(statements, 1):
            try:
                if statement.strip():
                    logger.info(f"Executing statement {i}/{len(statements)}...")
                    result = session.run(statement)
                    # Consume the result
                    records = list(result)
                    if records:
                        logger.info(f"  Result: {records[0] if len(records) == 1 else f'{len(records)} records'}")
            except Exception as e:
                logger.error(f"Error executing statement {i}: {e}")
                logger.error(f"Statement: {statement[:100]}...")
                # Continue with next statement
                continue

    logger.info("Schema initialization complete!")


def main():
    """Initialize the agent registry schema"""
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    try:
        logger.info("Initializing Agent-as-Graph schema...")
        execute_cypher_file(driver, "init_agent_graph_schema.cypher")

        # Verify schema
        logger.info("\nVerifying schema...")
        with driver.session() as session:
            queries = {
                "Agents": "MATCH (a:AGENT) RETURN count(a) as count",
                "Tools": "MATCH (t:TOOL) RETURN count(t) as count",
                "Capabilities": "MATCH (c:CAPABILITY) RETURN count(c) as count",
                "USES relationships": "MATCH ()-[r:USES]->() RETURN count(r) as count",
                "HAS_CAPABILITY relationships": "MATCH ()-[r:HAS_CAPABILITY]->() RETURN count(r) as count",
                "REQUIRES relationships": "MATCH ()-[r:REQUIRES]->() RETURN count(r) as count",
                "DEPENDS_ON relationships": "MATCH ()-[r:DEPENDS_ON]->() RETURN count(r) as count",
            }

            for label, query in queries.items():
                result = session.run(query).single()
                count = result["count"] if result else 0
                logger.info(f"  {label}: {count}")

        logger.info("\nAgent-as-Graph schema initialized successfully!")

    except Exception as e:
        logger.error(f"Failed to initialize schema: {e}")
        raise
    finally:
        driver.close()


if __name__ == "__main__":
    main()
