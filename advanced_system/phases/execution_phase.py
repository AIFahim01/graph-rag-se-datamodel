"""
Iterative Execution & Review Phase
Coder implements plan, Validator reviews execution
Continues until approval or max iterations
"""

import logging
from typing import Dict, Any
from datetime import datetime
from crewai import Crew, Process, Task

from advanced_system.agents.coder_agent import create_coder_agent
from advanced_system.agents.validator_agent import create_validator_agent
from advanced_system.tools import OpenInterpreterTool
from advanced_system.phases import PhaseResult

logger = logging.getLogger(__name__)


class ExecutionPhase:
    """
    Iterative execution phase with validation loop.

    Flow:
    1. Coder implements approved plan
    2. Validator reviews implementation
    3. If approved → return implementation result
    4. If not approved → Coder revises based on feedback
    5. Repeat 2-4 until approved or max iterations
    """

    def __init__(self, max_iterations: int = 5, llm=None):
        """
        Initialize execution phase.

        Args:
            max_iterations: Maximum revision iterations
            llm: LLM instance for agents
        """
        self.max_iterations = max_iterations
        self.llm = llm
        self.iteration_history = []
        self.open_interpreter = OpenInterpreterTool()

    def execute(self, context: Dict[str, Any]) -> PhaseResult:
        """
        Execute iterative implementation with validation.

        Args:
            context: Contains approved_plan, user_objective, user_data, domain_context

        Returns:
            PhaseResult with final implementation or failure
        """
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 2: ITERATIVE EXECUTION WITH VALIDATION")
        logger.info("=" * 80)

        approved_plan = context.get("approved_plan", "")
        user_objective = context.get("user_objective", "")
        user_data = context.get("user_data", "")
        domain_context = context.get("domain_context", "")

        coder = create_coder_agent(self.llm)
        validator = create_validator_agent(self.llm)

        # Add tools to agents
        coder.tools = [self.open_interpreter]

        final_implementation = None

        for iteration in range(1, self.max_iterations + 1):
            logger.info(f"\n{'─' * 80}")
            logger.info(f"ITERATION {iteration}/{self.max_iterations}")
            logger.info(f"{'─' * 80}")

            try:
                # Create task for coder
                if iteration == 1:
                    implementation_task = Task(
                        description=(
                            f"Implement this approved plan:\n\n"
                            f"APPROVED PLAN:\n{approved_plan}\n\n"
                            f"OBJECTIVE: {user_objective}\n\n"
                            f"DATA/RESOURCES: {user_data}\n\n"
                            f"DOMAIN CONTEXT: {domain_context}\n\n"
                            f"Execute the plan step-by-step, using available tools as needed.\n"
                            f"Document your progress and results."
                        ),
                        agent=coder,
                        expected_output="Complete implementation with results and documentation"
                    )
                else:
                    implementation_task = Task(
                        description=(
                            f"Revise the implementation based on this feedback:\n\n"
                            f"FEEDBACK:\n{self.iteration_history[-1]['feedback']}\n\n"
                            f"APPROVED PLAN:\n{approved_plan}\n\n"
                            f"OBJECTIVE: {user_objective}\n\n"
                            f"Create an improved implementation that addresses all feedback."
                        ),
                        agent=coder,
                        expected_output="Improved implementation addressing all feedback"
                    )

                # Execute implementation crew
                execution_crew = Crew(
                    agents=[coder],
                    tasks=[implementation_task],
                    process=Process.sequential,
                    verbose=False
                )

                logger.info("Coder Agent: Implementing plan...")
                execution_result = execution_crew.kickoff()
                execution_output = execution_result.raw if hasattr(execution_result, 'raw') else str(execution_result)

                # Validate the implementation
                validation_task = Task(
                    description=(
                        f"Review and validate this implementation:\n\n"
                        f"IMPLEMENTATION:\n{execution_output}\n\n"
                        f"APPROVED PLAN:\n{approved_plan}\n\n"
                        f"OBJECTIVE: {user_objective}\n\n"
                        f"Validate:\n"
                        f"- Does it correctly implement the plan?\n"
                        f"- Are all steps completed?\n"
                        f"- Are results documented?\n"
                        f"- Any errors or issues?\n\n"
                        f"If the implementation is fully approved, end with exactly: "
                        f"'IMPLEMENTATION APPROVED: 100% OK'\n"
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

                logger.info("Validator Agent: Reviewing implementation...")
                validation_result = validation_crew.kickoff()
                validation_output = validation_result.raw if hasattr(validation_result, 'raw') else str(validation_result)

                # Check for approval
                if "IMPLEMENTATION APPROVED: 100% OK" in validation_output:
                    final_implementation = execution_output
                    logger.info("\n✅ IMPLEMENTATION APPROVED!")
                    logger.info(f"Approved after {iteration} iteration(s)")

                    self.iteration_history.append({
                        "iteration": iteration,
                        "implementation": execution_output,
                        "validation": validation_output,
                        "approved": True
                    })

                    return PhaseResult(
                        success=True,
                        phase_name="execution",
                        data={
                            "final_implementation": final_implementation,
                            "iterations": iteration,
                            "history": self.iteration_history
                        }
                    )

                else:
                    # Not approved, store feedback for next iteration
                    logger.info(f"\n⚠️  Implementation not approved. Feedback provided.")
                    logger.info(f"Feedback:\n{validation_output[:200]}...")

                    self.iteration_history.append({
                        "iteration": iteration,
                        "implementation": execution_output,
                        "feedback": validation_output,
                        "approved": False
                    })

            except Exception as e:
                logger.error(f"Error in iteration {iteration}: {str(e)}")
                return PhaseResult(
                    success=False,
                    phase_name="execution",
                    data={"iterations": iteration},
                    error=str(e)
                )

        # Max iterations reached without approval
        logger.warning(f"\n⚠️  Max iterations ({self.max_iterations}) reached without approval")
        if final_implementation is None and self.iteration_history:
            final_implementation = self.iteration_history[-1].get("implementation")

        return PhaseResult(
            success=False if final_implementation is None else True,
            phase_name="execution",
            data={
                "final_implementation": final_implementation,
                "iterations": self.max_iterations,
                "history": self.iteration_history,
                "note": "Max iterations reached"
            },
            error="Max iterations reached without approval" if final_implementation is None else None
        )
