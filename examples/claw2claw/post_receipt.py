"""Optional demo: post a simple claw2claw receipt.

Requires:
  export CLAW2CLAW_API_KEY=...

This is deliberately tiny and side-effect free for the repo: it only runs if invoked.
"""

import os
import json
import time
import urllib.request

API = "https://claw2claw.com/api"


def post_json(path: str, body: dict) -> dict:
    req = urllib.request.Request(
        API + path,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "content-type": "application/json",
            "authorization": f"Bearer {os.environ[CLAW2CLAW_API_KEY]}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def main():
    ts = int(time.time())
    seller_bot_id = os.getenv("SELLER_BOT_ID", "bot_strands_demo")

    offer = post_json(
        "/offers",
        {
            "sellerBotId": seller_bot_id,
            "title": "Strands demo: summarize a text",
            "description": "Optional demo offer that produces a claw2claw receipt.",
            "price": {"currency": "USD", "amount": 1},
            "capabilities": ["summarize"],
        },
    )

    job = post_json(
        "/jobs",
        {
            "buyerBotId": "bot_strands_buyer_demo",
            "offerId": offer["offerId"],
            "inputs": {"text": "Hello from Strands. Summarize this sentence."},
            "idempotencyKey": f"strands-demo-{ts}",
        },
    )

    receipt = post_json(
        "/receipts",
        {
            "jobId": job["jobId"],
            "sellerBotId": seller_bot_id,
            "status": "ok",
            "summary": "Summarized text.",
            "artifacts": [
                {
                    "name": "summary.md",
                    "contentType": "text/markdown",
                    "sha256": "sha256:__REPLACED_BY_SERVER__",
                    "bodyBase64": "IyBTdHJhbmRzIGRlbW8KCi0gU3VtbWFyeTogSGVsbG8gZnJvbSBTdHJhbmRzLgo=",
                }
            ],
        },
    )

    rid = receipt.get("receiptId")
    print("receiptId:", rid)
    if rid:
        print("proof:", f"https://claw2claw.com/p/?receiptId={rid}")


if __name__ == "__main__":
    if "CLAW2CLAW_API_KEY" not in os.environ:
        raise SystemExit("Missing env: CLAW2CLAW_API_KEY")
    main()
