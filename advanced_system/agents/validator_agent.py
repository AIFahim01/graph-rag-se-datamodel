"""
Validator Agent - Reviews and validates plans and implementations
Provides iterative feedback for refinement
"""

from crewai import Agent
import logging

logger = logging.getLogger(__name__)


def create_validator_agent(llm=None):
    """
    Create a Quality Validator agent for reviewing and validating work.

    This agent reviews:
    - Plans from the planner (provides feedback for revision)
    - Implementations from the coder (approves or requests changes)

    Approval criteria uses clear markers:
    - "PLAN APPROVED: 100% OK" for plan approval
    - "IMPLEMENTATION APPROVED: 100% OK" for implementation approval

    Args:
        llm: Optional LLM instance (uses default if not provided)

    Returns:
        Agent: Configured validator agent
    """
    return Agent(
        role="Quality Reviewer & Validator",
        goal=(
            "Thoroughly validate plans and implementations to ensure they meet all "
            "requirements and will achieve the stated objectives. Provide constructive "
            "feedback for improvements."
        ),
        backstory=(
            "You are an expert quality reviewer with meticulous attention to detail. "
            "You carefully assess whether plans are comprehensive and implementable, "
            "and whether code implementations correctly execute the approved plans. "
            "You provide clear, actionable feedback for improvement. You only approve "
            "work when fully confident it will succeed. "
            "When reviewing unreadable files, use available tools to read them."
        ),
        verbose=False,
        llm=llm
    )
