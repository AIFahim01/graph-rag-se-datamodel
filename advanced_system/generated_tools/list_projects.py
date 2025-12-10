"""
Auto-generated Tool: list_projects
Description: List all projects
Parameters: {}
Cypher Query: MATCH (c:PageChunk) RETURN DISTINCT c.project_name LIMIT 100
"""

from neo4j import GraphDatabase
import logging

logger = logging.getLogger(__name__)


class LIST_PROJECTSTool:
    """Auto-generated tool class"""

    def __init__(self,
                 neo4j_uri: str = "bolt://localhost:7687",
                 neo4j_user: str = "neo4j",
                 neo4j_password: str = "siemensenergy"):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

    def execute(self, **kwargs) -> str:
        """Execute the tool"""
        try:

            with self.driver.session() as session:
                results = list(session.run(
                    "MATCH (c:PageChunk) RETURN DISTINCT c.project_name as name LIMIT 100"
                ))
                return f"Found {len(results)} projects"

        except Exception as e:
            logger.error(f"Tool error: {e}")
            return f"Error: {str(e)}"

    def close(self):
        if self.driver:
            self.driver.close()


def list_projects(**kwargs) -> str:
    """
    List all projects

    Parameters: {}
    """
    tool = LIST_PROJECTSTool()
    result = tool.execute(**kwargs)
    tool.close()
    return result
