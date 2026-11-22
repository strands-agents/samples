# PHM Physics Guard Integration

Example for integrating Strands Agent with [PHM Physics Guard](https://github.com/PHM-Audit/strands-phm-guard) (`strands-phm-guard` on PyPI), a deterministic physics/bounds intervention handler.

Where content-safety guardrails check *what the model says*, Physics Guard checks whether *what the agent is about to do is physically possible*. Physically impossible tool calls (faster-than-light speeds, negative masses, NaN leaking into measurements, impossible depths) are denied before execution.

Physics Guard provides:

- **Deterministic verdicts**: fixed rule table, no LLM in the loop, no external API; every verdict is recomputable
- **Pre-execution intervention**: implements the standard Strands `InterventionHandler` interface, invoked by the framework before each tool run
- **Three-state exits**: `Proceed` (clean), `Guide` (violations returned to the model for self-correction), `Deny` (hard veto)
- **Operator-declared bounds**: extend the default hard limits (speed of light, 12 km ocean depth, 40 km altitude, 1 GW power, ...) with domain-specific caps

## Prerequisites

- Python 3.10+
- No model credentials needed for the default deterministic demo
- AWS credentials configured for the full-agent mode (`MODEL_MODE=bedrock`)

## Setup

```bash
pip install -r requirements.txt
```

## Usage

Run the deterministic demo (no model calls, runs anywhere):

```bash
python main.py
```

Expected output:

```
[1] OK  Deny    | probe reports speed 4e8 m/s (faster than light)
      reason: physics guard veto: speed=400000000.0 exceeds hard limit 299792458.0
...
totals: 7 evaluated, 5 denied, 0 guided, 2 allowed
```

Run the full-agent demo on Amazon Bedrock:

```bash
export MODEL_MODE=bedrock
python main.py
```

The agent will attempt to launch a probe at 400,000,000 m/s; the intervention handler denies the launch before the tool executes, and the model receives the veto reason.

## How it works

`guardrail.py` re-exports `PhysicsGuard` from the `strands-phm-guard` package. The handler implements the Strands intervention lifecycle: for each tool-call event it evaluates the arguments against the rule table and returns a `Proceed` / `Guide` / `Deny` action, which the framework applies (veto reasons are surfaced back to the model).

Default rule table (extendable via `PhysicsGuard(hard_limits=...)`):

| Quantity | Hard limit |
|---|---|
| speed / velocity | 299,792,458 m/s |
| rpm | 500,000 |
| force_n | 10,000,000 N |
| power_w | 1,000,000,000 W |
| altitude_m | 40,000,000 m |
| depth_m | 12,000 m |

Negative values are forbidden for mass-like quantities; all values must be finite (NaN/inf denied).

## License

This sample is licensed under the Apache-2.0 License. The underlying `strands-phm-guard` package is MIT-licensed.
