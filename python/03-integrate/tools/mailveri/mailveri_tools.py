"""MailVeri email verification tools for Strands Agents.

The tools call the public MailVeri REST API (https://mailveri.com/docs/):

    POST /v1/verify-mail/   verify one address in real time (1 credit)
    GET  /v1/get-balance/   read the credit balance (no credits)

The outreach gate lives in code, not in the prompt: ``save_draft`` refuses any
address that was not verified in this run with a "send" decision, so the model
cannot draft outreach to an unverified or risky address.
"""

from __future__ import annotations

import csv
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from strands import tool

BASE_URL = "https://api.mailveri.com"
TIMEOUT_SECONDS = 30.0
USER_AGENT = "strands-samples-mailveri/0.1.0"

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Single verification is documented at 10 requests/second.
PAUSE_SECONDS = 0.15
MAX_EMAILS_PER_CALL = 50

SEND = "send"
SKIP = "skip"
REVIEW = "review"

# VALID is the only status sent by default. Hard failures are skipped, and
# addresses the API cannot confirm are held for a human to review.
SKIP_STATUSES = frozenset({"INVALID", "DISPOSABLE", "FULL_INBOX"})

STATUS_MESSAGES = {
    401: "MailVeri rejected the API key. Create a new key in the MailVeri dashboard under API Keys.",
    403: "This MailVeri API key is not allowed to do this. Check the key in the MailVeri dashboard.",
    404: "MailVeri could not find the requested resource.",
    429: "MailVeri rate limit reached. Wait a moment and try again.",
}


class MailVeriError(ValueError):
    """Input or API failure with a message that is safe to show to users and models."""


class InsufficientCreditsError(MailVeriError):
    """The account has no credits left (API error code 2)."""


def _clean(value: Any, max_len: int = 300) -> str:
    if not isinstance(value, str):
        return ""
    text = " ".join(value.split())
    return text if len(text) <= max_len else text[: max_len - 3] + "..."


def normalize_email(value: Any) -> str:
    email = str(value or "").strip().strip("<>\"'")
    if not email or len(email) > 320 or not EMAIL_RE.fullmatch(email):
        raise MailVeriError(f"'{_clean(email, 80)}' is not a valid email address.")
    return email.lower()


def decide(status: str, send_role_accounts: bool = False, send_catch_all: bool = False) -> str:
    """Map a MailVeri status to send, skip or review."""
    if status == "VALID":
        return SEND
    if status in SKIP_STATUSES:
        return SKIP
    if status == "ROLE_ACCOUNT" and send_role_accounts:
        return SEND
    if status == "CATCH_ALL" and send_catch_all:
        return SEND
    return REVIEW


class MailVeriClient:
    """Small synchronous client for the MailVeri REST API."""

    def __init__(self, api_key: Any, transport: httpx.BaseTransport | None = None):
        key = str(api_key or "").strip()
        if not key:
            raise MailVeriError("Missing MAILVERI_API_KEY. Create one in the MailVeri dashboard under API Keys.")
        self._api_key = key
        self._transport = transport

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        }
        try:
            with httpx.Client(
                base_url=BASE_URL,
                timeout=TIMEOUT_SECONDS,
                follow_redirects=False,
                transport=self._transport,
            ) as http:
                response = http.request(method, path, headers=headers, **kwargs)
        except httpx.TimeoutException:
            raise MailVeriError("MailVeri did not respond within 30 seconds. Try again.") from None
        except httpx.HTTPError:
            raise MailVeriError("Could not connect to MailVeri. Check the network and try again.") from None

        if response.status_code in STATUS_MESSAGES:
            raise MailVeriError(STATUS_MESSAGES[response.status_code])

        try:
            data = response.json()
        except ValueError:
            raise MailVeriError(f"MailVeri returned an unexpected response (HTTP {response.status_code}).") from None
        if not isinstance(data, dict):
            raise MailVeriError(f"MailVeri returned an unexpected response (HTTP {response.status_code}).")

        error = data.get("error", 0)
        if error == 2:
            raise InsufficientCreditsError(
                _clean(data.get("message")) or "Not enough MailVeri credits. Add credits in the MailVeri dashboard."
            )
        if error not in (0, None) or response.status_code >= 400:
            raise MailVeriError(
                _clean(data.get("message")) or f"MailVeri request failed (HTTP {response.status_code})."
            )
        return data

    def get_balance(self) -> dict[str, Any]:
        """GET /v1/get-balance/ - read-only, costs no credits."""
        data = self._request("GET", "/v1/get-balance/")
        return {"balance": data.get("balance"), "message": _clean(data.get("message"))}

    def verify_email(self, email: str) -> dict[str, Any]:
        """POST /v1/verify-mail/ - verify one address in real time."""
        data = self._request("POST", "/v1/verify-mail/", json={"email": email})
        return {
            "email": email,
            "status": str(data.get("status") or "UNKNOWN").upper(),
            "balance": data.get("balance"),
        }


class MailVeriTools:
    """Strands tools that share one verification log for the current run.

    Pass the bound tools to an agent:

        mailveri = MailVeriTools(api_key=os.environ["MAILVERI_API_KEY"])
        agent = Agent(tools=mailveri.tools)
    """

    def __init__(
        self,
        api_key: Any,
        drafts_path: str | Path = "drafts.csv",
        send_role_accounts: bool = False,
        send_catch_all: bool = False,
        pause_seconds: float = PAUSE_SECONDS,
        transport: httpx.BaseTransport | None = None,
    ):
        self.client = MailVeriClient(api_key, transport=transport)
        self.drafts_path = Path(drafts_path)
        self.send_role_accounts = send_role_accounts
        self.send_catch_all = send_catch_all
        self.pause_seconds = pause_seconds
        self.results: dict[str, dict[str, Any]] = {}
        self.drafts: list[dict[str, str]] = []

    @property
    def tools(self) -> list[Any]:
        return [self.verify_emails, self.get_credit_balance, self.save_draft]

    def _verify_one(self, email: str) -> dict[str, Any]:
        result = self.client.verify_email(email)
        result["decision"] = decide(result["status"], self.send_role_accounts, self.send_catch_all)
        result["verified_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.results[email] = result
        return result

    @tool
    def verify_emails(self, emails: list[str]) -> dict[str, Any]:
        """Verify prospect email addresses with MailVeri before any outreach is drafted.

        Each address gets a MailVeri status and a decision: "send" (draft outreach),
        "skip" (do not contact) or "review" (a human must decide). Each check uses
        one MailVeri credit.

        Args:
            emails: Email addresses to verify, up to 50 per call.
        """
        cleaned: list[str] = []
        invalid: list[str] = []
        for raw in emails:
            try:
                email = normalize_email(raw)
            except MailVeriError:
                invalid.append(_clean(str(raw), 80))
                continue
            if email not in cleaned:
                cleaned.append(email)
        if len(cleaned) > MAX_EMAILS_PER_CALL:
            return {
                "status": "error",
                "content": [{"text": f"Send at most {MAX_EMAILS_PER_CALL} addresses per call (got {len(cleaned)})."}],
            }

        results: list[dict[str, Any]] = []
        unchecked: list[str] = []
        stopped = ""
        for index, email in enumerate(cleaned):
            if email in self.results:
                results.append(self.results[email])
                continue
            if index and self.pause_seconds:
                time.sleep(self.pause_seconds)
            try:
                results.append(self._verify_one(email))
            except InsufficientCreditsError as error:
                stopped = str(error)
                unchecked = cleaned[index:]
                break
            except MailVeriError as error:
                if error.args and error.args[0] in STATUS_MESSAGES.values():
                    stopped = str(error)
                    unchecked = cleaned[index:]
                    break
                results.append({"email": email, "status": "ERROR", "decision": REVIEW, "error": str(error)})

        summary: dict[str, Any] = {
            "results": [{k: r.get(k) for k in ("email", "status", "decision", "error") if r.get(k)} for r in results],
            "send": [r["email"] for r in results if r["decision"] == SEND],
            "skip": [r["email"] for r in results if r["decision"] == SKIP],
            "review": [r["email"] for r in results if r["decision"] == REVIEW],
        }
        if invalid:
            summary["not_an_email"] = invalid
        if stopped:
            summary["stopped"] = stopped
            summary["unchecked"] = unchecked
        balances = [r.get("balance") for r in results if r.get("balance") is not None]
        if balances:
            summary["credits_left"] = balances[-1]
        return summary

    @tool
    def get_credit_balance(self) -> dict[str, Any]:
        """Read the MailVeri credit balance. This check is free and changes nothing."""
        try:
            return self.client.get_balance()
        except MailVeriError as error:
            return {"status": "error", "content": [{"text": str(error)}]}

    @tool
    def save_draft(self, email: str, subject: str, body: str) -> dict[str, Any]:
        """Save a first-touch outreach draft for one prospect. Nothing is sent.

        Only works for addresses that verify_emails returned with decision "send".

        Args:
            email: The prospect's email address.
            subject: Email subject line, under 80 characters.
            body: Plain-text email body, under 120 words.
        """
        try:
            address = normalize_email(email)
        except MailVeriError as error:
            return {"status": "error", "content": [{"text": str(error)}]}
        result = self.results.get(address)
        if result is None:
            return {"status": "error", "content": [{"text": f"{address} was not verified. Call verify_emails first."}]}
        if result["decision"] != SEND:
            reason = f"{address} is {result['status']} (decision: {result['decision']}). Do not draft outreach."
            return {"status": "error", "content": [{"text": reason}]}

        draft = {
            "email": address,
            "mailveri_status": result["status"],
            "subject": _clean(subject, 200),
            "body": str(body).strip(),
        }
        self.drafts = [d for d in self.drafts if d["email"] != address] + [draft]
        self._write_drafts()
        return {"saved": address, "drafts_file": str(self.drafts_path)}

    def _write_drafts(self) -> None:
        with self.drafts_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["email", "mailveri_status", "subject", "body"])
            writer.writeheader()
            writer.writerows(self.drafts)

    def write_log(self, path: str | Path = "verification_log.csv") -> Path:
        """Write every verification result and decision from this run."""
        target = Path(path)
        drafted = {d["email"] for d in self.drafts}
        with target.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["email", "status", "decision", "drafted", "verified_at"])
            writer.writeheader()
            for email, result in self.results.items():
                writer.writerow(
                    {
                        "email": email,
                        "status": result["status"],
                        "decision": result["decision"],
                        "drafted": "yes" if email in drafted else "no",
                        "verified_at": result.get("verified_at", ""),
                    }
                )
        return target
