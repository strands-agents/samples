"""Adapted from τ-bench https://arxiv.org/abs/2406.12045"""

from mabench.environments.base import Env
from mabench.environments.retail.data import load_data
from mabench.environments.retail.rules import RULES
from mabench.environments.retail.tools import ALL_TOOLS
from mabench.environments.retail.wiki import WIKI
from typing import Optional, Union
from mabench.environments.user import UserStrategy
from typing import Callable, Any


class MockRetailDomainEnv(Env):
    name: str = "retail"

    def __init__(
        self,
        user_strategy: Union[str, UserStrategy] = UserStrategy.LLM,
        user_model: str = "gpt-4o",
        user_provider: Optional[str] = None,
        task_split: str = "test",
        task_index: Optional[int] = None,
        wrap_index: bool = False,
        **kwargs: Any,
    ):
        print("TASK SPLIT", task_split)
        match task_split:
            case "test":
                from mabench.environments.retail.tasks_test import TASKS_TEST as tasks
            case "train":
                from mabench.environments.retail.tasks_train import TASKS_TRAIN as tasks
            case "dev":
                from mabench.environments.retail.tasks_dev import TASKS_DEV as tasks
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
            wrap_index=wrap_index,
            **kwargs,
        )
        self.terminate_tools = ["transfer_to_human_agents"]

    @property
    def tools_info(self) -> dict[str, dict[str, Callable]]:
        return {self.name: self.tools_map}
