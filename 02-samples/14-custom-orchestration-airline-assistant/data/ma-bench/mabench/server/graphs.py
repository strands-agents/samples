from mabench.agents import agent_factory
from mabench.environments import get_env
import langsmith as ls
from contextlib import contextmanager


@contextmanager
def graphs(config):
    configurable = config.get("configurable", {})
    env = get_env(
        "combined",
        user_strategy="llm",
        user_model=configurable.get("user_model", "gpt-4o"),
        task_split=configurable.get("task_split", "test"),
        n_distractors=configurable.get("n_distractors", 0),
        task_index=configurable.get("task_index"),
    )
    agent = agent_factory(
        env,
        configurable.get("agent_strategy", "single"),
        configurable.get("model", "gpt-4o"),
    )
    parent = None
    if parent_trace := configurable.get("langsmith-trace"):
        parent = ls.RunTree.from_dotted_order(
            parent_trace, project_name=configurable.get("langsmith-project")
        )

    with ls.tracing_context(parent=parent):
        yield agent
