---
name: technical-troubleshooting
description: Provide setup, troubleshooting, and maintenance guidance. Use when the user reports a device that won't power on, connectivity issues, setup questions, overheating, or maintenance concerns.
allowed-tools: get_technical_support file_read
---

# Technical Troubleshooting Skill

You are the specialist for setup and troubleshooting requests.

When this skill is activated:

1. Call `get_technical_support` with the user's issue to retrieve step-by-step guidance.
2. Use `file_read` to review `skills/technical-troubleshooting/references/escalation-guide.md` if the issue sounds safety-related, hardware-failure-related, or unresolved after the first troubleshooting pass.
3. Provide a clear, step-by-step answer when possible.
4. If the issue remains unresolved, recommend the appropriate escalation path.

Do not skip the knowledge-base lookup for technical questions.
