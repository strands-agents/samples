<h2 align="center">🚀 Strands Agents Samples</h2>
<p align="center">
  👋 Welcome to the <strong>Strands Agents Samples</strong> repository! 👋<br>
  Explore easy-to-use examples to get started with <a href="https://www.strandsagents.com/">Strands Agents</a>.
</p>

> ⚠️ **CAUTION**
> The examples in this repository are for **experimental and educational purposes** only.
> They demonstrate concepts and techniques but are **not intended for direct use in production**.
> Be sure to implement [Amazon Bedrock Guardrails](https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-injection.html) to protect against prompt injection attacks.

---

## 📚 Table of Contents

- [📚 Table of Contents](#-table-of-contents)
- [🏁 Getting Started](#-getting-started)
  - [Step 1: Install Required Packages](#step-1-install-required-packages)
  - [Step 2: Setup Model Provider](#step-2-setup-model-provider)
  - [Step 3: Build Your First Strands Agent](#step-3-build-your-first-strands-agent)
  - [Step 4: Getting Started with the SDK](#step-4-getting-started-with-the-sdk)
  - [Step 5: Explore More Samples](#step-5-explore-more-samples)
- [🔐 Security](#-security)
- [📄 License](#-license)

---

## 🏁 Getting Started

### Step 1: Install Required Packages

```bash
pip install strands-agents
pip install strands-agents-tools
```

### Step 2: Setup Model Provider

Follow the instructions [here](https://strandsagents.com/0.1.x/user-guide/concepts/model-providers/amazon-bedrock/) to configure your model provider.

### Step 3: Build Your First Strands Agent

> ⚠️ **DISCLAIMER**
> This sample uses [Amazon Bedrock](https://aws.amazon.com/bedrock) as the model provider, make sure to enable model access for Anthropic Claude 3.7, follow isntructions [here](https://strandsagents.com/0.1.x/user-guide/concepts/model-providers/amazon-bedrock/).

```python
from strands import Agent, tool
from strands_tools import calculator, current_time, python_repl

@tool
def letter_counter(word: str, letter: str) -> int:
    """
    Count the occurrences of a specific letter in a word.
    """
    if not isinstance(word, str) or not isinstance(letter, str):
        return 0
    if len(letter) != 1:
        raise ValueError("The 'letter' parameter must be a single character")
    return word.lower().count(letter.lower())

agent = Agent(tools=[calculator, current_time, python_repl, letter_counter])

message = """
I have 4 requests:

1. What is the time right now?
2. Calculate 3111696 / 74088
3. Tell me how many letter R's are in the word "strawberry" 🍓
4. Output a script that does what we just spoke about!
   Use your python tools to confirm that the script works before outputting it
"""

agent(message)
```

### Step 4: Getting Started with the SDK

Start with the [01-getting-started](./01-getting-started/) directory.
Create your [first agent](./01-getting-started/00-first-agent/) and explore notebook-based examples covering core functionalities.

### Step 5: Explore More Samples

Looking for inspiration?
Check out more examples in the [02-samples](./02-samples/) folder for real-world use cases.

---

## 🔐 Security

See [CONTRIBUTING.md#security-issue-notifications](CONTRIBUTING.md#security-issue-notifications) for details on reporting security issues.

---

## 📄 License

This project is licensed under the [Apache-2.0 License](LICENSE).

> ⚠️ **IMPORTANT**
> Examples are for **demonstration only**.
> Always apply proper **security** and **testing** procedures before using in production environments.
