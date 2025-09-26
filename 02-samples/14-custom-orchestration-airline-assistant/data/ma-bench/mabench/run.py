# Adapted from τ-bench https://arxiv.org/abs/2406.12045 by Sierra
import langsmith as ls
import uuid
from tqdm import tqdm
from mabench.environments.base import Env
import concurrent.futures
from mabench.bench_types import (
    SolveResult,
)
from typing import Optional

import os
import json
import random
import argparse
import traceback
from math import comb
import multiprocessing
from datetime import datetime
from typing import List
from concurrent.futures import ThreadPoolExecutor

from mabench.environments import get_env
from mabench.bench_types import EnvRunResult
from mabench.agents import agent_factory
from mabench.environments.user import UserStrategy
from langgraph.graph.state import CompiledStateGraph
from langgraph.pregel.remote import RemoteGraph
import logging

logger = logging.getLogger(__name__)


def run(
    args: argparse.Namespace,
    ckpt_path: str,
) -> List[EnvRunResult]:
    print(f"Loading user with strategy: {args.user_strategy}")
    env = get_env(
        args.env,
        user_strategy=args.user_strategy,
        user_model=args.user_model,
        user_provider=args.user_model_provider,
        task_split=args.task_split,
        n_distractors=args.n_distractors,
    )
    if args.remote:
        1 / 0
        agent = RemoteGraph("graphs", url="http://localhost:2024")
    else:
        agent = agent_factory(
            env=env,
            agent_strategy=args.agent_strategy,
            model=args.model,
        )
    end_index = (
        len(env.tasks) if args.end_index == -1 else min(args.end_index, len(env.tasks))
    )
    results: List[EnvRunResult] = []
    lock = multiprocessing.Lock()
    if args.task_ids and len(args.task_ids) > 0:
        print(f"Running tasks {args.task_ids} (checkpoint path: {ckpt_path})")
    else:
        print(
            f"Running tasks {args.start_index} to {end_index} (checkpoint path: {ckpt_path})"
        )
    response_error = None
    lsc = ls.Client()
    dataset_name = f"τ-bench/{args.env}"
    if not lsc.has_dataset(dataset_name=dataset_name):
        ds = lsc.create_dataset(dataset_name)
        examples_ = [
            {
                "inputs": task.example_inputs,
                "outputs": task.example_outputs,
                "metadata": {"index": idx},
            }
            for idx, task in enumerate(env.tasks)
        ]
        lsc.create_examples(examples=examples_, dataset_id=ds.id)
        dataset_id = ds.id
    else:
        dataset_id = lsc.read_dataset(dataset_name=dataset_name).id
    example_ids = {
        example.metadata["index"]: example.id
        for example in lsc.list_examples(dataset_id=dataset_id)
    }

    if args.existing:
        experiment = lsc.read_project(project_id=args.existing)
    else:
        experiment = lsc.create_project(
            ckpt_path.split("/")[-1].split(".json")[0],
            reference_dataset_id=dataset_id,
            metadata={**vars(args), "env": env.name},
        )
    try:
        for i in range(args.num_trials):
            if args.task_ids and len(args.task_ids) > 0:
                idxs = args.task_ids
            else:
                idxs = list(range(args.start_index, end_index))
            if args.shuffle:
                random.shuffle(idxs)

            @ls.traceable(name="Run Experiment")
            def _run(idx: int, agent) -> EnvRunResult:
                rt = ls.get_current_run_tree()
                rt.metadata.update(vars(args))
                rt.metadata["task_index"] = idx
                rt.metadata["experiment_path"] = str(ckpt_path)
                isolated_env = get_env(
                    args.env,
                    user_strategy=args.user_strategy,
                    user_model=args.user_model,
                    task_split=args.task_split,
                    user_provider=args.user_model_provider,
                    task_index=idx,
                    n_distractors=args.n_distractors,
                )

                print(f"Running task {idx}")
                try:
                    res = solve(
                        agent,
                        env=isolated_env,
                        args=args,
                        task_index=idx,
                    )
                    result = EnvRunResult(
                        task_id=idx,
                        reward=res.reward,
                        info=res.info,
                        traj=res.messages,
                        trial=i,
                    )
                except BaseException as e:
                    rt = ls.get_current_run_tree()
                    rt.error = repr(e)
                    print(f"❌ task_id={idx}: {rt.get_url()}")
                    result = EnvRunResult(
                        task_id=idx,
                        reward=0.0,
                        info={"error": str(e), "traceback": traceback.format_exc()},
                        traj=[],
                        trial=i,
                    )
                print(
                    "✅" if result.reward == 1 else "❌",
                    f"task_id={idx}",
                    result.info,
                )
                print("-----")
                with lock:
                    data = []
                    if os.path.exists(ckpt_path):
                        with open(ckpt_path, "r") as f:
                            data = json.load(f)
                    with open(ckpt_path, "w") as f:
                        json.dump(data + [result.model_dump()], f, indent=2)
                rt.client.create_feedback(rt.id, key="reward", score=result.reward)
                return result

            def _run_example(idx: int) -> EnvRunResult:
                return _run(
                    idx,
                    agent=agent,
                    langsmith_extra={
                        "reference_example_id": example_ids[idx],
                        "project_name": experiment.name,
                    },
                )

            if args.max_concurrency == 0:
                for idx in tqdm(idxs):
                    try:
                        results.append(_run_example(idx))
                    except Exception as e:
                        logger.error(f"Error running task {idx}: {e}")
                        results.append(
                            EnvRunResult(
                                task_id=idx,
                                reward=0.0,
                                info={
                                    "error": str(e),
                                    "traceback": traceback.format_exc(),
                                },
                                traj=[],
                                trial=idx,
                            )
                        )
            else:
                with ThreadPoolExecutor(max_workers=args.max_concurrency) as executor:
                    futures = [executor.submit(_run_example, idx) for idx in idxs]
                    results.extend(
                        [
                            fut.result()
                            for fut in concurrent.futures.as_completed(futures)
                        ]
                    )
    except Exception as e:
        response_error = e
    return results, response_error


def display_metrics(results: List[EnvRunResult]) -> None:
    def is_successful(reward: float) -> bool:
        return (1 - 1e-6) <= reward <= (1 + 1e-6)

    num_trials = len(set([r.trial for r in results]))
    rewards = [r.reward for r in results]
    avg_reward = sum(rewards) / len(rewards)
    # c from https://arxiv.org/pdf/2406.12045
    c_per_task_id: dict[int, int] = {}
    for result in results:
        if result.task_id not in c_per_task_id:
            c_per_task_id[result.task_id] = 1 if is_successful(result.reward) else 0
        else:
            c_per_task_id[result.task_id] += 1 if is_successful(result.reward) else 0
    pass_hat_ks: dict[int, float] = {}
    for k in range(1, num_trials + 1):
        sum_task_pass_hat_k = 0
        for c in c_per_task_id.values():
            sum_task_pass_hat_k += comb(c, k) / comb(num_trials, k)
        pass_hat_ks[k] = sum_task_pass_hat_k / len(c_per_task_id)
    print(f"🏆 Average reward: {avg_reward}")
    print("📈 Pass^k")
    for k, pass_hat_k in pass_hat_ks.items():
        print(f"  k={k}: {pass_hat_k}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-trials", type=int, default=1)
    parser.add_argument(
        "--env", type=str, choices=["retail", "airline", "combined"], default="retail"
    )
    parser.add_argument(
        "--model",
        type=str,
        help="The model to use for the agent",
    )
    parser.add_argument(
        "--model-provider",
        type=str,
        help="The model provider for the agent",
    )
    parser.add_argument(
        "--user-model",
        type=str,
        default="gpt-4o",
        help="The model to use for the user simulator",
    )
    parser.add_argument(
        "--user-model-provider",
        type=str,
        help="The model provider for the user simulator",
    )
    parser.add_argument(
        "--agent-strategy",
        type=str,
        default="tool-calling",
        choices=[
            "single",
            "supervisor",
            "swarm",
            "tree",
            "supervisor-invisihandoffs",
            "supervisor-forwarding",
            "supervisor-forwarding-and-invisihandoffs",
            "supervisor-forwarding-and-invisihandoffs-transfer-prefix",
            "supervisor-transfer-prefix",
        ],
    )
    parser.add_argument(
        "--remote",
        action="store_true",
        help="Run the agent remotely",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="The sampling temperature for the action model",
    )
    parser.add_argument(
        "--task-split",
        type=str,
        default="test",
        choices=["train", "test", "dev"],
        help="The split of tasks to run (only applies to the retail domain for now",
    )
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--end-index", type=int, default=-1, help="Run all tasks if -1")
    parser.add_argument(
        "--task-ids",
        type=int,
        nargs="+",
        help="(Optional) run only the tasks with the given IDs",
    )
    parser.add_argument("--log-dir", type=str, default="results")
    parser.add_argument(
        "--max-concurrency",
        type=int,
        default=1,
        help="Number of tasks to run in parallel",
    )
    parser.add_argument("--seed", type=int, default=10)
    parser.add_argument("--shuffle", type=int, default=0)
    parser.add_argument(
        "--user-strategy",
        type=str,
        default="llm",
        choices=[item.value for item in UserStrategy],
    )
    parser.add_argument(
        "--few-shot-displays-path",
        type=str,
        help="Path to a jsonlines file containing few shot displays",
    )
    parser.add_argument(
        "--n-distractors",
        type=int,
        default=0,
        help="Number of distractors to use",
    )
    parser.add_argument(
        "--existing", type=str, help="Existing project ID to use", default=None
    )
    args = parser.parse_args()
    print(args)
    random.seed(args.seed)

    time_str = datetime.now().strftime("%m%d%H%M%S")
    file_str = f"{args.log_dir}/{args.agent_strategy}-{args.model.split('/')[-1]}-distract_{args.n_distractors}-{args.temperature}_range_{args.start_index}-{args.end_index}_user-{args.user_model}-{args.user_strategy}_{time_str}.json"

    if not os.path.exists(args.log_dir):
        os.makedirs(args.log_dir)

    results, response_error = run(
        args=args,
        ckpt_path=file_str,
    )
    if not results and response_error:
        raise response_error
    display_metrics(results)

    with open(file_str, "w") as f:
        json.dump([result.model_dump() for result in results], f, indent=2)
        print(f"\n📄 Results saved to {file_str}\n")
    if response_error:
        raise response_error


@ls.traceable(name="Solve")
def solve(
    agent: CompiledStateGraph,
    env: Env,
    args,
    task_index: Optional[int] = None,
    max_num_turns: int = 30,
) -> SolveResult:
    rt = ls.get_current_run_tree()
    assert rt is not None
    if args.remote:
        1 / 0
        agent = agent.copy(
            {
                "headers": rt.to_headers(),
                "client": None,
                "sync_client": None,
                "url": "http://localhost:2024",
            }
        )
    config = {
        "configurable": {
            "thread_id": str(uuid.uuid4()),
            "agent_strategy": args.agent_strategy,
            "user_model": args.user_model,
            "model": args.model,
            "task_split": args.task_split,
            "task_index": task_index,
            "n_distractors": args.n_distractors,
        }
    }
    reset_response = env.reset(task_index=task_index)
    reward = 0.0
    next_message = {"role": "user", "content": reset_response.observation}
    info = {}
    rt = ls.get_current_run_tree()
    assert rt is not None
    for _ in range(max_num_turns):
        new_state = agent.invoke({"messages": [next_message]}, config)
        env_response = env.step(new_state["messages"])
        obs = env_response.observation
        reward = env_response.reward
        info = {**info, **env_response.info.model_dump()}
        if env_response.done:
            break
        next_message = {"role": "user", "content": obs}
        if env_response.done:
            break
    state = agent.get_state(config)
    messages = state.values["messages"]

    return SolveResult(
        messages=messages,
        reward=reward,
        info=info,
    )


if __name__ == "__main__":
    main()
