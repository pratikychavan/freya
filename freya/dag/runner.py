from __future__ import annotations

import asyncio
import logging
from typing import Any

from freya.dag.models import DAG, DAGResult, DAGTask
from freya.dag.validation import validate_dag, topological_generations
from freya.engine import ExecutionEngine
from freya.memory.store import InMemoryStore
from freya.models import Task, TaskResult
from freya.tracing.manager import TraceManager

logger = logging.getLogger(__name__)


class DAGRunner:
    def __init__(self, engine: ExecutionEngine) -> None:
        self._engine = engine

    async def run(
        self,
        dag: DAG,
        memory: Any | None = None,
        session_id: str | None = None,
    ) -> DAGResult:
        validate_dag(dag)

        task_map: dict[str, DAGTask] = {t.task_id: t for t in dag.tasks}
        generations = topological_generations(dag)

        completed: dict[str, TaskResult] = {}
        failed: set[str] = set()
        trace_manager = TraceManager()
        if session_id:
            trace_manager.dag_trace.session_id = session_id
        shared_memory = memory if memory is not None else InMemoryStore()

        for generation in generations:
            # Skip tasks whose dependencies already failed
            runnable = [
                tid for tid in generation
                if not any(dep in failed for dep in task_map[tid].depends_on)
            ]
            skipped = set(generation) - set(runnable)
            for tid in skipped:
                logger.warning("Skipping task '%s' — dependency failed.", tid)
                failed.add(tid)

            if not runnable:
                continue

            tasks_to_run = [
                self._build_task(task_map[tid], completed) for tid in runnable
            ]

            logger.info("Starting tasks: %s", runnable)
            results = await asyncio.gather(
                *[
                    self._engine.execute_task(t, trace_manager, shared_memory)
                    for t in tasks_to_run
                ],
                return_exceptions=False,
            )

            for tid, result in zip(runnable, results):
                completed[tid] = result
                if result.status == "FAILED":
                    logger.error("Task '%s' FAILED: %s", tid, result.error)
                    failed.add(tid)
                else:
                    logger.info("Task '%s' succeeded.", tid)

        overall = "FAILED" if failed else "SUCCESS"
        trace_manager.finalize(overall)
        return DAGResult(results=completed, status=overall, dag_trace=trace_manager.dag_trace)

    # ------------------------------------------------------------------

    def _build_task(
        self, dag_task: DAGTask, completed: dict[str, TaskResult]
    ) -> Task:
        merged_input: dict[str, Any] = {**dag_task.input}

        for dep_id in dag_task.depends_on:
            dep_result = completed.get(dep_id)
            if dep_result and dep_result.output is not None:
                merged_input[dep_id] = dep_result.output

        return Task(
            task_id=dag_task.task_id,
            type=dag_task.type,
            input=merged_input,
            config=dag_task.config,
        )
