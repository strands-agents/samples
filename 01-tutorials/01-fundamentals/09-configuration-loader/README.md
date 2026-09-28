# Configuration Loader Tutorial

This tutorial demonstrates how to use Strands Agents' experimental configuration system to load and manage agents, tools, swarms, and graphs programmatically using dictionary configurations.

## Prerequisites

- Python 3.10 or later
- Strands Agents SDK installed
- Basic understanding of Python dictionaries

## Overview

The experimental configuration loader system allows you to define agents, tools, swarms, and graphs programmatically using dictionary configurations. This approach provides:

- **Programmatic Configuration**: Define your agents and workflows using Python dictionaries
- **Reusability**: Share and reuse configurations across projects
- **Modularity**: Compose complex systems from simple components
- **Dynamic Loading**: Create configurations at runtime

**Note**: This is an experimental feature.

## Tutorial Notebooks

Run these notebooks in order to learn the configuration system:

### Core Configuration Loading
1. **01-tool-loading.ipynb** - Load individual tools using ToolConfigLoader
2. **02-agent-loading.ipynb** - Load agents with tools and system prompts using AgentConfigLoader
3. **04-swarm-loading.ipynb** - Load multi-agent swarms using SwarmConfigLoader
4. **05-graph-loading.ipynb** - Load workflow graphs with conditions and routing using GraphConfigLoader

### Advanced Patterns
5. **03-agents-as-tools.ipynb** - Use agents as tools within other agents
6. **06-structured-output-config.ipynb** - Configure agents with structured output schemas
7. **07-swarms-as-tools.ipynb** - Use entire swarms as tools
8. **08-graphs-as-tools.ipynb** - Use workflow graphs as tools

## Configuration Files

The `configs/` directory contains example configurations for:
- Individual tools
- Agent configurations  
- Swarm definitions
- Graph workflows
- Composite configurations (agents/swarms/graphs as tools)

## Running the Examples

### Prerequisites
Make sure you have the required dependencies installed:

```bash
pip install strands-agents
```

### Running Notebooks
1. Start Jupyter Lab or Jupyter Notebook:
   ```bash
   jupyter lab
   # or
   jupyter notebook
   ```

2. Open any notebook file (`.ipynb`) and run the cells sequentially

3. Each notebook is self-contained and includes:
   - Configuration examples using dictionary-based configs
   - Code to load and use the configurations with config loaders
   - Explanations of key concepts

### Key Files
- **weather_tool.py** - Example custom tool implementation
- **configs/** - Directory containing configuration examples
- **workflow/** - Directory containing workflow-specific configurations
- **SCHEMA-PLAN.md** - Documentation of the schema validation system (experimental)
- **README-schema-validation.md** - Detailed schema validation guide (experimental)

## Configuration Loaders

The tutorial demonstrates the experimental configuration loader classes:

- **AgentConfigLoader**: Load agents from dictionary configurations
- **ToolConfigLoader**: Load tools by identifier or multi-agent configurations  
- **SwarmConfigLoader**: Load swarms from dictionary configurations
- **GraphConfigLoader**: Load graphs from dictionary configurations

Each loader provides programmatic configuration management with caching and validation.

## Next Steps

After completing this tutorial, you'll understand how to:
- Create dictionary configurations for all Strands components
- Load and use configurations programmatically with config loaders
- Compose complex multi-agent systems
- Use agents, swarms, and graphs as reusable tools
- Work with the experimental configuration system

For more advanced topics, explore the other tutorial sections in the samples repository.