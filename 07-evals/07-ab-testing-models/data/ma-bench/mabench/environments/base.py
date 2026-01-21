"""Adapted from τ-bench https://arxiv.org/abs/2406.12045"""

import random
from hashlib import sha256
from typing import Any, Callable, Dict, List, Optional, Protocol, Set, Union, Tuple
import functools

from langchain_core.tools import tool as as_lc_tool
from mabench.environments.user import load_user, UserStrategy
from mabench.bench_types import (
    Action,
    Task,
    EnvInfo,
    EnvResetResponse,
    EnvResponse,
    RewardResult,
    RewardOutputInfo,
    RewardActionInfo,
    RESPOND_ACTION_NAME,
)
import langsmith as ls
import logging
from deepdiff import DeepDiff
import json


def pretty_deepdiff(a, b):
    diff = DeepDiff(a, b, verbose_level=2)
    # You can pretty print the diff dict as JSON for clarity
    try:
        return json.dumps(diff, indent=2, sort_keys=True)
    except BaseException:
        return str(diff)


logger = logging.getLogger(__name__)

ToHashable = Union[
    str, int, float, Dict[str, "ToHashable"], List["ToHashable"], Set["ToHashable"]
]
Hashable = Union[str, int, float, Tuple["Hashable"], Tuple[Tuple[str, "Hashable"]]]


def to_hashable(item: ToHashable) -> Hashable:
    if isinstance(item, dict):
        return tuple((key, to_hashable(value)) for key, value in sorted(item.items()))
    elif isinstance(item, list):
        return tuple(to_hashable(element) for element in item)
    elif isinstance(item, set):
        return tuple(sorted(to_hashable(element) for element in item))
    else:
        return item


def consistent_hash(
    value: Hashable,
) -> str:
    return sha256(str(value).encode("utf-8")).hexdigest()


def as_tool(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        result = fn(*args, **kwargs)
        if "error:" in str(result).lower():
            rt = ls.get_current_run_tree()
            if rt is not None:
                rt.error = str(result)
        return result

    return as_lc_tool()(wrapper)


class EnvProtocol(Protocol):
    name: str
    data: Dict[str, Any]
    tools_map: Dict[str, Callable]
    terminate_tools: List[str]
    tasks: List[Task]
    task_index: int
    task: Task
    wiki: str
    rules: List[str]
    user: Any
    actions: List[Action]

    def reset(self, task_index: Optional[int] = None) -> EnvResetResponse: ...

    def step(self, action: Action) -> EnvResponse: ...

    def get_data_hash(self) -> str: ...

    def calculate_reward(self) -> RewardResult: ...


class Env(object):
    name: str

    def __init__(
        self,
        data_load_func: Callable[[], Dict[str, Any]],
        tools: List[Callable],
        tasks: List[Task],
        wiki: str,
        rules: List[str],
        user_strategy: Union[str, UserStrategy],
        user_model: str,
        user_provider: Optional[str] = None,
        task_index: Optional[int] = None,
        wrap_index: bool = False,
    ) -> None:
        super().__init__()
        self.data_load_func = data_load_func
        self.data = self.data_load_func()
        self.tools_map: Dict[str, Callable] = {
            tool.__name__: as_tool(tool) for tool in tools
        }
        self.terminate_tools = []
        logger.error(f"Loaded {len(tasks)} tasks for env {self.name}")
        self.tasks = tasks
        if task_index is not None:
            self.task_index = task_index
        else:
            logger.error(f"Huh randomizing? {len(tasks)}")
            self.task_index = random.randint(0, len(tasks))
        try:
            if tasks:
                ti = self.task_index % len(tasks) if wrap_index else self.task_index
                self.task = tasks[ti]
            else:
                self.task = None
        except IndexError:
            logger.error(
                f"Invalid task index: {self.task_index}. Max index: {len(tasks)}"
            )
            raise
        self.wiki = wiki
        self.rules = rules
        self.user = load_user(
            user_strategy=user_strategy, model=user_model, provider=user_provider
        )
        self.actions: List[Action] = []

    def reset(self, task_index: Optional[int] = None) -> EnvResetResponse:
        if task_index is None:
            task_index = random.randint(0, len(self.tasks))
        self.task_index = task_index
        self.data = self.data_load_func()
        self.task = self.tasks[task_index] if self.tasks else None
        self.actions = []
        initial_observation = self.user.reset(instruction=self.task.instruction)
        self.set_data(self.data)
        return EnvResetResponse(
            observation=initial_observation, info=EnvInfo(task=self.task, source="user")
        )

    def set_data(self, data: Dict[str, Any]):
        from mabench.utils import set_data

        set_data(data)

    @ls.traceable
    def step(self, action: Action | list) -> EnvResponse:
        if isinstance(action, Action):
            return self._step_action(action)

        msg = action[-1]
        msg_content = msg.content if hasattr(msg, "content") else msg["content"]
        self.actions.append(
            Action(name=RESPOND_ACTION_NAME, kwargs={"content": msg_content})
        )
        # It's a list of messages, from langgraph.
        info = EnvInfo(task=self.task, source="user")
        observation = self.user.step(msg_content)
        done = "###STOP###" in observation
        reward = 0
        if done:
            reward_res = self.calculate_reward()
            reward = reward_res.reward
            info.reward_info = reward_res
            info.user_cost = self.user.get_total_cost()
        return EnvResponse(observation=observation, reward=reward, done=done, info=info)

    def _step_action(self, action: Action) -> EnvResponse:
        self.actions.append(action)

        info = EnvInfo(task=self.task)
        reward = 0
        done = False
        if action.name == RESPOND_ACTION_NAME:
            observation = self.user.step(action.kwargs["content"])
            info.source = "user"
            done = "###STOP###" in observation
        elif action.name in self.tools_map:
            try:
                observation = self.tools_map[action.name].invoke(action.kwargs)
            except Exception as e:
                observation = f"Error: {e}"
            info.source = action.name
            if action.name in self.terminate_tools:
                done = True
        else:
            observation = f"Unknown action {action.name}"
            info.source = action.name

        if done:
            reward_res = self.calculate_reward()
            reward = reward_res.reward
            info.reward_info = reward_res
            info.user_cost = self.user.get_total_cost()
        return EnvResponse(observation=observation, reward=reward, done=done, info=info)

    def get_data_hash(self) -> str:
        from mabench.utils import get_data

        data = get_data()
        return consistent_hash(to_hashable(data))

    def calculate_reward(self) -> RewardResult:
        data_hash = self.get_data_hash()
        from mabench.utils import get_data

        og_data = get_data().copy()
        reward = 1.0  # Start out assuming success
        # You can fail if either:
        # a) You don't take the required actions
        # b) You don't respond with the right things. (really lax here though)
        actions = [
            action for action in self.task.actions if action.name != RESPOND_ACTION_NAME
        ]

        # Check if the database changes are correct. If they are not correct, then we set the reward to 0.
        # TODO: cache gt_data_hash in tasks.py (low priority)
        self.set_data(self.data_load_func())
        with ls.trace(
            "calculate_reward", inputs={"data_hash": data_hash, "actions": actions}
        ) as rt:
            with ls.trace(
                "calculate_ground_truth_reward", inputs={"data_hash": data_hash}
            ) as rtgt:
                for action in self.task.actions:
                    if action.name not in self.terminate_tools:
                        self.step(action)
                gt_data_hash = self.get_data_hash()
                info = RewardActionInfo(
                    r_actions=data_hash == gt_data_hash, gt_data_hash=gt_data_hash
                )
                # We compare side effects.
                if not info.r_actions:
                    gt_data = get_data().copy()
                    expected_actions = "\n".join(
                        [
                            f"{action.name}: {action.kwargs}"
                            for action in self.task.actions
                            if action.name != RESPOND_ACTION_NAME
                        ]
                    )
                    diff = pretty_deepdiff(og_data, gt_data)
                    print(
                        f"\n###  Different State   ###\n\nDiff:\n\n{diff}\n\nExpected:\n\n{expected_actions}"
                    )
                    rt.client.create_feedback(
                        rt.trace_id,
                        key="action_state",
                        score=0.0,
                        comment=f"Expected actions:\n\n{expected_actions}\n\nData diff:\n\n{diff}",
                    )
                    reward = 0.0
                else:
                    print("OH SAME DB STATE", data_hash, gt_data_hash)
                    rt.client.create_feedback(
                        rt.trace_id, key="action_state", score=1.0
                    )
                rtgt.add_outputs(
                    {"info": info, "reward": reward, "gt_data_hash": gt_data_hash}
                )

            if len(self.task.outputs) > 0:
                # check outputs
                r_outputs = 1.0
                outputs = {}
                comments = []
                action_contents = [
                    action.kwargs["content"]
                    for action in self.actions
                    if action.name == RESPOND_ACTION_NAME
                ]
                for output in self.task.outputs:
                    found = False
                    for action_content in action_contents:
                        if output.lower() in action_content.lower().replace(",", ""):
                            found = True
                            break
                    outputs[output] = found
                    if not found:
                        comments.append(f"Missing output: {output}")
                        r_outputs = 0.0
                        reward = 0.0
                rt.client.create_feedback(
                    rt.trace_id,
                    key="output_state",
                    score=r_outputs,
                    comment="\n".join(comments)
                    + "\n\n"
                    + "In actions: "
                    + "\n"
                    + "\n".join(action_contents),
                )
                info = RewardOutputInfo(r_outputs=r_outputs, outputs=outputs)
            else:
                rt.client.create_feedback(
                    rt.trace_id,
                    key="output_state",
                    score=None,
                    comment="Output not required.",
                )

            result = RewardResult(reward=reward, info=info, actions=actions)
            rt.add_outputs({"result": result})
            return result
