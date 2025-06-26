# MCP Servers for AWS Medical AI Triage Workshop

This directory contains MCP (Model Context Protocol) server examples used in the workshop.

## Directory Structure

```
mcp_servers/
├── README.md                    # This file
├── calculator_server.py         # Basic calculator MCP server
├── calculator_client.py         # Calculator client example
├── task_manager_server.py       # Custom task manager MCP server
├── task_manager_client.py       # Task manager client example
├── calendar/
│   └── calendar_server.py       # Calendar integration MCP server
└── weather/
    └── weather_server.py        # Weather forecasting MCP server
```

## Quick Start

### 1. Calculator Example (Module 1)

**Terminal 1 - Start the Calculator Server:**
```bash
cd ui/backend
python mcp_servers/calculator_server.py
```

**Terminal 2 - Start the Calculator Client:**
```bash
cd ui/backend
python mcp_servers/calculator_client.py
```

### 2. Task Manager Example (Module 1 - Build Your Own)

**Terminal 1 - Start the Task Manager Server:**
```bash
cd ui/backend
python mcp_servers/task_manager_server.py
```

**Terminal 2 - Start the Task Manager Client:**
```bash
cd ui/backend
python mcp_servers/task_manager_client.py
```

### 3. Calendar Integration (Module 2)

**Terminal 1 - Start the Calendar Server:**
```bash
cd ui/backend
python mcp_servers/calendar/calendar_server.py
```

### 4. Weather Forecasting (Module 3)

**Terminal 1 - Start the Weather Server:**
```bash
cd ui/backend
python mcp_servers/weather/weather_server.py
```

## Server Ports

| Server | Port | URL |
|--------|------|-----|
| Calculator | 8000 | http://localhost:8000/mcp/ |
| Task Manager | 8001 | http://localhost:8001/mcp/ |
| Calendar | 8002 | http://localhost:8002/mcp/ |
| Weather | 8003 | http://localhost:8003/mcp/ |

## Dependencies

Make sure you have the required dependencies installed:

```bash
cd ui/backend
pip install -r requirements.txt
```

## Workshop Notes

- Each server runs independently on different ports
- The main backend application (main.py) can integrate with these MCP servers
- All servers use the FastMCP library for simplicity
- In production, replace mock data with real API integrations

## Troubleshooting

### Common Issues:

1. **Port already in use**: Make sure no other processes are using the server ports
2. **Import errors**: Ensure all dependencies are installed with `pip install -r requirements.txt`
3. **Connection refused**: Make sure the server is running before starting the client

### Testing Server Status:

```bash
# Test if a server is running
curl http://localhost:8000/mcp/
```

## Integration with Main Application

The main backend application (`main.py`) can connect to these MCP servers using the Strands SDK. See the workshop content for detailed integration examples. 