# Datadog Observability for Amazon Bedrock Agents with Strands

This folder contains an extension of the Amazon Bedrock Agents with Strands sample, integrating Datadog for comprehensive observability. The integration allows you to monitor, trace, and evaluate your Bedrock Agents with Strands applications using Datadog's powerful observability platform.

## Contents

- **Jupyter Notebooks**:
  - [DatadogObservabilityStrandsAgents.ipynb](DatadogObservabilityStrandsAgents.ipynb): Main notebook demonstrating Datadog integration with Bedrock Agents

## ADOT Collector with Datadog Exporter

The `adot` directory contains all necessary components to deploy an AWS Distro for OpenTelemetry (ADOT) collector with the Datadog exporter enabled and configured in AWS:

- Deployment YAML files for Kubernetes
- Setup and configuration scripts
- Sample applications with OpenTelemetry instrumentation
- Detailed setup instructions in [adot/README.md](adot/README-ADOT-SETUP.md)

## Getting Started

1. Review the Jupyter notebooks to understand the integration patterns
2. Follow the instructions in [adot/README.md](adot/README.md) to deploy the ADOT collector
3. Configure your Datadog API key in the `.env` file
4. Run the [DatadogObservabilityStrandsAgents.ipynb](DatadogObservabilityStrandsAgents.ipynb) notebook to execute the sample with Datadog integration

## Requirements

- AWS account with access to Amazon Bedrock
- Datadog account with API key
- Kubernetes cluster (for ADOT collector deployment)
- Python 3.8+ with required dependencies

## Additional Resources

For more information on Datadog integration with AWS services, visit the [Datadog AWS Integration documentation](https://docs.datadoghq.com/integrations/amazon_web_services/).
