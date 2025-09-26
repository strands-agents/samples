"""Adapted from τ-bench https://arxiv.org/abs/2406.12045"""

from mabench.environments.base import EnvProtocol
from typing import Callable, Dict, Optional, Union, Any
from mabench.environments.user import UserStrategy
from mabench.bench_types import (
    Action,
    EnvResetResponse,
    EnvResponse,
    RewardResult,
)


class CombinedEnv(EnvProtocol):
    name: str = "combined"

    def __init__(
        self,
        n_distractors: Optional[int] = None,
        user_strategy: Union[str, UserStrategy] = UserStrategy.LLM,
        user_model: str = "gpt-4o",
        user_provider: Optional[str] = None,
        task_split: str = "test",
        task_index: Optional[int] = None,
        **kwargs: Any,
    ):
        valid = (
            "spotify",
            "restaurant",
            "automotive",
            "pharmacy",
            "financialadvisor",
            "techsupport",
            "homeimprovement",
            "airline",
            "retail",
        )
        if n_distractors is not None and (
            n_distractors < 0 or n_distractors >= len(valid)
        ):
            raise ValueError(
                f"Invalid number of distractors: {n_distractors}. Must be between 0 and {len(valid) - 1}"
            )
        environments = valid[-((n_distractors or 0) + 1) :]
        print(f"Selected environments: {environments}")

        from mabench.environments import get_env

        self.environments = list(
            reversed(
                [
                    get_env(
                        env,
                        user_strategy,
                        user_model,
                        task_split,
                        user_provider,
                        task_index,
                        wrap_index=True,
                    )
                    for env in environments
                ]
            )
        )

        # Set the active environment and task index
        self.active_env_index = 0
        self.task_index = task_index

        # Set up active environment helper
        def get_active_env():
            return self.environments[self.active_env_index]

        self._get_active_env = get_active_env

        # Combine tools from all environments
        self.tools_map = {}
        for env in self.environments:
            self.tools_map.update(env.tools_map)

        # Combine tasks from all environments
        self.tasks = []
        for env in self.environments:
            self.tasks.extend(env.tasks)

        if not self.tasks:
            raise ValueError("No tasks found in any environment")

        self.task = (
            self.tasks[self.task_index]
            if self.task_index is not None
            else self.tasks[0]
        )

        self.wiki = "\n\n".join([env.wiki for env in self.environments])

        self.rules = []
        for env in self.environments:
            self.rules.extend(env.rules)

        self.user = self.environments[self.active_env_index].user
        self.actions = []
        self.terminate_tools = ["transfer_to_human_agents"]
        self.set_data(self._get_active_env().data)

    def _get_active_env(self):
        return self.environments[self.active_env_index]

    @property
    def data(self):
        from mabench.utils import get_data

        return get_data()

    def reset(self, task_index: Optional[int] = None) -> EnvResetResponse:
        if task_index is not None:
            self.task_index = task_index
        elif self.task_index is None:
            self.task_index = 0  # Default to first task if none specified

        # Determine which environment this task belongs to
        task_env_map = {}
        current_index = 0
        for i, env in enumerate(self.environments):
            for _ in env.tasks:
                task_env_map[current_index] = i
                current_index += 1

        # Set the active environment based on the task_index
        if self.task_index in task_env_map:
            self.active_env_index = task_env_map[self.task_index]
        else:
            raise ValueError(f"Invalid task index: {self.task_index}")

        # Reset the active environment
        active_env = self._get_active_env()
        print(f"Resetting active environment: {active_env.name}")

        # Find the equivalent task in the active environment
        task = self.tasks[self.task_index]
        env_task_index = None

        # Try to find the task in the active environment
        for i, env_task in enumerate(active_env.tasks):
            # Compare tasks by their attributes - might need adjustment
            if (
                hasattr(task, "id")
                and hasattr(env_task, "id")
                and task.id == env_task.id
            ):
                env_task_index = i
                break

        # If not found by ID, try direct comparison
        if env_task_index is None:
            try:
                env_task_index = active_env.tasks.index(task)
            except ValueError:
                # If we can't find the task, default to the first task
                if active_env.tasks:
                    env_task_index = 0
                else:
                    raise ValueError(
                        f"No tasks in the active environment {active_env.name}"
                    )

        reset_response = active_env.reset(task_index=env_task_index)

        # Update local properties
        self.task = self.tasks[self.task_index]
        self.set_data(active_env.data)
        self.actions = []

        return reset_response

    def set_data(self, data: dict):
        from mabench.utils import set_data

        set_data(data)

    def step(self, action: Action) -> EnvResponse:
        self.actions.append(action)
        return self._get_active_env().step(action)

    def get_data_hash(self) -> str:
        return self._get_active_env().get_data_hash()

    def calculate_reward(self) -> RewardResult:
        return self._get_active_env().calculate_reward()

    @property
    def tools_info(self) -> Dict[str, Dict[str, Callable]]:
        return {env.name: env.tools_map for env in self.environments}
