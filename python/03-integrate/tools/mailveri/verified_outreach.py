"""Verified outreach agent: Strands Agents + MailVeri.

The agent reads a prospect list, verifies every address with MailVeri, and
drafts a short first-touch email only for addresses that pass the gate.
Nothing is sent. Drafts go to drafts.csv and every decision to
verification_log.csv.

Run:
    uv run verified_outreach.py
    uv run verified_outreach.py --prospects my_prospects.csv
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from strands import Agent
from strands.models import BedrockModel

from mailveri_tools import MailVeriError, MailVeriTools

DEFAULT_MODEL_ID = "us.anthropic.claude-sonnet-4-6"

SYSTEM_PROMPT = """You are an outbound sales assistant for {company}. You write first-touch emails for {sender}.

Rules:
1. Before drafting anything, call verify_emails once with every prospect address.
2. Draft outreach only for addresses whose decision is "send". Save each draft with save_draft.
3. Never draft for "skip" addresses. List "review" addresses for a human with the MailVeri status.
4. If verification stopped (for example no credits left), say so and leave the unchecked prospects alone.
5. Keep each email under 120 words, plain text, one clear question, and use the prospect's hook.
   Sign as {sender}, {company}. Do not invent facts about the prospect.

End with a short summary: drafted, skipped, held for review."""


def _flag(name: str) -> bool:
    return os.getenv(name, "false").strip().lower() in ("1", "true", "yes")


def load_prospects(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = [{k: (v or "").strip() for k, v in row.items()} for row in csv.DictReader(handle)]
    return [row for row in rows if row.get("email")]


def build_prompt(prospects: list[dict[str, str]]) -> str:
    lines = [
        f"- {p['email']} | {p.get('name', '')} | {p.get('company', '')} | hook: {p.get('hook', '')}" for p in prospects
    ]
    return "Prospects (email | name | company | hook):\n" + "\n".join(lines)


def build_agent(mailveri: MailVeriTools) -> Agent:
    model = BedrockModel(model_id=os.getenv("BEDROCK_MODEL_ID", DEFAULT_MODEL_ID))
    prompt = SYSTEM_PROMPT.format(
        sender=os.getenv("SENDER_NAME", "Sam"),
        company=os.getenv("SENDER_COMPANY", "Example Co"),
    )
    return Agent(model=model, system_prompt=prompt, tools=mailveri.tools)


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Verify prospects with MailVeri, then draft outreach.")
    parser.add_argument("--prospects", default="prospects.example.csv", help="CSV with email,name,company,hook")
    args = parser.parse_args()

    prospects = load_prospects(Path(args.prospects))
    if not prospects:
        print(f"No prospects with an email column found in {args.prospects}.")
        return 1

    try:
        mailveri = MailVeriTools(
            api_key=os.getenv("MAILVERI_API_KEY"),
            send_role_accounts=_flag("SEND_ROLE_ACCOUNTS"),
            send_catch_all=_flag("SEND_CATCH_ALL"),
        )
    except MailVeriError as error:
        print(error)
        return 1

    agent = build_agent(mailveri)
    agent(build_prompt(prospects))

    log_path = mailveri.write_log()
    print(f"\n\nDrafts: {mailveri.drafts_path if mailveri.drafts else 'none'} | Log: {log_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
