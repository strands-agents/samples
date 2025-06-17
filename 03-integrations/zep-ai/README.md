# Zep AI Dining Assistant

Minimal proof-of-concept for a personal dining assistant agent using Zep AI's graph-based memory and the Strands framework.

## Overview
- Demonstrates semantic, episodic, and procedural memory
- Showcases graph memory for user preferences, experiences, and context-aware recommendations
- Integrates mock APIs for calendar and restaurant booking

## Architecture
- **Agent Framework:** Strands
- **Memory:** Zep AI (graph-based)
- **APIs:** Mock calendar, mock booking

## Demo
- Jupyter notebook walks through preference discovery, conflict resolution, memory evolution, and booking
- Visualizes memory graph and agent reasoning

## Requirements
- Python 3.12+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [Zep API key](https://help.getzep.com/quickstart#obtain-an-api-key)

## Getting Started
1. Open a new terminal

2. Copy the `.env.example` file to `.env`:

```bash
cp .env.example .env
```

3. Edit the .env file and add your Zep API key

3. Install the dependencies and run the following command to start the jupyter notebook in a new browser tab:

```bash
uv run --with jupyter jupyter lab
```

This will open a new browser tab with the jupyter notebook on [http://localhost:8888/lab](http://localhost:8888/lab). You can then navigate to the `dining-assistant/zep-dining-assistant.ipynb` notebook.