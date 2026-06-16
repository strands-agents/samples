"""Run the agent on a cron schedule - fire-and-forget automation.

Usage:
    pip install schedule
    python scheduler.py
"""
import os
from datetime import datetime
from pathlib import Path

import schedule
import time

from agent import make_agent

JOURNAL = Path("journal.md")


def log(text: str):
    JOURNAL.write_text(
        (JOURNAL.read_text() if JOURNAL.exists() else "")
        + f"\n\n## {datetime.now().isoformat(timespec='seconds')}\n{text}\n"
    )


def job():
    print(f"\n[scheduler] firing at {datetime.now():%H:%M:%S}")
    agent = make_agent()
    result = agent(
        "Spend 30 seconds researching any Bedrock or AgentCore news. "
        "Summarize the most interesting item in one paragraph."
    )
    log(str(result))


def main():
    # Run every 5 minutes in production; 1 min is fine for workshop demo
    interval = int(os.environ.get("AIM308_SCHEDULE_MIN", "5"))
    print(f"🗓  Scheduler: firing every {interval} min. Journal → {JOURNAL}")
    schedule.every(interval).minutes.do(job)
    job()  # run once immediately
    while True:
        schedule.run_pending()
        time.sleep(15)


if __name__ == "__main__":
    main()
