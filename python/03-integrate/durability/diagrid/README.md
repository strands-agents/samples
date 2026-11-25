# Durable Strands agents with Dapr Workflow

Make a Strands agent durable with Dapr Workflow and the `diagrid` package, so a run that crashes resumes from its last completed step instead of starting over.

## Overview

A Strands agent normally keeps its progress in memory. If the process stops halfway through a run, that progress is gone: the agent starts again, calls the model again, and may run tools twice. This sample wraps the agent in `DaprWorkflowAgentRunner` from [`diagrid[strands]`](https://pypi.org/project/diagrid/). Each model call and each tool call becomes a Dapr Workflow activity, and Dapr saves the result of every activity. When the process comes back, Dapr replays the saved history and only runs what has not finished yet.

### Sample Details

| Information            | Details                                                         |
|------------------------|-----------------------------------------------------------------|
| **Agent Architecture** | Single-agent                                                    |
| **Native Tools**       | None                                                            |
| **Custom Tools**       | `get_weather`, `convert_temperature`, `step_one`, `step_two`, `step_three` |
| **MCP Servers**        | None                                                            |
| **Use Case Vertical**  | Cross-industry                                                  |
| **Complexity**         | Basic                                                           |
| **Model Provider**     | Amazon Bedrock (OpenAI optional)                                |
| **SDK Used**           | Strands Agents SDK, `diagrid[strands]`, Dapr                    |

### Architecture

![A Strands agent running as a durable Dapr workflow](./images/architecture.svg)

The agent runs in your Python process next to a Dapr sidecar. The sidecar's workflow engine drives the agent loop: it schedules a "call model" activity, then a "run tool" activity for each tool the model asks for, and so on until the model gives its answer. The sidecar stores the workflow's progress in Redis.

### Key Features

- Durable agent runs: a run that is interrupted continues from its last completed step.
- No changes to your agent or tools. You pass an ordinary Strands `Agent` to `DaprWorkflowAgentRunner`.
- Runs locally with the open source Dapr CLI, so you don't need an account to try it.

## Prerequisites

- Python 3.11, 3.12 or 3.13
- [uv](https://docs.astral.sh/uv/getting-started/installation/) for dependency management
- [Docker](https://docs.docker.com/get-docker/), used by `dapr init`
- The [Dapr CLI](https://docs.dapr.io/getting-started/install-dapr-cli/), initialized with `dapr init`. This starts a local Redis container that the sample uses. Tested with Dapr 1.19.
- One model provider:
  - Amazon Bedrock (default): AWS credentials and [model access](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access-modify.html) to Amazon Nova Pro (`us.amazon.nova-pro-v1:0`)
  - OpenAI: an API key

## Setup

1. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env: keep MODEL_PROVIDER=bedrock, or set MODEL_PROVIDER=openai and OPENAI_API_KEY
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```

3. **Initialize Dapr** (once per machine, if you haven't already):
   ```bash
   dapr init
   ```

## Usage

Run the commands from this folder. `dapr run` starts a Dapr sidecar next to the script and loads the components in `./resources`.

### A durable agent run

`simple_agent.py` asks a weather question. The agent calls two tools, and every step runs as a workflow activity.

```bash
dapr run --app-id simple-agent --resources-path ./resources -- uv run python simple_agent.py
```

Among the Dapr logs you'll see:

```text
Workflow started: strands-simple-agent-demo-c2419a9c
Status: RUNNING
Status: COMPLETED

Tool calls:
  - get_weather
  - convert_temperature

Answer:
The weather in Amsterdam is cloudy with light rain, and the temperature is 12 degrees Celsius, which is 53.6 degrees Fahrenheit.
```

### Crash and resume

`crash_recovery.py` gives the agent three tools that it calls in order. On the first run the process exits while `step_two` is running, as if the machine went down. Each tool writes to a log file, so you can see exactly which steps ran.

1. Run it once. The process stops during `step_two`:

   ```bash
   dapr run --app-id crash-recovery --resources-path ./resources -- uv run python crash_recovery.py
   ```

   ```text
   Starting the workflow runtime. Dapr resumes an unfinished workflow right away.
   Starting workflow strands-durability-demo
   >>> step_one: start
   >>> step_one: done
   >>> step_two: start

   >>> Simulating a crash while step_two is running.
   >>> Run the same command again to resume the workflow.
   ```

2. Run the same command again. Dapr finds the unfinished workflow and resumes it. `step_one` already finished, so it does not run again. `step_two` never finished, so it runs again, followed by `step_three`:

   ```text
   Starting the workflow runtime. Dapr resumes an unfinished workflow right away.
   Workflow strands-durability-demo was interrupted. Waiting for the resumed run to finish...
   >>> step_two: start
   >>> step_two: done
   >>> step_three: start
   >>> step_three: done

   Workflow status: COMPLETED
   Tool calls recorded across all runs:
     step_one: started 1x, finished 1x
     step_two: started 2x, finished 1x
     step_three: started 1x, finished 1x

   PASS: the workflow resumed after the crash and did not repeat completed steps.
   ```

The model calls are activities too, so the model is not asked again for the steps that already completed.

To run the demo again from the start, reset it first:

```bash
dapr run --app-id crash-recovery --resources-path ./resources -- uv run python crash_recovery.py --reset
```

## How it works

```python
from diagrid.agent.strands import DaprWorkflowAgentRunner
from strands import Agent

agent = Agent(model=build_model(), tools=[get_weather, convert_temperature])
runner = DaprWorkflowAgentRunner(agent=agent, name="simple-agent")

runner.start()
async for event in runner.run_async(task="...", session_id="simple-agent-demo"):
    ...
runner.shutdown()
```

- `runner.start()` registers a workflow and two activities with the Dapr sidecar: one that calls the model, and one that runs a tool.
- `run_async` starts a workflow instance for the task and yields events as it progresses.
- Dapr writes the result of every activity to the state store in `resources/statestore.yaml`. When a process with the same app ID starts again, Dapr replays that history and continues with the first activity that has no result.
- `resources/agent-memory.yaml` gives the agent's conversation history a durable home as well.

## Cleanup

Reset the crash demo:

```bash
dapr run --app-id crash-recovery --resources-path ./resources -- uv run python crash_recovery.py --reset
```

To remove the local Dapr containers and binaries, run `dapr uninstall --all`.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `No Dapr sidecar found. Start this script with dapr run ...` | The script was started with `uv run python` on its own | Start it with the `dapr run` command shown above |
| The answer is `Error: ... Access to Bedrock models is not allowed for this account` or `AccessDeniedException` | Your AWS account or role has no access to the model | Enable model access in the Bedrock console, or set `MODEL_PROVIDER=openai` |
| `The tool log and the workflow store disagree` | Redis was flushed, or the workflow was removed, after a crash run | Run the script with `--reset` |
| `FAIL: the tool calls do not match a single crash and resume` | The demo ran more than once without a reset in between | Run the script with `--reset`, then start again |

## Usage analytics and licensing

When a runner starts, the `diagrid` package sends one anonymous usage event per process (package and framework versions, OS and Python version, no prompts or app data). Set `DO_NOT_TRACK=1` to turn it off. The [`diagrid` README](https://github.com/diagridio/python-ai#usage-analytics) lists exactly what is sent.

The `diagrid` package is published by Diagrid under the Business Source License 1.1. The code in this sample is licensed under Apache 2.0, like the rest of this repository.

## Additional Resources

- [Diagrid docs: Strands agents](https://docs.diagrid.io/develop/agents/strands/)
- [Dapr Workflow overview](https://docs.dapr.io/developing-applications/building-blocks/workflow/workflow-overview/)
- [`diagridio/python-ai` on GitHub](https://github.com/diagridio/python-ai)
- [Diagrid Catalyst](https://www.diagrid.io/catalyst), a hosted option for running these workflows without managing Dapr yourself

## Disclaimer

This sample is provided for educational and demonstration purposes only. It is not intended for production use without further development, testing, and hardening.

For production deployments, consider:
- Implementing appropriate content filtering and safety measures
- Following security best practices for your deployment environment
- Conducting thorough testing and validation
- Reviewing and adjusting configurations for your specific requirements
