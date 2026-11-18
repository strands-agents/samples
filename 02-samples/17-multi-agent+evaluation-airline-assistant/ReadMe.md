# MultiAgent with Taubench

This repository contains AWS Strands SDK implementation of a multi-agent solution on the taubench dataset.

## Description

This project integrates taubench into a multi-agent solution. Taubench is a benchmarking dataset that allows for standardized performance testing and analysis. This is a demo that utilizes single and multi-agents to run taubench examples.

## Getting Started

DISCLAIMER: Under the Setting Up LangFuse Tracing Section (Step 3: Replace the API Keys), make sure to add your own API keys. All secrets should be added onto Secrets Manager. 

### Dependencies

* Git
* Python 3.8 or higher
* pip (Python package installer)


## Setup Instructions

### Step 1: Clone the multi-agent-awsStrands Repository
```bash
# Clone the multi-agent-awsStrands repository
git clone git@ssh.gitlab.aws.dev:genaiic-reusable-assets/shareable-assets/multi-agent-awsStrands.git
```

### Step 2: Clone the Taubench and Mabench Repository
```bash
# Clone the taubench repository
git clone https://github.com/sierra-research/tau-bench.git
git clone https://github.com/hinthornw/mabench.git
```

### Step 3: Create Directory in multi-agent-awsStrands Repository
```bash
# Navigate back to the multi-agent-awsStrands repo
mkdir -p multi-agent-awsStrands/taubench/data/tau-bench
mkdir -p multi-agent-awsStrands/taubench/data/ma-bench
```

### Step 4: Copy Taubench and Mabench Content (Excluding Git Files)
```bash
# Copy all non-git related files to our repository
# Make sure to exclude .git, .github, .gitignore, etc.
rsync -av --exclude='.git*' --exclude='.github' tau-bench/ multi-agent-awsStrands/taubench/data/tau-bench/
rsync -av --exclude='.git*' --exclude='.github' mabench/ multi-agent-awsStrands/taubench/data/ma-bench/
```

### Step 5: Delete Taubench and Mabench Content (Excluding Git Files)
```bash
# Copy all non-git related files to our repository
# Make sure to exclude .git, .github, .gitignore, etc.
rm -rf tau-bench
rm -rf mabench
```

### Step 5: Install from source
```bash
# Navigate to the taubench data directory
cd multi-agent-awsStrands/taubench/

# Install in development mode
pip install -e data/tau-bench
```

## Running Tools Modification Script

To prepare tool files for use with the Strands framework, you need to run the modifyToolsStrands.py script which adds the necessary imports, decorators, and data loading code:

```bash
# Navigate to the src directory
cd multi-agent-awsStrands/taubench/src

# Run the script for the airline domain (default)
python modifyToolsStrands.py

# Or run for a different domain if needed
python modifyToolsStrands.py [domain_name]
```

This script will:
1. Add `from strands import tool` import if not present
2. Add `from mabench.environments.airline.data import load_data` import if needed
3. Add `@tool` decorator to tool functions if not present
4. Replace `data = get_data()` calls with `data = load_data()`

## Creating Ground Truth Data

To generate ground truth data for the airline tasks, you can run the createGT_airline.py script:

```bash
# Navigate to the src directory
cd multi-agent-awsStrands/taubench/src

# Run the script to generate ground truth data
python createGT.py --domain airline
```

This script:
1. Converts task instructions into natural language questions using the Claude model via AWS Bedrock
2. Generates appropriate tool outputs for each action in the tasks
3. Saves the updated tasks with questions and action results to `tasks_singleturn.json`

Note: This script requires AWS credentials with access to Bedrock. Make sure your AWS credentials are properly configured before running this script.

## Setting Up Langfuse Tracing

Langfuse provides tracing, evaluation, and analytics for LLM applications. Follow these steps to set up Langfuse tracing for this project:

### Step 1: Create a Langfuse Account
1. Sign up at [langfuse.com](https://langfuse.com/)
2. Create a new project in the Langfuse dashboard
3. Generate API keys from the project settings page

### Step 2: Add Langfuse Configuration to Your Notebooks
Add the following code at the beginning of your notebook, before creating any Strands agents:

```python
######################### LANGFUSE SETUP ########################
# Langfuse credentials
os.environ["LANGFUSE_PUBLIC_KEY"] = "your generated public key"
os.environ["LANGFUSE_SECRET_KEY"] = "your generated secret key"
os.environ["LANGFUSE_HOST"] = "https://us.cloud.langfuse.com"

# Build Basic Auth header
LANGFUSE_AUTH = base64.b64encode(
    f"{os.environ.get('LANGFUSE_PUBLIC_KEY')}:{os.environ.get('LANGFUSE_SECRET_KEY')}".encode()
).decode()

# Configure OpenTelemetry endpoint & headers
os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = os.environ.get("LANGFUSE_HOST") + "/api/public/otel/"
os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Basic {LANGFUSE_AUTH}"

# Initialize OpenTelemetry BEFORE creating Strands agent

strands_telemetry = StrandsTelemetry()
strands_telemetry.setup_otlp_exporter()
# strands_telemetry.setup_console_exporter()  # Print traces to console
######################### LANGFUSE SETUP ########################
```

### Step 3: Replace the API Keys
Replace the placeholder API keys in the code with your own keys from the Langfuse dashboard:
- `LANGFUSE_PUBLIC_KEY`: Your public API key from Langfuse
- `LANGFUSE_SECRET_KEY`: Your secret API key from Langfuse

### Step 4: Run Your Notebook
Once configured, all Strands agent activities will be traced and available in your Langfuse dashboard for analysis.

### Step 5: Running Evaluation Notebook
In terminal, navigate to taubench/src/ragas-evaluation/ and run git init
```bash
# Navigate to the ragas repository
cd taubench/src/ragas-evaluation/

# Git initialize
git init
```
Then run evaluation.ipynb to obtain results. 
