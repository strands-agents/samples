# Strands Agent with Supabase Integration

## Overview

[Supabase](https://supabase.com/) is an open-source Firebase alternative providing all the backend services you need to build a product: a PostgreSQL database, authentication, instant APIs, edge functions, realtime subscriptions, and storage. This integration demonstrates how to use Supabase with Strands AI agents through the Model Context Protocol (MCP).

![architecture](./assets/architecture.png)

|Feature             |Description                                        |
|--------------------|---------------------------------------------------|
|Agent Structure     |Single-agent architecture                          |
|Native Tools        |file_read, file_write                              |
|MCP Servers         |[Supabase MCP Server](https://github.com/supabase-community/supabase-mcp)                  |
|Model Provider      |Amazon Bedrock                                     |

## Prerequisites

- A [Supabase account](https://supabase.com/) with a project
- Supabase personal access token
- Set up AWS credentials with access to AWS services
  - You need an AWS account with appropriate permissions
  - Configure AWS credentials with aws configure or environment variables

## Getting Started

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/).

2. Set up Supabase credentials in `.env` using [.env.example](./.env.example).

3. Run the notebook `supabase-integration.ipynb` to explore the Supabase MCP features.

## Features

The Supabase MCP integration provides the following capabilities:

- **Project Management**: Create, list, and manage Supabase projects
- **Database Management**: Execute SQL queries, manage tables, and handle database migrations
- **Edge Function Management**: Deploy, update, and invoke serverless functions
- **Storage Management**: Upload, download, and manage files in Supabase storage
- **Authentication**: Manage users and authentication settings
