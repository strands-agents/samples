"""Adapted from τ-bench https://arxiv.org/abs/2406.12045"""

from mabench.environments.airline.data import load_data
from mabench.environments.airline.rules import RULES
from mabench.environments.airline.tools import ALL_TOOLS
from mabench.environments.airline.wiki import WIKI
from mabench.environments.base import Env
from typing import Optional, Union, Callable, Any
from mabench.environments.user import UserStrategy


class MockAirlineDomainEnv(Env):
    name: str = "airline"

    def __init__(
        self,
        user_strategy: Union[str, UserStrategy] = UserStrategy.LLM,
        user_model: str = "gpt-4o",
        user_provider: Optional[str] = None,
        task_split: str = "test",
        task_index: Optional[int] = None,
        **kwargs: Any,
    ):
        match task_split:
            case "test":
                from mabench.environments.airline.tasks_test import TASKS as tasks
            case _:
                raise ValueError(f"Unknown task split: {task_split}")
        super().__init__(
            data_load_func=load_data,
            tools=ALL_TOOLS,
            tasks=tasks,
            wiki=WIKI,
            rules=RULES,
            user_strategy=user_strategy,
            user_model=user_model,
            user_provider=user_provider,
            task_index=task_index,
            **kwargs,
        )
        self.terminate_tools = ["transfer_to_human_agents"]

    @property
    def tools_info(self) -> dict[str, dict[str, Callable]]:
        return {self.name: self.tools_map}
