"""Tests for the MailVeri tools. All HTTP traffic is mocked with respx."""

from __future__ import annotations

import csv
import json

import httpx
import pytest
import respx
from strands import Agent

import verified_outreach
from mailveri_tools import BASE_URL, MailVeriError, MailVeriTools, decide

VERIFY_URL = f"{BASE_URL}/v1/verify-mail/"
BALANCE_URL = f"{BASE_URL}/v1/get-balance/"

STATUSES = {
    "valid@example.com": "VALID",
    "bad@example.com": "INVALID",
    "temp@example.com": "DISPOSABLE",
    "info@example.com": "ROLE_ACCOUNT",
    "any@example.com": "CATCH_ALL",
}


def verify_handler(request: httpx.Request) -> httpx.Response:
    email = json.loads(request.content)["email"]
    return httpx.Response(
        200, json={"error": 0, "status": STATUSES.get(email, "UNKNOWN"), "email": email, "balance": 99}
    )


@pytest.fixture
def tools(tmp_path):
    return MailVeriTools(api_key="test-key", drafts_path=tmp_path / "drafts.csv", pause_seconds=0)


def test_missing_key_raises():
    with pytest.raises(MailVeriError):
        MailVeriTools(api_key="")


@pytest.mark.parametrize(
    ("status", "role", "catch_all", "expected"),
    [
        ("VALID", False, False, "send"),
        ("INVALID", False, False, "skip"),
        ("DISPOSABLE", False, False, "skip"),
        ("FULL_INBOX", False, False, "skip"),
        ("ROLE_ACCOUNT", False, False, "review"),
        ("ROLE_ACCOUNT", True, False, "send"),
        ("CATCH_ALL", False, False, "review"),
        ("CATCH_ALL", False, True, "send"),
        ("UNKNOWN", True, True, "review"),
    ],
)
def test_decide(status, role, catch_all, expected):
    assert decide(status, role, catch_all) == expected


@respx.mock
def test_verify_emails_splits_decisions_and_sends_bearer(tools):
    route = respx.post(VERIFY_URL).mock(side_effect=verify_handler)
    result = tools.verify_emails(list(STATUSES) + ["not-an-email", "VALID@example.com"])

    assert result["send"] == ["valid@example.com"]
    assert result["skip"] == ["bad@example.com", "temp@example.com"]
    assert result["review"] == ["info@example.com", "any@example.com"]
    assert result["not_an_email"] == ["not-an-email"]
    assert result["credits_left"] == 99
    assert route.call_count == 5  # duplicates and bad input are not sent
    assert route.calls[0].request.headers["Authorization"] == "Bearer test-key"


@respx.mock
def test_out_of_credits_stops_and_returns_unchecked(tools):
    respx.post(VERIFY_URL).mock(
        side_effect=[
            httpx.Response(200, json={"error": 0, "status": "VALID", "balance": 0}),
            httpx.Response(200, json={"error": 2, "message": "Insufficient credits"}),
        ]
    )
    result = tools.verify_emails(["a@example.com", "b@example.com", "c@example.com"])
    assert result["send"] == ["a@example.com"]
    assert result["stopped"] == "Insufficient credits"
    assert result["unchecked"] == ["b@example.com", "c@example.com"]


@respx.mock
def test_bad_key_stops_without_leaking_key(tools):
    respx.post(VERIFY_URL).mock(return_value=httpx.Response(401, json={"detail": "bad"}))
    result = tools.verify_emails(["a@example.com"])
    assert "rejected the API key" in result["stopped"]
    assert "test-key" not in str(result)


@respx.mock
def test_network_error_marks_review(tools):
    respx.post(VERIFY_URL).mock(side_effect=httpx.ConnectError("boom"))
    result = tools.verify_emails(["a@example.com"])
    assert result["review"] == ["a@example.com"]
    assert result["results"][0]["status"] == "ERROR"


def test_too_many_emails(tools):
    result = tools.verify_emails([f"user{i}@example.com" for i in range(51)])
    assert result["status"] == "error"


@respx.mock
def test_save_draft_gate(tools):
    respx.post(VERIFY_URL).mock(side_effect=verify_handler)
    tools.verify_emails(["valid@example.com", "bad@example.com", "info@example.com"])

    assert tools.save_draft("never@example.com", "Hi", "Body")["status"] == "error"
    assert "INVALID" in tools.save_draft("bad@example.com", "Hi", "Body")["content"][0]["text"]
    assert "review" in tools.save_draft("info@example.com", "Hi", "Body")["content"][0]["text"]

    saved = tools.save_draft("Valid@Example.com", "Quick question", "Hi Jane, ...")
    assert saved["saved"] == "valid@example.com"
    with tools.drafts_path.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows == [
        {"email": "valid@example.com", "mailveri_status": "VALID", "subject": "Quick question", "body": "Hi Jane, ..."}
    ]

    log = tools.write_log(tools.drafts_path.parent / "log.csv")
    with log.open(encoding="utf-8") as handle:
        drafted = {row["email"]: row["drafted"] for row in csv.DictReader(handle)}
    assert drafted == {"valid@example.com": "yes", "bad@example.com": "no", "info@example.com": "no"}


@respx.mock
def test_get_credit_balance(tools):
    respx.get(BALANCE_URL).mock(return_value=httpx.Response(200, json={"error": 0, "balance": 1234, "message": "ok"}))
    assert tools.get_credit_balance()["balance"] == 1234


def test_tools_register_with_strands_agent(tools, monkeypatch):
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    agent = Agent(tools=tools.tools, callback_handler=None)
    assert set(agent.tool_names) == {"verify_emails", "get_credit_balance", "save_draft"}
    spec = tools.verify_emails.tool_spec
    assert spec["inputSchema"]["json"]["required"] == ["emails"]


@respx.mock
def test_direct_tool_call_through_agent(tools, monkeypatch):
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    respx.post(VERIFY_URL).mock(side_effect=verify_handler)
    agent = Agent(tools=tools.tools, callback_handler=None)
    result = agent.tool.verify_emails(emails=["valid@example.com"], record_direct_tool_call=False)
    assert result["status"] == "success"
    assert '"send": ["valid@example.com"]' in result["content"][0]["text"]


def test_build_prompt_and_agent(monkeypatch):
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    prospects = verified_outreach.load_prospects(verified_outreach.Path("prospects.example.csv"))
    assert len(prospects) == 3
    assert "jane.doe@example.com" in verified_outreach.build_prompt(prospects)
    agent = verified_outreach.build_agent(MailVeriTools(api_key="test-key"))
    assert agent.model.config["model_id"] == verified_outreach.DEFAULT_MODEL_ID
