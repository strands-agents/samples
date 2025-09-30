import ast
import re
from typing import Dict, List, Optional

def normalize_prompt(prompt) -> str:
    if isinstance(prompt, list):
        # assume list of dicts like [{"text": "..."}]
        texts = [p.get("text", "") for p in prompt if isinstance(p, dict)]
        return " ".join(t.strip() for t in texts if t)
    if isinstance(prompt, dict) and "text" in prompt:
        return prompt["text"].strip()
    if isinstance(prompt, str):
        return prompt.strip()
    return str(prompt).strip()


def _unescape_if_escaped(s: str) -> str:
    # Many planner payloads embed '\n' etc. inside single-quoted dicts.
    try:
        return bytes(s, "utf-8").decode("unicode_escape")
    except Exception:
        return s

def extract_original_task(raw: str) -> Optional[str]:
    """
    Extracts the 'Original Task' block.
    """
    m = re.search(
        r"Original Task:\s*(.*?)\s*(?:\n\s*Inputs from previous nodes:|\Z)",
        raw,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if not m:
        return None
    return m.group(1).strip()

def extract_planner_plan_text(raw: str) -> Optional[str]:
    """
    Extracts the plain text of the planner's plan.
    Tries (1) to read from the Agent content['text'] payload,
    falls back to scanning from 'Plan 1:' onward.
    """
    # 1) Try to pull the content['text'] field from the 'From planner' block
    m = re.search(
        r"From planner:.*?'content'\s*:\s*\[\s*\{\s*'text'\s*:\s*'(.*?)'\s*\}\s*\]",
        raw,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if m:
        return _unescape_if_escaped(m.group(1)).strip()

    # 2) Fallback: grab everything starting at "Plan 1:" until the next blank line that
    # does not continue with "Plan X:" (best-effort).
    m = re.search(r"(Plan\s+1:.*)", raw, flags=re.DOTALL | re.IGNORECASE)
    if not m:
        return None
    return m.group(1).strip()

def parse_plan_steps(plan_text: str) -> List[Dict[str, str]]:
    """
    Parses the planner plan text into a list of {plan_no, intent, call} dicts.
    Works with blocks like:

        Plan 1: <intent...>
        #E1 = <tool_name>[args...]

    Multi-line think[...] is preserved inside 'intent' if it sits before #E line.
    """
    steps = []
    # Split into plan blocks by detecting the next "Plan X:"
    for m in re.finditer(r"Plan\s+(\d+):\s*(.*?)(?=\n\s*Plan\s+\d+:|$)", plan_text, flags=re.DOTALL | re.IGNORECASE):
        plan_no = m.group(1)
        block = m.group(2).strip()

        # Separate the intent (text before first #E...) and the call line (first #E...)
        call_match = re.search(r"(#E\d+\s*=\s*.+)", block, flags=re.DOTALL)
        if call_match:
            call = call_match.group(1).strip()
            intent = block[:call_match.start()].strip()
        else:
            call = ""
            intent = block.strip()

        steps.append({
            "plan_no": plan_no,
            "intent": intent,
            "call": call
        })
    return steps

def extract_original_task_and_plan(raw: str) -> Dict[str, object]:
    task = extract_original_task(raw)
    plan_text = extract_planner_plan_text(raw)
    steps = parse_plan_steps(plan_text) if plan_text else []
    return {
        "original_task": task,
        "plan_text": plan_text,
        "plan_steps": steps
    }

