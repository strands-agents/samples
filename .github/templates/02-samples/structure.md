# Sample Project Structure Guide

Recommended directory structures for samples in `02-samples`. These structures help users quickly understand and navigate samples. Use these as guidelines and adapt as needed for your specific use case.

## Python Scripts-Based Samples

#### Basic Use Case Structure
```
sample-name/
├── main.py or sample_name.py        # Main agent/application entry point
├── requirements.txt                 # Python dependencies
├── README.md                        # Sample overview and setup
├── images/                          # Architecture diagrams
│   └── architecture.png
└── .env.example                     # Environment variables template
```

**Use when:**
- Single focused problem to solve
- Minimal external dependencies
- Self-contained demonstration
- Quick setup and execution

#### Complex Use Case Structure
```
sample-name/
├── main.py or sample_name.py        # Main orchestrator/entry point
├── requirements.txt or pyproject.toml
├── README.md                        # Comprehensive documentation
├── .env.example                     # Environment variables template
├── images/                          # Architecture diagrams
│   ├── architecture.png
│   └── agent_flow.png
├── src/                             # Source code modules
│   ├── __init__.py
│   ├── agents/                      # Multiple agent implementations
│   │   ├── __init__.py
│   │   ├── coordinator_agent.py
│   │   ├── specialist_agent_1.py
│   │   └── specialist_agent_2.py
│   ├── tools/                       # Custom tools
│   │   ├── __init__.py
│   │   ├── tool_category_1/
│   │   │   ├── __init__.py
│   │   │   └── specific_tool.py
│   │   └── tool_category_2/
│   │       ├── __init__.py
│   │       └── another_tool.py
│   └── utils/                       # Utilities and helpers
│       ├── __init__.py
│       ├── constants.py
│       └── helpers.py
├── infrastructure/                  # External service setup
│   ├── deploy_prereqs.sh
│   ├── cleanup.sh
│   ├── prereqs_config.yaml
│   └── resources/                   # Resource provisioning scripts
│       ├── database.py
│       ├── storage.py
│       └── knowledge_base.py
├── config/                          # Configuration files
│   └── settings.yaml
└── data/                            # Sample and test data
    ├── sample_inputs/
    └── test_data/
```

**Use when:**
- Multi-faceted problem requiring orchestration
- Multiple specialized components or tools
- Production-ready patterns
- External service integrations (databases, APIs, etc.)
- Setup/teardown scripts needed for the use case

---

## Jupyter Notebook-Based Samples

#### Tutorial Walkthrough Structure
```
sample-name/
├── sample-name.ipynb                # Single notebook
   OR
├── part1-topic.ipynb                # Multiple sequential notebooks
├── part2-topic.ipynb
├── part3-topic.ipynb
├── shared_utils.py                  # Optional: shared code across notebooks
├── requirements.txt                 # Python dependencies
├── README.md                        # Quick start and overview
├── images/                          # Architecture diagrams
│   └── architecture.png
└── .env.example                     # Environment variables template
```

**Use when:**
- Educational and learning focused
- Step-by-step concept demonstration
- Interactive exploration and experimentation
- Minimal external setup required
- Tools and agents defined inline
- Single notebook for focused learning OR multiple notebooks for progressive learning path (beginner → advanced)

#### End-to-End Solution Structure
```
sample-name/
├── sample-name.ipynb                # Main tutorial notebook
├── notebooks/                       # Optional: additional notebooks for setup/exploration
│   ├── 01_data_prep.ipynb
│   └── 02_advanced_setup.ipynb
├── requirements.txt                 # Python dependencies
├── README.md                        # Setup guide and overview
├── .env.example                     # Environment variables template
├── images/                          # Architecture diagrams
│   ├── architecture.png
│   └── workflow.png
├── src/                             # External source code
│   ├── __init__.py
│   ├── agents/                      # Agent implementations
│   │   ├── __init__.py
│   │   └── specialized_agent.py
│   ├── tools/                       # Custom tool implementations
│   │   ├── __init__.py
│   │   ├── tool_1.py
│   │   └── tool_2.py
│   └── utils/                       # Helper functions
│       ├── __init__.py
│       └── helpers.py
├── infrastructure/                  # External service setup
│   ├── deploy_prereqs.sh
│   ├── cleanup.sh
│   ├── prereqs_config.yaml
│   └── resources/                   # Resource provisioning scripts
│       ├── database.py
│       ├── storage.py
│       └── knowledge_base.py
├── config/                          # Configuration files
│   └── settings.yaml
└── data/                            # Sample data
    └── sample_input.json
```

**Use when:**
- Complete working solution demonstration
- Real-world integration points (databases, APIs, external services)
- Reusable modular components (external src/ directory)
- Setup/teardown scripts needed for the use case
- Data preprocessing or configuration required
- May include additional notebooks for data prep, setup, or exploration tasks

---
