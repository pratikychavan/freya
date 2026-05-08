from __future__ import annotations

from collections import deque

from freya.dag.models import DAG


class DAGValidationError(ValueError):
    pass


def validate_dag(dag: DAG) -> None:
    """Raise DAGValidationError if the DAG has missing refs or cycles."""
    ids = {t.task_id for t in dag.tasks}

    # 1. All dependency references must exist
    for task in dag.tasks:
        for dep in task.depends_on:
            if dep not in ids:
                raise DAGValidationError(
                    f"Task '{task.task_id}' depends on unknown task '{dep}'."
                )

    # 2. Cycle detection via Kahn's algorithm
    in_degree: dict[str, int] = {t.task_id: 0 for t in dag.tasks}
    adjacency: dict[str, list[str]] = {t.task_id: [] for t in dag.tasks}

    for task in dag.tasks:
        for dep in task.depends_on:
            adjacency[dep].append(task.task_id)
            in_degree[task.task_id] += 1

    queue: deque[str] = deque(tid for tid, deg in in_degree.items() if deg == 0)
    visited = 0

    while queue:
        node = queue.popleft()
        visited += 1
        for neighbour in adjacency[node]:
            in_degree[neighbour] -= 1
            if in_degree[neighbour] == 0:
                queue.append(neighbour)

    if visited != len(dag.tasks):
        raise DAGValidationError("DAG contains a cycle.")


def topological_generations(dag: DAG) -> list[list[str]]:
    """
    Return tasks grouped into generations (waves) that can run in parallel.
    Each generation depends only on tasks in earlier generations.
    """
    in_degree: dict[str, int] = {t.task_id: 0 for t in dag.tasks}
    adjacency: dict[str, list[str]] = {t.task_id: [] for t in dag.tasks}

    for task in dag.tasks:
        for dep in task.depends_on:
            adjacency[dep].append(task.task_id)
            in_degree[task.task_id] += 1

    generations: list[list[str]] = []
    ready = [tid for tid, deg in in_degree.items() if deg == 0]

    while ready:
        generations.append(ready)
        next_ready: list[str] = []
        for node in ready:
            for neighbour in adjacency[node]:
                in_degree[neighbour] -= 1
                if in_degree[neighbour] == 0:
                    next_ready.append(neighbour)
        ready = next_ready

    return generations
