# Strands Research Agent

[![Powered by Strands Agents](https://img.shields.io/badge/Powered%20by-Strands%20Agents-blue)](https://strandsagents.com)
[![PyPI - Version](https://img.shields.io/pypi/v/strands-research-agent)](https://pypi.org/project/strands-research-agent/)
[![Python Version](https://img.shields.io/pypi/pyversions/strands-research-agent)](https://pypi.org/project/strands-research-agent/)

Autonomous research agent demonstrating advanced Strands Agents patterns including hot-reloading tools, multi-agent coordination, and persistent learning systems for enterprise research automation.

## Feature Overview

- **Hot-Reloading Development**: Create and modify tools without restarting - save `.py` files in `./tools/` for instant availability
- **Multi-Agent Orchestration**: Background tasks, parallel processing, and model coordination across different providers
- **Persistent Learning**: Cross-session knowledge accumulation via AWS Bedrock Knowledge Base and SQLite memory
- **Self-Modifying Systems**: Dynamic behavior adaptation through the `system_prompt` tool and continuous improvement loops

```mermaid
graph LR
    subgraph TRADITIONAL["❌ Traditional Development (Minutes/Hours)"]
        A["🔧 Modify Tool"] --> B["🔄 Restart Agent"]
        B --> C["🧪 Test Change"]
        C --> D["🐛 Debug Issues"]
        D --> A
    end
    
    subgraph HOTRELOAD["✅ Hot-Reload Development (Seconds)"]
        E["💾 Save .py to ./tools/"] --> F["⚡ Instant Loading"]
        F --> G["🚀 Agent Uses Tool"]
        G --> H["🔬 Refine & Test"]
        H --> E
    end
    
    TRADITIONAL -.->|"Strands Research Agent"| HOTRELOAD
    
    style A fill:#ffcdd2,stroke:#d32f2f,stroke-width:2px,color:#000
    style B fill:#ffcdd2,stroke:#d32f2f,stroke-width:2px,color:#000
    style C fill:#ffcdd2,stroke:#d32f2f,stroke-width:2px,color:#000
    style D fill:#ffcdd2,stroke:#d32f2f,stroke-width:2px,color:#000
    
    style E fill:#c8e6c9,stroke:#388e3c,stroke-width:2px,color:#000
    style F fill:#81c784,stroke:#388e3c,stroke-width:3px,color:#000
    style G fill:#c8e6c9,stroke:#388e3c,stroke-width:2px,color:#000
    style H fill:#c8e6c9,stroke:#388e3c,stroke-width:2px,color:#000
    
    style TRADITIONAL fill:#ffebee,stroke:#d32f2f,stroke-width:2px
    style HOTRELOAD fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
```

## Quick Start

```bash
# Install the research agent
pip install strands-research-agent[all]

# Configure your model (Bedrock recommended)
export STRANDS_MODEL_ID="us.anthropic.claude-sonnet-4-20250514-v1:0"
export MODEL_PROVIDER="bedrock"

# Start interactive research
research-agent
```

```python
# Agent creates its own tools and uses them immediately
agent("Create tools for competitive intelligence analysis and start researching AI agent frameworks")

# What happens behind the scenes:
# 1. Agent recognizes it needs specialized capabilities
# 2. Creates competitive_intel.py in ./tools/ (hot-loaded instantly)
# 3. Tool becomes available as agent.tool.competitive_intel()
# 4. Agent begins research using its newly created tool
# 5. Stores findings in knowledge base for future sessions
# 
# This is tool creation at the speed of thought - no restart, no manual coding
```

## Installation

Ensure you have Python 3.10+ installed, then:

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate

# Install from PyPI
pip install strands-research-agent[all]

# Or clone for development
git clone https://github.com/strands-agents/samples.git
cd samples/02-samples/14-research-agent
pip install -e .[dev]
```

**Configuration:**

```bash
# Core configuration
export STRANDS_MODEL_ID="us.anthropic.claude-sonnet-4-20250514-v1:0"
export MODEL_PROVIDER="bedrock"

# Optional - for persistent learning
export STRANDS_KNOWLEDGE_BASE_ID="your_kb_id"
export AWS_REGION="us-west-2"
```

**🚀 Recommended Settings for Optimal Performance:**

```bash
# Maximum performance settings for production research workloads
export STRANDS_MODEL_ID="us.anthropic.claude-sonnet-4-20250514-v1:0"
export STRANDS_ADDITIONAL_REQUEST_FIELDS='{"anthropic_beta": ["interleaved-thinking-2025-05-14", "context-1m-2025-08-07"], "thinking": {"type": "enabled", "budget_tokens": 2048}}'
export STRANDS_MAX_TOKENS="65536"
```

**What these settings provide:**
- **Enhanced Model**: Claude 4 Sonnet with latest capabilities
- **Interleaved Thinking**: Real-time reasoning during responses for better analysis
- **Extended Context**: 1M token context window for complex research sessions
- **Thinking Budget**: 2048 tokens for advanced reasoning cycles
- **Maximum Output**: 65536 tokens for comprehensive research reports

> **Note**: For the default Amazon Bedrock provider, you'll need AWS credentials configured and model access enabled for Claude 4 Sonnet in the us-west-2 region.

## Features at a Glance

### Hot-Reloading Tool Development

Automatically create and load tools from the `./tools/` directory:

```python
# ./tools/competitive_intel.py
from strands import tool

@tool
def competitive_intel(company: str, domain: str = "ai-agents") -> dict:
    """Gather competitive intelligence on companies in specific domains.
    
    This docstring is used by the LLM to understand the tool's purpose.
    """
    # Tool implementation here - the agent wrote this code itself
    return {"status": "success", "analysis": f"Intelligence for {company} in {domain}"}

# The breakthrough: Save this file and it's instantly available
# No imports, no registration, no restart needed
# Just save → agent.tool.competitive_intel() exists immediately
#
# Traditional AI: Fixed capabilities, human-coded tools
# Research Agent: Self-expanding capabilities, AI-created tools
```

### Multi-Agent Task Orchestration

Create background tasks with different models and specialized capabilities:

```mermaid
graph TD
    A["🎯 Research Query"] --> B{"🧠 Complexity Assessment"}
    
    B -->|"Simple"| C["⚡ Direct Processing"]
    B -->|"Complex"| D["🚀 Multi-Agent Coordination"]
    
    subgraph COORDINATION["🤝 Coordination Strategies"]
        D --> E["📋 tasks: Background Processing"]
        D --> F["🔄 use_agent: Model Switching"]  
        D --> G["👥 swarm: Parallel Teams"]
        D --> H["💭 think: Multi-Cycle Reasoning"]
    end
    
    subgraph SPECIALISTS["🎓 Specialist Agents"]
        E --> I["📊 Market Research Agent"]
        F --> J["⚙️ Technical Analysis Agent"]
        G --> K["🔬 Specialist Team A"]
        G --> L["🛠️ Specialist Team B"]
        H --> M["🧠 Deep Reasoning Cycles"]
    end
    
    I --> N["🔗 Coordinated Results"]
    J --> N
    K --> N
    L --> N
    M --> N
    
    N --> O["💡 Knowledge Integration"]
    O --> P["🔄 system_prompt: Self-Adaptation"]
    
    style A fill:#e3f2fd,stroke:#1976d2,stroke-width:3px,color:#000
    style B fill:#fff3e0,stroke:#f57c00,stroke-width:2px,color:#000
    style C fill:#e8f5e8,stroke:#388e3c,stroke-width:2px,color:#000
    style D fill:#f3e5f5,stroke:#7b1fa2,stroke-width:3px,color:#000
    
    style E fill:#e1f5fe,stroke:#0277bd,stroke-width:2px,color:#000
    style F fill:#f1f8e9,stroke:#558b2f,stroke-width:2px,color:#000
    style G fill:#fce4ec,stroke:#c2185b,stroke-width:2px,color:#000
    style H fill:#fff8e1,stroke:#ff8f00,stroke-width:2px,color:#000
    
    style I fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px,color:#000
    style J fill:#e0f2f1,stroke:#00695c,stroke-width:2px,color:#000
    style K fill:#fce4ec,stroke:#ad1457,stroke-width:2px,color:#000
    style L fill:#fce4ec,stroke:#ad1457,stroke-width:2px,color:#000
    style M fill:#fff3e0,stroke:#ef6c00,stroke-width:2px,color:#000
    
    style N fill:#e8f5e8,stroke:#2e7d32,stroke-width:3px,color:#000
    style O fill:#fff3e0,stroke:#f57c00,stroke-width:3px,color:#000
    style P fill:#f3e5f5,stroke:#7b1fa2,stroke-width:3px,color:#000
    
    style COORDINATION fill:#fafafa,stroke:#424242,stroke-width:2px
    style SPECIALISTS fill:#f5f5f5,stroke:#616161,stroke-width:2px
```

```python
from strands_research_agent.agent import create_agent

agent, mcp_client = create_agent()

with mcp_client:
    # The orchestration story: One brain, multiple specialists
    # Think of it like a research team where the lead researcher
    # (main agent) coordinates different experts working in parallel
    
    # Expert 1: Market Research Specialist (background task)
    agent.tool.tasks(
        action="create",
        task_id="market_research",
        prompt="Research AI agent market trends and competitive landscape",
        system_prompt="You are a market research analyst specializing in AI technologies.",
        tools=["scraper", "http_request", "store_in_kb"]
    )
    # This agent works independently, reports back when done

    # Expert 2: Technical Architect (different model, specialized brain)
    technical_analysis = agent.tool.use_agent(
        prompt="Analyze technical capabilities of top 5 AI agent frameworks",
        system_prompt="You are a senior software architect",
        model_provider="openai",  # Different AI model = different thinking style
        model_settings={"model_id": "gpt-4", "temperature": 0.2}
    )
    # Lower temperature = more analytical, precise thinking

    # The coordination: Experts share knowledge
    agent.tool.tasks(
        action="add_message",
        task_id="market_research", 
        message="Integrate technical analysis findings into market research"
    )
    # Knowledge flows between specialists, compound intelligence emerges
```

### Dynamic Self-Modification

The agent can modify its own behavior during runtime:

```python
# The evolution story: Agent learns and adapts its personality
# Like a researcher who gets better at research through experience

# Agent reflects: "I've learned something important about competitive analysis"
agent.tool.system_prompt(
    action="update",
    prompt="You are now a competitive intelligence specialist with deep knowledge of AI agent frameworks. Focus on technical differentiation and market positioning."
)
# The agent literally rewrites its own identity based on expertise gained

# The memory formation: Insights become institutional knowledge
agent.tool.store_in_kb(
    content="Key findings from competitive analysis research session...",
    title="AI Agent Framework Analysis - Q4 2024"
)
# Today's breakthrough becomes tomorrow's context
# This is how AI systems develop expertise over time
```

### Meta-Agent Cascading Orchestration

The research agent demonstrates unique **emergent intelligence patterns** through recursive meta-tool usage:

```mermaid
graph TD
    subgraph LEVEL1["🎖️ LEVEL 1: Primary Agent"]
        A["🎯 Primary Agent<br/>Research Coordinator"]
    end
    
    A --> B{"🔍 Complex Research Task<br/>Assessment"}
    
    subgraph LEVEL2["🎖️ LEVEL 2: Sub-Agents"]
        B --> C["🤖 use_agent: Create Sub-Agent<br/>Market Analyst"]
        C --> D["📊 Sub-Agent Processing<br/>Market Analysis"]
    end
    
    D --> E{"🎚️ Sub-Task Complexity?<br/>Need Deeper Analysis"}
    
    subgraph LEVEL3["🎖️ LEVEL 3: Sub-Sub-Agents"]
        E -->|"High Complexity"| F["🤖 use_agent: Create Sub-Sub-Agent<br/>Technical Specialist"]
        E -->|"Medium Complexity"| G["📋 tasks: Background Processing<br/>Data Collection"]
        E -->|"Simple Tasks"| H["⚡ Direct Processing<br/>Basic Analysis"]
    end
    
    subgraph LEVEL4["🎖️ LEVEL 4: Micro-Specialists"]
        F --> I["🔬 Sub-Sub-Agent Analysis<br/>Code Architecture Review"]
        G --> J["🌐 Background Task Spawns<br/>More Specialized Tasks"]
    end
    
    subgraph RESULTS["📈 Intelligence Compound Effect"]
        I --> K["⬆️ Results Flow Up Chain<br/>Technical Insights"]
        J --> K
        H --> K
        
        K --> L["🧠 Compound Intelligence<br/>Synthesis & Integration"]
        L --> M["✨ Emergent Research Insights<br/>Beyond Sum of Parts"]
    end
    
    style A fill:#e3f2fd,stroke:#1976d2,stroke-width:4px,color:#000
    style B fill:#fff3e0,stroke:#f57c00,stroke-width:3px,color:#000
    
    style C fill:#f3e5f5,stroke:#7b1fa2,stroke-width:3px,color:#000
    style D fill:#f8bbd9,stroke:#7b1fa2,stroke-width:2px,color:#000
    style E fill:#fff8e1,stroke:#ff8f00,stroke-width:2px,color:#000
    
    style F fill:#fff3e0,stroke:#ef6c00,stroke-width:3px,color:#000
    style G fill:#e1f5fe,stroke:#0277bd,stroke-width:2px,color:#000
    style H fill:#e8f5e8,stroke:#388e3c,stroke-width:2px,color:#000
    
    style I fill:#fff8e1,stroke:#f57c00,stroke-width:2px,color:#000
    style J fill:#e0f7fa,stroke:#00838f,stroke-width:2px,color:#000
    
    style K fill:#e8f5e8,stroke:#2e7d32,stroke-width:3px,color:#000
    style L fill:#e8f5e8,stroke:#1b5e20,stroke-width:4px,color:#000
    style M fill:#c8e6c9,stroke:#1b5e20,stroke-width:4px,color:#000
    
    style LEVEL1 fill:#e3f2fd,stroke:#1976d2,stroke-width:3px
    style LEVEL2 fill:#f3e5f5,stroke:#7b1fa2,stroke-width:3px
    style LEVEL3 fill:#fff8e1,stroke:#ff8f00,stroke-width:3px
    style LEVEL4 fill:#e0f7fa,stroke:#00838f,stroke-width:3px
    style RESULTS fill:#e8f5e8,stroke:#2e7d32,stroke-width:3px
```

```python
# Example: Cascading orchestration in action
# Primary agent recognizes complex research need
result = agent.tool.use_agent(
    prompt="Analyze AI agent market landscape comprehensively",
    system_prompt="You are a research coordinator with meta-cognitive capabilities",
    tools=["use_agent", "tasks", "retrieve", "store_in_kb"]
)

# What happens behind the scenes:
# 1. Research Coordinator Agent (Level 1) breaks down the task
# 2. Creates Technical Analysis Specialist via use_agent (Level 2)
# 3. Technical Specialist recognizes need for deeper analysis
# 4. Creates Code Analysis Sub-Agent via use_agent (Level 3) 
# 5. Meanwhile, creates background tasks for parallel processing
# 6. Each level can spawn additional agents or tasks as needed
#
# This creates exponential intelligence scaling:
# 1 Agent → 3 Agents → 9+ Specialist Agents → Emergent insights
#
# The breakthrough: Intelligence scales with compute through coordination
```

### Relay Chain Intelligence Pattern

Agents create successor agents while still running, forming continuous intelligence chains:

```mermaid
graph LR
    subgraph TIMELINE["⏱️ Temporal Flow: Parallel Intelligence Chain"]
        subgraph T1["🕐 Time T1: Agent A Starts"]
            A["🎯 Agent A<br/>Market Analysis"]
        end
        
        subgraph T2["🕑 Time T2: A Creates B (A Still Running)"]
            A1["📊 Agent A Processing...<br/>Market Research"]
            B["🚀 A creates Agent B<br/>Technical Analysis"]
        end
        
        subgraph T3["🕒 Time T3: B Creates C (A & B Running)"]
            B1["⚙️ Agent B Processing...<br/>Technical Research"]
            C["🔬 B creates Agent C<br/>Code Analysis"]
        end
        
        subgraph T4["🕓 Time T4: C Creates D (All Running)"]
            C1["💻 Agent C Processing...<br/>Code Review"]
            D["🛠️ C creates Agent D<br/>Implementation"]
        end
        
        subgraph T5["🕔 Time T5: Parallel Completion"]
            D1["🎯 Agent D Processing...<br/>Implementation Details"]
            
            E["✅ Agent A Completes<br/>Market Insights"]
            F["✅ Agent B Completes<br/>Technical Insights"]
            G["✅ Agent C Completes<br/>Code Insights"]
            H["✅ Agent D Completes<br/>Implementation Plan"]
        end
    end
    
    subgraph SYNTHESIS["🧠 Intelligence Synthesis"]
        E --> I["🔗 Results Chain Integration"]
        F --> I
        G --> I
        H --> I
        
        I --> J["✨ Enhanced Final Analysis<br/>Beyond Individual Capabilities"]
    end
    
    A --> A1
    A1 --> B
    B --> B1
    B1 --> C
    C --> C1
    C1 --> D
    D --> D1
    
    A1 --> E
    B1 --> F
    C1 --> G
    D1 --> H
    
    style A fill:#e3f2fd,stroke:#1976d2,stroke-width:3px,color:#000
    style A1 fill:#e1f5fe,stroke:#0288d1,stroke-width:2px,color:#000
    style B fill:#f3e5f5,stroke:#7b1fa2,stroke-width:3px,color:#000
    style B1 fill:#f8bbd9,stroke:#8e24aa,stroke-width:2px,color:#000
    style C fill:#fff3e0,stroke:#f57c00,stroke-width:3px,color:#000
    style C1 fill:#fff8e1,stroke:#ff8f00,stroke-width:2px,color:#000
    style D fill:#e8f5e8,stroke:#2e7d32,stroke-width:3px,color:#000
    style D1 fill:#c8e6c9,stroke:#388e3c,stroke-width:2px,color:#000
    
    style E fill:#e8eaf6,stroke:#3f51b5,stroke-width:3px,color:#000
    style F fill:#e0f2f1,stroke:#00695c,stroke-width:3px,color:#000
    style G fill:#fff3e0,stroke:#ef6c00,stroke-width:3px,color:#000
    style H fill:#e8f5e8,stroke:#2e7d32,stroke-width:3px,color:#000
    
    style I fill:#ffebee,stroke:#c62828,stroke-width:4px,color:#000
    style J fill:#ffcdd2,stroke:#d32f2f,stroke-width:4px,color:#000
    
    style T1 fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style T2 fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px
    style T3 fill:#fff8e1,stroke:#ff8f00,stroke-width:2px
    style T4 fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    style T5 fill:#e0f2f1,stroke:#00695c,stroke-width:2px
    style TIMELINE fill:#fafafa,stroke:#424242,stroke-width:3px
    style SYNTHESIS fill:#ffebee,stroke:#c62828,stroke-width:3px
```

```python
# Example: Intelligence relay chain in action
# Agent A starts and immediately creates Agent B while continuing its work
result_a = agent.tool.use_agent(
    prompt="Analyze AI market trends and spawn technical analysis specialist",
    system_prompt="Create specialized agents for deeper analysis while you continue market research",
    tools=["use_agent", "scraper", "store_in_kb"]
)

# Behind the scenes relay pattern:
# 1. Agent A: Starts market analysis
# 2. Agent A: Creates Agent B for technical analysis (Agent A still running)
# 3. Agent B: Starts technical work, creates Agent C for code analysis
# 4. Agent C: Starts code work, creates Agent D for implementation details  
# 5. All agents work in parallel, each enhancing the research depth
# 6. Results compound as each agent contributes specialized intelligence
#
# This creates continuous intelligence amplification:
# Each agent both contributes AND spawns the next level of expertise
# The original goal evolves and deepens through the intelligence relay
```

### Background Task Spawning Patterns

Background tasks can autonomously create additional tasks for distributed processing:

```mermaid
graph LR
    subgraph MAIN["🎯 Main Agent Process"]
        A["👤 Main Agent<br/>Research Coordinator"]
    end
    
    A --> B["📋 tasks: Create Background Task<br/>Market Research Analysis"]
    
    subgraph BACKGROUND["🌐 Background Agent Autonomous Processing"]
        B --> C["🤖 Background Agent Running<br/>Independent Processing"]
        
        C --> D{"🧠 Task Complexity Assessment<br/>Do I need help?"}
        
        subgraph SPAWN_LOGIC["🚀 Autonomous Spawning Logic"]
            D -->|"High Complexity"| E["📋 tasks: Spawn Sub-Task 1<br/>Technical Analysis"]
            D -->|"High Complexity"| F["📋 tasks: Spawn Sub-Task 2<br/>Market Intelligence"]
            D -->|"Simple Task"| G["⚡ Direct Processing<br/>Handle Myself"]
        end
    end
    
    subgraph SUBTASKS["👥 Sub-Agent Network"]
        E --> H["🔬 Sub-Agent 1 Processing<br/>Technical Research"]
        F --> I["📊 Sub-Agent 2 Processing<br/>Market Analysis"]
        
        H --> J{"🤔 Need More Specialization?<br/>Complexity Check"}
        I --> J
        
        subgraph MICRO_SPAWN["⚙️ Micro-Task Generation"]
            J -->|"Yes, Too Complex"| K["🎯 tasks: Create Micro-Tasks<br/>Company-Specific Analysis"]
            J -->|"No, Manageable"| L["📈 Results Aggregation<br/>Compile Findings"]
        end
    end
    
    subgraph NETWORK["🕸️ Distributed Processing Network"]
        K --> M["🌐 Micro-Agent Network<br/>Specialized Researchers"]
        M --> L
        G --> L
    end
    
    subgraph RESULTS["📊 Intelligence Synthesis"]
        L --> N["🔗 Compound Results<br/>Multi-Level Analysis"]
        N --> O["✅ Background Task Complete<br/>Report to Main Agent"]
    end
    
    style A fill:#e3f2fd,stroke:#1976d2,stroke-width:4px,color:#000
    style B fill:#f3e5f5,stroke:#7b1fa2,stroke-width:3px,color:#000
    style C fill:#f8bbd9,stroke:#8e24aa,stroke-width:3px,color:#000
    style D fill:#fff3e0,stroke:#f57c00,stroke-width:3px,color:#000
    
    style E fill:#e1f5fe,stroke:#0277bd,stroke-width:2px,color:#000
    style F fill:#e1f5fe,stroke:#0277bd,stroke-width:2px,color:#000
    style G fill:#e8f5e8,stroke:#388e3c,stroke-width:2px,color:#000
    
    style H fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px,color:#000
    style I fill:#e0f2f1,stroke:#00695c,stroke-width:2px,color:#000
    style J fill:#fff8e1,stroke:#ff8f00,stroke-width:2px,color:#000
    
    style K fill:#fff3e0,stroke:#ef6c00,stroke-width:3px,color:#000
    style L fill:#e8f5e8,stroke:#2e7d32,stroke-width:3px,color:#000
    style M fill:#fff8e1,stroke:#f57c00,stroke-width:2px,color:#000
    
    style N fill:#e8f5e8,stroke:#1b5e20,stroke-width:4px,color:#000
    style O fill:#c8e6c9,stroke:#1b5e20,stroke-width:4px,color:#000
    
    style MAIN fill:#e3f2fd,stroke:#1976d2,stroke-width:3px
    style BACKGROUND fill:#f3e5f5,stroke:#7b1fa2,stroke-width:3px
    style SUBTASKS fill:#e8eaf6,stroke:#3f51b5,stroke-width:3px
    style NETWORK fill:#fff8e1,stroke:#ff8f00,stroke-width:3px
    style RESULTS fill:#e8f5e8,stroke:#2e7d32,stroke-width:3px
    style SPAWN_LOGIC fill:#fafafa,stroke:#616161,stroke-width:2px
    style MICRO_SPAWN fill:#fafafa,stroke:#616161,stroke-width:2px
```

```python
# Example: Self-spawning background research network
agent.tool.tasks(
    action="create",
    task_id="market_research",
    prompt="Research AI agent frameworks and create specialized analysis teams as needed",
    system_prompt="You are a research coordinator. Use tasks and use_agent tools to spawn specialized teams when complexity requires it.",
    tools=["tasks", "use_agent", "scraper", "store_in_kb", "retrieve"]
)

# The spawned background agent autonomously:
# 1. Assesses research complexity
# 2. Creates sub-tasks for technical analysis, market analysis, competitive intelligence
# 3. Each sub-task can spawn micro-tasks for specific companies/frameworks
# 4. Results flow back up the hierarchy for synthesis
# 5. Final comprehensive analysis stored in knowledge base
#
# This pattern enables:
# - Autonomous research team scaling based on complexity
# - Parallel processing without manual orchestration  
# - Exponential research capability through recursive delegation
```

### Persistent Learning System

Cross-session knowledge accumulation and context awareness:

```mermaid
graph LR
    subgraph SESSION["🔄 Research Session Cycle"]
        A["🚀 Research Session<br/>New Query"]
    end
    
    A --> B["📖 retrieve: Past Context<br/>What do I know?"]
    
    subgraph RETRIEVAL["🧠 Knowledge Retrieval"]
        B --> B1["📚 SQLite Memory<br/>Recent Sessions"]
        B --> B2["☁️ Bedrock KB<br/>Long-term Knowledge"] 
        B --> B3["🔍 S3 Vectors<br/>Semantic Search"]
    end
    
    subgraph PROCESSING["⚙️ Agent Processing"]
        B1 --> C["🤖 Agent Processing<br/>Enhanced by Past Context"]
        B2 --> C
        B3 --> C
        
        C --> D["💡 New Insights Generated<br/>Novel Discoveries"]
    end
    
    subgraph STORAGE["💾 Knowledge Storage & Growth"]
        D --> E1["📋 store_in_kb: Knowledge Storage<br/>Permanent Learning"]
        D --> E2["💬 SQLite: Session Memory<br/>Conversation Context"]
        D --> E3["🧠 S3 Vectors: Semantic Memory<br/>Similarity Patterns"]
    end
    
    subgraph KNOWLEDGE["🏛️ Knowledge Infrastructure"]
        E1 --> F1["☁️ Knowledge Base<br/>Enterprise Memory"]
        E2 --> F2["💾 Local SQLite<br/>Session Context"]
        E3 --> F3["🔗 S3 Vectors<br/>Semantic Network"]
        
        F1 --> G["🌐 Cross-Session Memory<br/>Persistent Intelligence"]
        F2 --> G
        F3 --> G
    end
    
    subgraph EVOLUTION["🔄 Self-Evolution"]
        D --> I["🎯 system_prompt: Behavior Adaptation<br/>I've learned something new"]
        I --> J["⬆️ Improved Capabilities<br/>Enhanced Research Patterns"]
        J --> K["📈 Better Research Quality<br/>Exponential Growth"]
    end
    
    subgraph CONTINUITY["♻️ Continuous Learning Loop"]
        G --> H["🔮 Future Sessions<br/>Start Smarter"]
        K --> H
        H --> A
    end
    
    style A fill:#e3f2fd,stroke:#1976d2,stroke-width:4px,color:#000
    style B fill:#f3e5f5,stroke:#7b1fa2,stroke-width:3px,color:#000
    
    style B1 fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px,color:#000
    style B2 fill:#e0f7fa,stroke:#00838f,stroke-width:2px,color:#000
    style B3 fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px,color:#000
    
    style C fill:#fff8e1,stroke:#ff8f00,stroke-width:3px,color:#000
    style D fill:#fff3e0,stroke:#ef6c00,stroke-width:4px,color:#000
    
    style E1 fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#000
    style E2 fill:#e3f2fd,stroke:#1976d2,stroke-width:2px,color:#000
    style E3 fill:#e8f5e8,stroke:#388e3c,stroke-width:2px,color:#000
    
    style F1 fill:#f8bbd9,stroke:#8e24aa,stroke-width:2px,color:#000
    style F2 fill:#bbdefb,stroke:#1976d2,stroke-width:2px,color:#000
    style F3 fill:#c8e6c9,stroke:#388e3c,stroke-width:2px,color:#000
    
    style G fill:#e0f2f1,stroke:#00695c,stroke-width:4px,color:#000
    style H fill:#e8eaf6,stroke:#3f51b5,stroke-width:3px,color:#000
    
    style I fill:#fff8e1,stroke:#ff8f00,stroke-width:3px,color:#000
    style J fill:#e8f5e8,stroke:#2e7d32,stroke-width:3px,color:#000
    style K fill:#c8e6c9,stroke:#1b5e20,stroke-width:4px,color:#000
    
    style SESSION fill:#e3f2fd,stroke:#1976d2,stroke-width:3px
    style RETRIEVAL fill:#f3e5f5,stroke:#7b1fa2,stroke-width:3px
    style PROCESSING fill:#fff8e1,stroke:#ff8f00,stroke-width:3px
    style STORAGE fill:#e8eaf6,stroke:#3f51b5,stroke-width:3px
    style KNOWLEDGE fill:#e0f2f1,stroke:#00695c,stroke-width:3px
    style EVOLUTION fill:#fff3e0,stroke:#ef6c00,stroke-width:3px
    style CONTINUITY fill:#e8f5e8,stroke:#2e7d32,stroke-width:3px
```

```python
# The continuity story: Every session builds on previous discoveries
# Like a scientist's lab notebook that gets smarter over time

# Agent wakes up: "What did I learn before about this topic?"
context = agent.tool.retrieve(
    text="AI agent framework competitive analysis",
    knowledgeBaseId="your_kb_id",
    numberOfResults=5
)
# The agent queries its own past insights, building on previous work

# This happens automatically:
# - Every conversation gets stored in SQLite (session memory)
# - Important insights get stored in Bedrock Knowledge Base (long-term memory)
# - Future sessions start with accumulated knowledge, not blank slate
# 
# This creates exponential learning: each research session
# becomes more sophisticated than the last
```

## Core Tools

The research agent includes specialized tools for advanced research patterns:

**Hot-Reloading & Development**
- `load_tool` - Dynamic tool loading at runtime
- `editor` - Create/modify tool files
- `system_prompt` - Dynamic behavior modification

**Multi-Agent Coordination**  
- `tasks` - Background task management with persistence
- `use_agent` - Model switching and delegation
- `swarm` - Self-organizing agent teams
- `think` - Multi-cycle reasoning

**Learning & Memory**
- `store_in_kb` - Asynchronous knowledge base storage  
- `retrieve` - Semantic search across stored knowledge
- `sqlite_memory` - Session memory with full-text search
- `s3_memory` - Vector-based semantic memory

**Research & Analysis**
- `scraper` - Web scraping and parsing
- `http_request` - API integrations with authentication
- `graphql` - GraphQL queries
- `python_repl` - Data analysis and computation

## Multiple Model Providers

Support for various model providers with intelligent coordination:

```python
# The specialization story: Different brains for different tasks
# Like having a team of experts, each with unique strengths

# AWS Bedrock (Production recommended) - The strategist
export STRANDS_MODEL_ID="us.anthropic.claude-sonnet-4-20250514-v1:0"
export MODEL_PROVIDER="bedrock"

# OpenAI for code analysis - The technical architect
agent.tool.use_agent(
    prompt="Analyze technical architecture", 
    model_provider="openai",  # GPT-4 excels at code understanding
    model_settings={"model_id": "gpt-4", "temperature": 0.2}
)
# Low temperature = precise, analytical thinking

# Anthropic for strategic analysis - The creative strategist  
agent.tool.use_agent(
    prompt="Market positioning analysis",
    model_provider="anthropic",  # Claude excels at nuanced reasoning
    model_settings={"model_id": "claude-3-5-sonnet-20241022"}
)

# Local Ollama for high-volume processing - The workhorse
agent.tool.use_agent(
    prompt="Process large dataset",
    model_provider="ollama",  # Local model for cost-effective bulk work
    model_settings={"model_id": "qwen3:4b", "host": "http://localhost:11434"}
)
# The agent automatically picks the right brain for each job
```

Built-in model providers:
- [Amazon Bedrock](https://aws.amazon.com/bedrock/) (Recommended for production)
- [Anthropic](https://www.anthropic.com/)
- [OpenAI](https://openai.com/)
- [Ollama](https://ollama.ai/) (Local models)
- [LiteLLM](https://litellm.ai/) (Multi-provider proxy)

## Architecture

The research agent demonstrates advanced Strands Agents patterns with a modular, extensible architecture:

```mermaid
graph TB
    subgraph HOTRELOAD["🔥 Hot-Reload Engine (Zero Restart Development)"]
        A["📁 ./tools/ Directory<br/>Developer Workspace"]
        B["👁️ File Watcher<br/>Real-time Monitoring"]
        C["⚡ Dynamic Tool Loading<br/>Instant Availability"]
        D["🧰 Agent Tool Registry<br/>Live Tool Catalog"]
        
        A --> B
        B --> C
        C --> D
    end
    
    subgraph ORCHESTRATION["🤖 Multi-Agent Orchestration (Coordination Intelligence)"]
        E["📋 tasks.py<br/>Background Processing"]
        G["🔄 use_agent.py<br/>Model Switching"]
        I["👥 swarm.py<br/>Parallel Teams"]
        K["💭 think.py<br/>Multi-Cycle Reasoning"]
        
        E --> F["⚙️ Background Processing<br/>Independent Execution"]
        G --> H["🧠 Model Switching<br/>Specialized Intelligence"]
        I --> J["🤝 Parallel Teams<br/>Collaborative Processing"]
        K --> L["🔄 Multi-Cycle Reasoning<br/>Deep Analysis"]
    end
    
    subgraph LEARNING["💾 Persistent Learning (Compound Intelligence)"]
        M["📝 store_in_kb.py<br/>Knowledge Ingestion"]
        O["🔍 retrieve.py<br/>Knowledge Retrieval"]
        Q["💬 sqlite_memory.py<br/>Session Context"]
        S["🎯 system_prompt.py<br/>Behavior Adaptation"]
        
        M --> N["☁️ Bedrock Knowledge Base<br/>Enterprise Memory"]
        O --> P["🔍 Semantic Search<br/>Context Discovery"]
        Q --> R["📚 Session Context<br/>Local Memory"]
        S --> T["🔄 Behavior Adaptation<br/>Dynamic Evolution"]
    end
    
    subgraph INFRASTRUCTURE["🌐 Cloud Infrastructure (AWS Foundation)"]
        U["🏛️ AWS Bedrock<br/>Model Hosting"]
        W["📡 EventBridge<br/>Distributed Events"]
        Y["📦 S3 Vectors<br/>Semantic Storage"]
        
        U --> V["🤖 Claude Models<br/>Advanced Reasoning"]
        W --> X["🔗 Distributed Coordination<br/>Cross-Instance Sync"]
        Y --> Z["🧠 Vector Storage<br/>Similarity Search"]
    end
    
    subgraph CONNECTIONS["🔗 System Integration Flow"]
        D --> E
        D --> G
        D --> I
        D --> K
        D --> M
        D --> O
        D --> Q
        D --> S
        
        F --> U
        H --> U
        J --> U
        L --> U
        N --> U
        P --> U
        R --> Y
        T --> D
    end
    
    style A fill:#e3f2fd,stroke:#1976d2,stroke-width:3px,color:#000
    style B fill:#e1f5fe,stroke:#0288d1,stroke-width:2px,color:#000
    style C fill:#81c784,stroke:#388e3c,stroke-width:4px,color:#000
    style D fill:#c8e6c9,stroke:#2e7d32,stroke-width:3px,color:#000
    
    style E fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#000
    style F fill:#f8bbd9,stroke:#8e24aa,stroke-width:3px,color:#000
    style G fill:#e8f5e8,stroke:#388e3c,stroke-width:2px,color:#000
    style H fill:#c8e6c9,stroke:#4caf50,stroke-width:3px,color:#000
    style I fill:#fce4ec,stroke:#c2185b,stroke-width:2px,color:#000
    style J fill:#f8bbd9,stroke:#e91e63,stroke-width:3px,color:#000
    style K fill:#fff8e1,stroke:#ff8f00,stroke-width:2px,color:#000
    style L fill:#fff3e0,stroke:#ef6c00,stroke-width:3px,color:#000
    
    style M fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px,color:#000
    style N fill:#c5cae9,stroke:#3f51b5,stroke-width:4px,color:#000
    style O fill:#e0f2f1,stroke:#00695c,stroke-width:2px,color:#000
    style P fill:#b2dfdb,stroke:#00695c,stroke-width:3px,color:#000
    style Q fill:#e3f2fd,stroke:#1976d2,stroke-width:2px,color:#000
    style R fill:#bbdefb,stroke:#1976d2,stroke-width:3px,color:#000
    style S fill:#fff3e0,stroke:#f57c00,stroke-width:2px,color:#000
    style T fill:#ffe0b2,stroke:#f57c00,stroke-width:4px,color:#000
    
    style U fill:#ffecb3,stroke:#ffa000,stroke-width:4px,color:#000
    style V fill:#fff8e1,stroke:#ff8f00,stroke-width:4px,color:#000
    style W fill:#e0f7fa,stroke:#00838f,stroke-width:3px,color:#000
    style X fill:#b2ebf2,stroke:#00838f,stroke-width:3px,color:#000
    style Y fill:#f1f8e9,stroke:#558b2f,stroke-width:3px,color:#000
    style Z fill:#c8e6c9,stroke:#558b2f,stroke-width:3px,color:#000
    
    style HOTRELOAD fill:#e8f5e8,stroke:#2e7d32,stroke-width:4px
    style ORCHESTRATION fill:#f3e5f5,stroke:#7b1fa2,stroke-width:4px
    style LEARNING fill:#e8eaf6,stroke:#3f51b5,stroke-width:4px
    style INFRASTRUCTURE fill:#fff8e1,stroke:#ff8f00,stroke-width:4px
    style CONNECTIONS fill:#fafafa,stroke:#424242,stroke-width:2px
```

```
📦 strands-research-agent/
├── src/strands_research_agent/
│   ├── agent.py                 # Main agent with MCP integration
│   ├── tools/                   # Specialized tools
│   │   ├── tasks.py             # Background task orchestration
│   │   ├── system_prompt.py     # Dynamic behavior adaptation
│   │   ├── store_in_kb.py       # Knowledge base integration
│   │   ├── scraper.py           # Web research capabilities  
│   │   └── ...                  # Additional research tools
│   └── handlers/
│       └── callback_handler.py  # Event handling and notifications
├── tools/                       # Hot-reloadable tools (auto-created)
├── tasks/                       # Task state and results (auto-created)
└── pyproject.toml              # Package configuration
```

## Documentation

For detailed guidance & examples, explore our documentation:

- [Strands Agents Documentation](https://strandsagents.com/) - Core framework and concepts
- [Strands Agents 1.0 Release](https://aws.amazon.com/blogs/opensource/introducing-strands-agents-1-0-production-ready-multi-agent-orchestration-made-simple/) - Multi-agent orchestration foundations
- [Original SDK Introduction](https://aws.amazon.com/blogs/opensource/introducing-strands-agents-an-open-source-ai-agents-sdk/) - The vision and architecture
- [Production Deployment Guide](https://strandsagents.com/latest/user-guide/deploy/operating-agents-in-production/) - Enterprise deployment patterns

## Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository** - Click the fork button on GitHub
2. **Setup development environment**:
   ```bash
   # The contributor's journey: From clone to breakthrough
   git clone https://github.com/your-username/samples.git
   cd samples/02-samples/14-research-agent
   pip install -e .[dev]
   
   # Now you're ready to push the boundaries of AI agent capabilities
   # Your code changes will hot-reload instantly - no friction between idea and execution
   ```
3. **Create new tools** - Save `.py` files in `./tools/` - they auto-load instantly
4. **Test your changes** - Run `research-agent` to test new capabilities
5. **Submit pull request** - Include examples and documentation

**Development Areas:**
- Meta-cognitive tools for advanced coordination
- Research methodologies and analysis patterns  
- Learning systems and knowledge persistence
- Distributed intelligence and cross-instance coordination

## Production Usage

The research agent demonstrates patterns used in production AI systems at AWS:

- **Amazon Q Developer** - Uses Strands Agents for intelligent code assistance
- **AWS Glue** - Automated data analysis and pipeline optimization  
- **VPC Reachability Analyzer** - Network intelligence and troubleshooting

**Enterprise Features:**
- Cross-session knowledge persistence via AWS Bedrock Knowledge Base
- Distributed coordination through AWS EventBridge
- Background task processing with filesystem persistence
- Multi-model orchestration for specialized intelligence

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

---

*Built with [Strands Agents SDK](https://strandsagents.com) | Part of [Strands Agents Samples](https://github.com/strands-agents/samples)*
