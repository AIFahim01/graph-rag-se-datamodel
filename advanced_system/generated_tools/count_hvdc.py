"""
Auto-generated Tool: count_hvdc
Description: Count HVDC projects
Parameters: {}
Cypher Query: MATCH (c:PageChunk) WHERE c.technology = 'HVDC' RETURN count(DISTINCT c.project_id)
"""

from neo4j import GraphDatabase
import logging

logger = logging.getLogger(__name__)


class COUNT_HVDCTool:
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
                result = session.run(
                    "MATCH (c:PageChunk) WHERE c.technology = 'HVDC' "
                    "RETURN count(DISTINCT c.project_id) as count"
                ).single()
                return f"Found {result['count']} HVDC projects"

        except Exception as e:
            logger.error(f"Tool error: {e}")
            return f"Error: {str(e)}"

    def close(self):
        if self.driver:
            self.driver.close()


def count_hvdc(**kwargs) -> str:
    """
    Count HVDC projects

    Parameters: {}
    """
    tool = COUNT_HVDCTool()
    result = tool.execute(**kwargs)
    tool.close()
    return result
