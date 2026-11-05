#!/usr/bin/env python3
"""
Publish to the Web - deed.page Tool Sample

A Strands agent that writes a self-contained HTML page (a report, a one-pager,
a status update) and publishes it to a public HTTPS URL with deed.page, so the
answer is a link people can open instead of a file on the agent's machine.

What it shows:
- A custom @tool that wraps an HTTP API and keeps the credential out of the
  model's context (the API token is stored on disk, never returned to the agent)
- Letting the agent decide when its output is ready to publish
- Optional expiry (ttl_seconds) for pages that are only needed for a while
- Cleanup outside the agent loop (--delete), so the model cannot delete pages

Prerequisites:
    - AWS credentials configured for Amazon Bedrock access (agent mode only)
    - No deed.page account or API key: the first publish returns a token, which
      this sample saves to ~/.config/deed-page/token (mode 600) and reuses

Usage:
    python publish_agent.py "Write a one-page brief on the history of the bicycle"
    python publish_agent.py --ttl 3600 "Summarize the Strands agent loop as a cheat sheet"
    python publish_agent.py --no-llm              # publish a sample page, no model call
    python publish_agent.py --delete <slug>       # delete a page you published
"""

import argparse
import json
import os
import re
import secrets
import sys
import urllib.error
import urllib.request
from pathlib import Path

API_URL = "https://deed.page/v1/sites"
TOKEN_FILE = Path(os.environ.get("DEEDPAGE_TOKEN_FILE", Path.home() / ".config" / "deed-page" / "token"))
SLUG_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
CLIENT_NAME = "strands-samples"

SYSTEM_PROMPT = """You write short, well-structured web pages and publish them.

When the user asks for a page, report, brief or summary:
1. Write one complete, self-contained HTML document: inline CSS only, no external
   scripts, fonts or images, readable on a phone.
2. Call publish_page once with the HTML and a short descriptive slug.
3. Reply with the URL from the tool result and one sentence about what is on the page.

Never put secrets, API keys or personal data in a page: anyone with the URL can read it."""


def load_token() -> str | None:
    """Return the deed.page token from DEEDPAGE_TOKEN or the token file, if any."""
    token = os.environ.get("DEEDPAGE_TOKEN", "").strip()
    if token:
        return token
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text().strip() or None
    return None


def save_token(token: str) -> None:
    """Store a newly issued token with owner-only permissions."""
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(TOKEN_FILE.parent, 0o700)
    fd = os.open(TOKEN_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(token)


def make_slug(hint: str) -> str:
    """Turn a free-form hint into a valid slug with a random suffix."""
    base = re.sub(r"[^a-z0-9]+", "-", hint.lower()).strip("-")[:40].strip("-") or "page"
    slug = f"{base}-{secrets.token_hex(3)}"
    if not SLUG_RE.match(slug):
        raise ValueError(f"could not build a valid slug from {hint!r}")
    return slug


def call_api(method: str, url: str, payload: dict | None = None, ttl_seconds: int = 0) -> dict:
    """Send one request to the deed.page API and return the decoded JSON body."""
    headers = {"X-Client": CLIENT_NAME, "Accept": "application/json"}
    token = load_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if ttl_seconds:
        headers["X-Ttl"] = str(ttl_seconds)
    data = None
    if payload is not None:
        data = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"
    if not url.startswith(API_URL):
        raise ValueError(f"refusing to call a URL outside {API_URL}: {url}")
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        # Only https://deed.page/v1/sites URLs reach this point (checked above).
        with urllib.request.urlopen(request, timeout=30) as response:  # nosec B310
            return json.loads(response.read() or b"{}")
    except urllib.error.HTTPError as err:
        body = err.read().decode(errors="replace")
        try:
            detail = json.loads(body)
            message = detail.get("user_message") or detail.get("message") or body
        except ValueError:
            message = body
        raise RuntimeError(f"deed.page returned HTTP {err.code}: {message}") from None


def publish_html(html: str, slug_hint: str = "", ttl_seconds: int = 0) -> dict:
    """Publish one HTML document as index.html. Returns url, slug, version, expires_at."""
    slug = make_slug(slug_hint or "page")
    result = call_api("PUT", API_URL + "?slug=" + slug, {"files": {"index.html": html}}, ttl_seconds)
    new_token = result.pop("token", None)
    if new_token:
        save_token(new_token)
    return {k: result.get(k) for k in ("url", "slug", "version", "expires_at")}


def delete_site(slug: str) -> dict:
    """Delete a page published with the saved token."""
    if not SLUG_RE.match(slug):
        raise ValueError(f"invalid slug: {slug!r}")
    if not load_token():
        raise RuntimeError(f"no token found in DEEDPAGE_TOKEN or {TOKEN_FILE}")
    return call_api("DELETE", f"{API_URL}/{slug}")


def build_agent(ttl_seconds: int):
    from strands import Agent, tool
    from strands.models.bedrock import BedrockModel

    @tool
    def publish_page(html: str, slug: str = "") -> str:
        """Publish a complete HTML document to a public HTTPS URL and return the URL.

        Args:
            html: The full HTML document (it becomes index.html of the site).
            slug: Short lowercase name for the URL, e.g. "bicycle-history". A random
                suffix is added so the URL is not guessable.
        """
        info = publish_html(html, slug, ttl_seconds)
        expiry = f", expires {info['expires_at']}" if info.get("expires_at") else ""
        return f"Published {info['url']} (slug {info['slug']}, {info['version']}{expiry})"

    model = BedrockModel(model_id=os.environ.get("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-6"))
    return Agent(model=model, system_prompt=SYSTEM_PROMPT, tools=[publish_page])


SAMPLE_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Published from a Strands sample</title>
<style>body{font-family:system-ui,sans-serif;max-width:40rem;margin:3rem auto;padding:0 1rem;line-height:1.5}</style>
</head><body>
<h1>Hello from Strands Agents</h1>
<p>This page was published by <code>publish_agent.py --no-llm</code>.</p>
</body></html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("prompt", nargs="*", help="what the agent should write and publish")
    parser.add_argument("--ttl", type=int, default=0, help="expire the page after this many seconds")
    parser.add_argument("--no-llm", action="store_true", help="publish a built-in sample page without calling a model")
    parser.add_argument("--delete", metavar="SLUG", help="delete a page published with the saved token")
    args = parser.parse_args()

    if args.delete:
        print(json.dumps(delete_site(args.delete)))
        return 0
    if args.no_llm:
        print(json.dumps(publish_html(SAMPLE_PAGE, "strands-sample", args.ttl), indent=2))
        return 0

    prompt = " ".join(args.prompt) or "Write a one-page brief on the history of the bicycle and publish it."
    agent = build_agent(args.ttl)
    agent(prompt)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
