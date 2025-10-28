#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { LambdaErrorAnalysisStack } from './cdk/stacks/lambda-error-analysis-agent-stack';
import { projectName, envNameType } from './cdk/constant';
import { AwsSolutionsChecks } from 'cdk-nag';

const app = new cdk.App();

// CDK NAG for security compliance - enabled with comprehensive suppressions
cdk.Aspects.of(app).add(new AwsSolutionsChecks({ verbose: true }));

// Get environment name from context
const envName = app.node.tryGetContext('envName') as envNameType || 'local';

// Create the stack
new LambdaErrorAnalysisStack(app, `${projectName}Stack`, {
  envName: envName,
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
  },
  description: `${projectName} - Intelligent error analysis for Lambda automation using Strands Agents`,
});