# Tutorial Folder Structure

Guidelines for organizing tutorial folders in `01-tutorials/`. These structures help users quickly understand and navigate tutorials. Use these as guidelines and adapt as needed for your specific learning objectives.

## Naming Convention

- Use lowercase with hyphens: `07-memory-persistent-agents`
- Prefix with number for ordering within category: `01-`, `02-`, etc.
- Be descriptive but concise

## Structure Patterns

### Simple Tutorial (Notebook-Focused)

```
tutorial-name/
├── tutorial-name.ipynb      # Main interactive notebook
├── README.md                 # Overview, prerequisites, instructions
├── requirements.txt          # Python dependencies
└── images/
    └── architecture.png      # Architecture or workflow diagram
```

**Use when:**
- Single-concept demonstration
- Getting started guides
- Minimal external dependencies
- Quick setup and execution

### Standard Tutorial (Notebook + Script)

```
tutorial-name/
├── tutorial-name.ipynb      # Interactive notebook version
├── main.py                   # CLI script version
├── README.md                 # Overview and both execution paths
├── requirements.txt
├── .env.example              # Environment variables template
└── images/
    ├── architecture.png
    └── output-example.png
```

**Use when:**
- Tutorials with both interactive and CLI options
- Moderate complexity
- Users may want to run without Jupyter

### Complex Tutorial (Multi-Component)

```
tutorial-name/
├── README.md                 # Comprehensive guide
├── requirements.txt
├── .env.example              # Environment variables template
│
├── notebooks/                # Interactive notebooks
│   ├── 01-setup.ipynb
│   ├── 02-exploration.ipynb
│   └── 03-advanced.ipynb
│
├── src/                      # Reusable components
│   ├── __init__.py
│   ├── agents/
│   │   ├── __init__.py
│   │   └── agent_name.py
│   └── tools/
│       ├── __init__.py
│       └── custom_tool.py
│
├── scripts/                  # CLI entry points
│   ├── run_demo.py
│   └── run_interactive.py
│
├── infrastructure/           # AWS resource setup (if needed)
│   ├── deploy_prereqs.sh
│   ├── cleanup.sh
│   ├── prereqs_config.yaml
│   └── resources/
│       ├── database.py
│       └── knowledge_base.py
│
├── config/                   # Configuration files
│   └── settings.yaml
│
├── data/                     # Sample data (if needed)
│   └── sample_input.json
│
└── images/
    ├── architecture.png
    └── workflow.png
```

**Use when:**
- Multi-agent systems
- Infrastructure-heavy tutorials
- External service integrations
- Setup/teardown scripts needed
- Progressive learning paths (beginner → advanced)

### Multi-Variant Tutorial

```
02-model-providers/
├── README.md                 # Overview of all variants
│
├── 01-ollama/
│   ├── ollama-agent.ipynb
│   ├── README.md
│   └── requirements.txt
│
├── 02-openai/
│   ├── openai-agent.ipynb
│   ├── README.md
│   └── requirements.txt
│
└── 03-anthropic/
    ├── anthropic-agent.ipynb
    ├── README.md
    └── requirements.txt
```

**Use when:**
- Same concept with different providers/approaches
- Comparing implementation patterns
- Provider-specific configurations

---

## Required Files

| File | Required | Purpose |
|------|----------|---------|
| `README.md` | Yes | Documentation and instructions |
| `requirements.txt` | Yes | Python dependencies |
| `*.ipynb` or `*.py` | Yes | Tutorial code (at least one) |
| `images/` | Recommended | Architecture diagrams |
| `.env.example` | If secrets used | Environment template |

## Images Guidelines

- Store in `images/` subdirectory
- Use PNG format for diagrams
- Keep file sizes reasonable (< 500KB)
- Use descriptive names: `architecture.png`, `workflow.png`, `output-example.png`

## Dependencies

In `requirements.txt`:
- Pin major versions: `strands-agents>=0.1.0`
- Include all direct dependencies
- Add comments for non-obvious packages

Example:
```
strands-agents>=0.1.0
strands-agents-tools>=0.1.0
boto3>=1.28.0
python-dotenv>=1.0.0  # For .env file loading
```

