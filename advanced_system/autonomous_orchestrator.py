"""
Autonomous Orchestrator
Coordinates full autonomy pipeline with iterative planning and execution
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from crewai import LLM

from advanced_system.phases.planning_phase import PlanningPhase
from advanced_system.phases.execution_phase import ExecutionPhase

logger = logging.getLogger(__name__)


class AutonomousOrchestrator:
    """
    Full autonomy orchestrator with iterative planning and execution.

    Pipeline Flow:
    1. PLANNING PHASE (Iterative)
       - Planner creates initial plan
       - Validator reviews and provides feedback
       - Repeat until plan is approved

    2. EXECUTION PHASE (Iterative)
       - Coder implements approved plan
       - Validator reviews implementation
       - Repeat until implementation is approved

    Both phases have approval-based loops for full autonomy.
    """

    def __init__(
        self,
        max_planning_iterations: int = 5,
        max_execution_iterations: int = 5,
        llm: Optional[LLM] = None
    ):
        """
        Initialize autonomous orchestrator.

        Args:
            max_planning_iterations: Max iterations for plan validation
            max_execution_iterations: Max iterations for implementation validation
            llm: LLM instance for agents (uses default if not provided)
        """
        self.max_planning_iterations = max_planning_iterations
        self.max_execution_iterations = max_execution_iterations
        self.llm = llm

        # Initialize phases
        self.planning_phase = PlanningPhase(max_planning_iterations, llm)
        self.execution_phase = ExecutionPhase(max_execution_iterations, llm)

        self.start_time = None
        self.results = {}

    def run(
        self,
        user_objective: str,
        user_data: str = "",
        domain_context: str = ""
    ) -> Dict[str, Any]:
        """
        Execute full autonomous pipeline.

        Args:
            user_objective: The objective to achieve
            user_data: Data/resources available
            domain_context: Domain-specific context

        Returns:
            Dictionary with:
            - success: Overall success status
            - phases_completed: List of completed phases
            - planning_result: Planning phase output
            - execution_result: Execution phase output
            - final_plan: Approved plan
            - final_implementation: Approved implementation
            - duration_seconds: Total execution time
        """
        self.start_time = datetime.now()

        logger.info("\n" + "=" * 80)
        logger.info("AUTONOMOUS PIPELINE STARTING")
        logger.info("=" * 80)
        logger.info(f"Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Objective: {user_objective}")
        logger.info("=" * 80)

        phases_completed = []
        phase_results = {}

        try:
            # PHASE 1: Planning
            logger.info("\n" + "=" * 80)
            logger.info("STARTING PHASE 1: ITERATIVE PLANNING")
            logger.info("=" * 80)

            planning_context = {
                "user_objective": user_objective,
                "user_data": user_data,
                "domain_context": domain_context
            }

            planning_result = self.planning_phase.execute(planning_context)
            phase_results["planning"] = planning_result

            if not planning_result.success:
                logger.error("❌ Planning phase failed")
                return self._create_result(
                    success=False,
                    phases_completed=phases_completed,
                    phase_results=phase_results,
                    reason="Planning phase did not produce an approved plan"
                )

            phases_completed.append("planning")
            approved_plan = planning_result.data["final_plan"]
            logger.info("\n✅ Planning phase complete")

            # PHASE 2: Execution
            logger.info("\n" + "=" * 80)
            logger.info("STARTING PHASE 2: ITERATIVE EXECUTION")
            logger.info("=" * 80)

            execution_context = {
                "approved_plan": approved_plan,
                "user_objective": user_objective,
                "user_data": user_data,
                "domain_context": domain_context
            }

            execution_result = self.execution_phase.execute(execution_context)
            phase_results["execution"] = execution_result

            if not execution_result.success:
                logger.warning("⚠️  Execution phase: Implementation not fully approved")

            phases_completed.append("execution")
            final_implementation = execution_result.data.get("final_implementation")
            logger.info("\n✅ Execution phase complete")

            # Success!
            return self._create_result(
                success=execution_result.success,
                phases_completed=phases_completed,
                phase_results=phase_results,
                final_plan=approved_plan,
                final_implementation=final_implementation
            )

        except Exception as e:
            logger.error(f"\n❌ Pipeline error: {str(e)}", exc_info=True)
            return self._create_result(
                success=False,
                phases_completed=phases_completed,
                phase_results=phase_results,
                error=str(e)
            )

    def _create_result(
        self,
        success: bool,
        phases_completed: list,
        phase_results: dict,
        **kwargs
    ) -> Dict[str, Any]:
        """Create final pipeline result."""
        duration = (datetime.now() - self.start_time).total_seconds()

        result = {
            "success": success,
            "phases_completed": phases_completed,
            "phase_results": phase_results,
            "duration_seconds": duration,
            "orchestrator_config": {
                "max_planning_iterations": self.max_planning_iterations,
                "max_execution_iterations": self.max_execution_iterations
            },
            **kwargs
        }

        # Log summary
        logger.info("\n" + "=" * 80)
        logger.info("AUTONOMOUS PIPELINE SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Success: {success}")
        logger.info(f"Phases completed: {', '.join(phases_completed)}")
        logger.info(f"Duration: {duration:.2f} seconds")

        if "final_plan" in kwargs:
            logger.info("✅ Plan: APPROVED")
        if "final_implementation" in kwargs:
            logger.info("✅ Implementation: APPROVED")
        if "error" in kwargs:
            logger.error(f"Error: {kwargs['error']}")

        logger.info("=" * 80 + "\n")

        return result
