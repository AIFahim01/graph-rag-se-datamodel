"""
Iterative Planning Phase
Planner creates plans, Validator reviews and provides feedback
Continues until approval or max iterations
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from crewai import Crew, Process, Task

from advanced_system.agents.planner_agent import create_planner_agent
from advanced_system.agents.validator_agent import create_validator_agent
from advanced_system.phases import PhaseResult

logger = logging.getLogger(__name__)


class PlanningPhase:
    """
    Iterative planning phase with validation loop.

    Flow:
    1. Planner creates initial plan
    2. Validator reviews plan
    3. If approved → return plan
    4. If not approved → Planner revises based on feedback
    5. Repeat 2-4 until approved or max iterations
    """

    def __init__(self, max_iterations: int = 5, llm=None):
        """
        Initialize planning phase.

        Args:
            max_iterations: Maximum validation iterations
            llm: LLM instance for agents
        """
        self.max_iterations = max_iterations
        self.llm = llm
        self.iteration_history = []

    def execute(self, context: Dict[str, Any]) -> PhaseResult:
        """
        Execute iterative planning with validation.

        Args:
            context: Contains user_objective, user_data, domain_context

        Returns:
            PhaseResult with approved plan or failure
        """
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 1: ITERATIVE PLANNING WITH VALIDATION")
        logger.info("=" * 80)

        user_objective = context.get("user_objective", "")
        user_data = context.get("user_data", "")
        domain_context = context.get("domain_context", "")

        planner = create_planner_agent(self.llm)
        validator = create_validator_agent(self.llm)

        approved_plan = None

        for iteration in range(1, self.max_iterations + 1):
            logger.info(f"\n{'─' * 80}")
            logger.info(f"ITERATION {iteration}/{self.max_iterations}")
            logger.info(f"{'─' * 80}")

            try:
                # Create task for planner
                if iteration == 1:
                    plan_task = Task(
                        description=(
                            f"Create a comprehensive plan to achieve this objective:\n\n"
                            f"OBJECTIVE: {user_objective}\n\n"
                            f"DATA AVAILABLE: {user_data}\n\n"
                            f"DOMAIN CONTEXT: {domain_context}\n\n"
                            f"Provide a detailed, step-by-step plan that:\n"
                            f"- Breaks down the objective into clear phases\n"
                            f"- Identifies required tools and data\n"
                            f"- Outlines success criteria\n"
                            f"- Considers potential challenges"
                        ),
                        agent=planner,
                        expected_output="A comprehensive, numbered plan with all required details"
                    )
                else:
                    plan_task = Task(
                        description=(
                            f"Revise the plan based on this feedback:\n\n"
                            f"FEEDBACK:\n{self.iteration_history[-1]['feedback']}\n\n"
                            f"ORIGINAL OBJECTIVE: {user_objective}\n\n"
                            f"Create an improved plan that addresses all feedback points."
                        ),
                        agent=planner,
                        expected_output="An improved plan addressing all feedback"
                    )

                # Execute planning crew
                planning_crew = Crew(
                    agents=[planner],
                    tasks=[plan_task],
                    process=Process.sequential,
                    verbose=False
                )

                logger.info("Planning Agent: Creating plan...")
                plan_result = planning_crew.kickoff()
                plan_output = plan_result.raw if hasattr(plan_result, 'raw') else str(plan_result)

                # Validate the plan
                validation_task = Task(
                    description=(
                        f"Review and validate this plan:\n\n"
                        f"PLAN:\n{plan_output}\n\n"
                        f"OBJECTIVE: {user_objective}\n\n"
                        f"Provide your validation:\n"
                        f"- Are all steps clear and actionable?\n"
                        f"- Is the plan complete?\n"
                        f"- Will it achieve the objective?\n"
                        f"- Any gaps or issues?\n\n"
                        f"If the plan is fully approved, end with exactly: 'PLAN APPROVED: 100% OK'\n"
                        f"Otherwise, provide specific feedback for improvement."
                    ),
                    agent=validator,
                    expected_output="Validation feedback or approval message"
                )

                validation_crew = Crew(
                    agents=[validator],
                    tasks=[validation_task],
                    process=Process.sequential,
                    verbose=False
                )

                logger.info("Validator Agent: Reviewing plan...")
                validation_result = validation_crew.kickoff()
                validation_output = validation_result.raw if hasattr(validation_result, 'raw') else str(validation_result)

                # Check for approval
                if "PLAN APPROVED: 100% OK" in validation_output:
                    approved_plan = plan_output
                    logger.info("\n✅ PLAN APPROVED!")
                    logger.info(f"Approved after {iteration} iteration(s)")

                    self.iteration_history.append({
                        "iteration": iteration,
                        "plan": plan_output,
                        "validation": validation_output,
                        "approved": True
                    })

                    return PhaseResult(
                        success=True,
                        phase_name="planning",
                        data={
                            "final_plan": approved_plan,
                            "iterations": iteration,
                            "history": self.iteration_history
                        }
                    )

                else:
                    # Not approved, store feedback for next iteration
                    logger.info(f"\n⚠️  Plan not approved. Feedback provided.")
                    logger.info(f"Feedback:\n{validation_output[:200]}...")

                    self.iteration_history.append({
                        "iteration": iteration,
                        "plan": plan_output,
                        "feedback": validation_output,
                        "approved": False
                    })

            except Exception as e:
                logger.error(f"Error in iteration {iteration}: {str(e)}")
                return PhaseResult(
                    success=False,
                    phase_name="planning",
                    data={"iterations": iteration},
                    error=str(e)
                )

        # Max iterations reached without approval
        logger.warning(f"\n⚠️  Max iterations ({self.max_iterations}) reached without approval")
        if approved_plan is None and self.iteration_history:
            approved_plan = self.iteration_history[-1].get("plan")

        return PhaseResult(
            success=False if approved_plan is None else True,
            phase_name="planning",
            data={
                "final_plan": approved_plan,
                "iterations": self.max_iterations,
                "history": self.iteration_history,
                "note": "Max iterations reached"
            },
            error="Max iterations reached without approval" if approved_plan is None else None
        )
