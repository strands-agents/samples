import { Duration, Stack, StackProps } from "aws-cdk-lib";
import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as iam from "aws-cdk-lib/aws-iam";
// Direct Lambda invocation architecture
import * as path from "path";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as s3deployment from "aws-cdk-lib/aws-s3-deployment";
import * as ssm from "aws-cdk-lib/aws-ssm";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";

import { bedrock } from "@cdklabs/generative-ai-cdk-constructs";
import * as events from "aws-cdk-lib/aws-events";
import * as targets from "aws-cdk-lib/aws-events-targets";
import {
  envNameType,
  projectName,
  s3BucketProps,
  ssmParamDynamoDb,
  ssmParamKnowledgeBaseId,
} from "../constant";
import { NagSuppressions } from "cdk-nag";

interface LambdaErrorAnalysisStackProps extends StackProps {
  envName: envNameType;
}

export class LambdaErrorAnalysisStack extends Stack {
  constructor(
    scope: Construct,
    id: string,
    props: LambdaErrorAnalysisStackProps
  ) {
    super(scope, id, props);

    // Create Knowledge Base using AWS Labs Level 3 Construct (much more reliable!)
    const knowledgeBase = new bedrock.KnowledgeBase(
      this,
      `${projectName}-knowledge-base`,
      {
        embeddingsModel:
          bedrock.BedrockFoundationModel.TITAN_EMBED_TEXT_V2_1024,
        instruction:
          "Use this knowledge base to answer questions about Lambda automation errors, " +
          "troubleshooting, and best practices. It contains source code, documentation, " +
          "and error analysis patterns for Lambda error analysis.",
      }
    );

    // Create DynamoDB table for error analysis storage
    const errorAnalysisTable = new dynamodb.Table(
      this,
      `${projectName}-error-analysis-table`,
      {
        tableName: `${projectName}-error-analysis`,
        partitionKey: { name: "error_id", type: dynamodb.AttributeType.STRING },
        sortKey: { name: "timestamp", type: dynamodb.AttributeType.STRING },
        billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
        encryption: dynamodb.TableEncryption.AWS_MANAGED,
        pointInTimeRecovery: true,
        removalPolicy: cdk.RemovalPolicy.DESTROY,
      }
    );

    // Create SSM parameter for DynamoDB table name
    new ssm.StringParameter(this, `${projectName}-dynamo-db-param`, {
      parameterName: `/${ssmParamDynamoDb}`,
      stringValue: errorAnalysisTable.tableName,
      description: "DynamoDB table name for error analysis storage",
    });

    // Create S3 buckets for access logs and source code
    const accessLogBucket = new s3.Bucket(
      this,
      `${projectName}-access-bucket-access-logs`,
      {
        objectOwnership: s3.ObjectOwnership.OBJECT_WRITER,
        encryption: s3.BucketEncryption.S3_MANAGED,
        blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
        versioned: true,
        enforceSSL: true,
        ...s3BucketProps,
      }
    );

    const sourceCodeBucket = new s3.Bucket(
      this,
      `${projectName}-source-code-bucket`,
      {
        blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
        encryption: s3.BucketEncryption.S3_MANAGED,
        serverAccessLogsBucket: accessLogBucket,
        enforceSSL: true,
        versioned: true,
        serverAccessLogsPrefix: `${projectName}-source-code-bucket-access-logs`,
        ...s3BucketProps,
      }
    );

    // AWS Lambda Powertools Layer
    const powertoolsLayer = lambda.LayerVersion.fromLayerVersionArn(
      this,
      `${projectName}-powertools-layer`,
      `arn:aws:lambda:${this.region}:017000801446:layer:AWSLambdaPowertoolsPythonV2:68`
    );

    // Strands Agents SDK layer
    const strandsLayer = new lambda.LayerVersion(
      this,
      `${projectName}-strands-layer`,
      {
        code: lambda.Code.fromAsset(
          path.join(__dirname, "../layers/strands-layer")
        ),
        compatibleRuntimes: [lambda.Runtime.PYTHON_3_12],
        description: "Strands Agents layer for AI error analysis",
      }
    );

    // IAM role for Sample Business Function
    const sampleBusinessFunctionRole = new iam.Role(
      this,
      `${projectName}-sample-business-function-role`,
      {
        assumedBy: new iam.ServicePrincipal("lambda.amazonaws.com"),
        description: "Custom role for sample business function",
      }
    );

    // Add custom CloudWatch Logs permissions
    sampleBusinessFunctionRole.addToPolicy(
      new iam.PolicyStatement({
        actions: [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ],
        resources: [
          `arn:aws:logs:${this.region}:${this.account}:log-group:/aws/lambda/${projectName}-sample-business-function:*`,
        ],
      })
    );

    // Sample Business Function Lambda
    const sampleBusinessFunction = new lambda.Function(
      this,
      `${projectName}-sample-business-function`,
      {
        runtime: lambda.Runtime.PYTHON_3_12,
        code: lambda.Code.fromAsset(
          path.join(__dirname, "../lambda/sample-business-function")
        ),
        handler: "lambda_function.lambda_handler",
        functionName: `${projectName}-sample-business-function`,
        description:
          "Sample business function with @automation decorator for error simulation",
        timeout: Duration.seconds(120),
        memorySize: 512,
        architecture: lambda.Architecture.X86_64,
        layers: [powertoolsLayer],
        role: sampleBusinessFunctionRole,
      }
    );

    // IAM role for Error Analyzer Agent
    const errorAnalyzerAgentRole = new iam.Role(
      this,
      `${projectName}-error-analyzer-agent-role`,
      {
        assumedBy: new iam.ServicePrincipal("lambda.amazonaws.com"),
        description: "Custom role for error analyzer agent",
      }
    );

    // Add custom CloudWatch Logs permissions
    errorAnalyzerAgentRole.addToPolicy(
      new iam.PolicyStatement({
        actions: [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ],
        resources: [
          `arn:aws:logs:${this.region}:${this.account}:log-group:/aws/lambda/${projectName}-error-analyzer-agent:*`,
        ],
      })
    );

    // Error Analyzer Agent Lambda
    const errorAnalyzerAgent = new lambda.Function(
      this,
      `${projectName}-error-analyzer-agent`,
      {
        runtime: lambda.Runtime.PYTHON_3_12,
        code: lambda.Code.fromAsset(
          path.join(__dirname, "../lambda/error-analyzer-agent")
        ),
        handler: "lambda_function.lambda_handler",
        functionName: `${projectName}-error-analyzer-agent`,
        description:
          "AI-powered error analysis agent using Strands SDK and Amazon Bedrock",
        timeout: Duration.seconds(300),
        memorySize: 1024,
        architecture: lambda.Architecture.X86_64,
        layers: [strandsLayer],
        role: errorAnalyzerAgentRole,
        environment: {
          DYNAMODB_TABLE_NAME: errorAnalysisTable.tableName,
          SOURCE_CODE_BUCKET: sourceCodeBucket.bucketName,
          STORE_CLOUDWATCH_LOGS: "true",
          STORE_SOURCE_CODE: "true",
          USE_SONNET_4: "false",
        },
      }
    );

    // EventBridge permissions for Sample Business Function
    sampleBusinessFunctionRole.addToPolicy(
      new iam.PolicyStatement({
        actions: ["events:PutEvents"],
        resources: [
          `arn:aws:events:${this.region}:${this.account}:event-bus/default`,
        ],
      })
    );

    // Bedrock API permissions for Error Analyzer Agent
    errorAnalyzerAgentRole.addToPolicy(
      new iam.PolicyStatement({
        actions: [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
        ],
        resources: ["*"],
      })
    );

    // Knowledge Base permissions
    errorAnalyzerAgentRole.addToPolicy(
      new iam.PolicyStatement({
        actions: ["bedrock:Retrieve"],
        resources: [knowledgeBase.knowledgeBaseArn],
      })
    );

    // DynamoDB permissions
    errorAnalysisTable.grantReadWriteData(errorAnalyzerAgentRole);

    // CloudWatch Logs permissions
    errorAnalyzerAgentRole.addToPolicy(
      new iam.PolicyStatement({
        actions: [
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams",
          "logs:GetLogEvents",
          "logs:FilterLogEvents",
        ],
        resources: [
          `arn:aws:logs:${this.region}:${this.account}:log-group:/aws/lambda/*:*`,
        ],
      })
    );

    // SSM Parameter Store permissions
    errorAnalyzerAgentRole.addToPolicy(
      new iam.PolicyStatement({
        actions: ["ssm:GetParameter"],
        resources: [
          `arn:aws:ssm:${this.region}:${this.account}:parameter/${ssmParamDynamoDb}`,
          `arn:aws:ssm:${this.region}:${this.account}:parameter/${ssmParamKnowledgeBaseId}`,
        ],
      })
    );

    // S3 permissions
    sourceCodeBucket.grantRead(errorAnalyzerAgentRole);

    // Lambda function code access permissions
    errorAnalyzerAgentRole.addToPolicy(
      new iam.PolicyStatement({
        actions: ["lambda:GetFunction", "lambda:GetFunctionConfiguration"],
        resources: ["*"],
      })
    );

    // S3 data source for Knowledge Base - only index knowledge_base/ folder
    const sourceCodeDataSource = new bedrock.S3DataSource(
      this,
      `${projectName}-s3-data-source`,
      {
        bucket: sourceCodeBucket,
        knowledgeBase: knowledgeBase,
        dataSourceName: "lambda-source-code",
        chunkingStrategy: bedrock.ChunkingStrategy.FIXED_SIZE,
        maxTokens: 300,
        overlapPercentage: 20,
        inclusionPrefixes: ["knowledge_base/"], // Only index files in knowledge_base/ folder
      }
    );

    // Create SSM parameter with Knowledge Base ID
    new ssm.StringParameter(this, `${projectName}-kb-param`, {
      parameterName: `/${ssmParamKnowledgeBaseId}`,
      stringValue: knowledgeBase.knowledgeBaseId,
      description: "Knowledge Base ID for error analysis",
    });

    // Set Knowledge Base ID environment variable
    errorAnalyzerAgent.addEnvironment(
      "KNOWLEDGE_BASE_ID",
      knowledgeBase.knowledgeBaseId
    );

    // Deploy Lambda code to S3
    new s3deployment.BucketDeployment(
      this,
      `${projectName}-sample-business-function-deployment`,
      {
        sources: [
          s3deployment.Source.asset(
            path.join(__dirname, "../lambda/sample-business-function")
          ),
        ],
        destinationBucket: sourceCodeBucket,
        destinationKeyPrefix: `lambdas/${projectName}-sample-business-function/`,
      }
    );


    new s3deployment.BucketDeployment(
      this,
      `${projectName}-error-analyzer-agent-deployment`,
      {
        sources: [
          s3deployment.Source.asset(
            path.join(__dirname, "../lambda/error-analyzer-agent")
          ),
        ],
        destinationBucket: sourceCodeBucket,
        destinationKeyPrefix: `lambdas/${projectName}-error-analyzer-agent/`,
      }
    );


    const knowledgeBaseDeployment = new s3deployment.BucketDeployment(
      this,
      `${projectName}-knowledge-base-deployment`,
      {
        sources: [
          s3deployment.Source.asset(
            path.join(__dirname, "../../knowledge_base")
          ),
        ],
        destinationBucket: sourceCodeBucket,
        destinationKeyPrefix: "knowledge_base/",
      }
    );

    // EventBridge Rule to trigger Error Analyzer Agent on task events
    const taskEventRule = new events.Rule(
      this,
      `${projectName}-task-event-rule`,
      {
        ruleName: `${projectName}-task-events`,
        description:
          "Trigger error analyzer agent when task events are published",
        eventPattern: {
          detailType: ["TaskFailed", "TaskSucceeded", "TaskUpdate"],
          source: events.Match.wildcard("lambda.*"),
        },
      }
    );


    taskEventRule.addTarget(new targets.LambdaFunction(errorAnalyzerAgent));

    // CloudFormation Outputs
    new cdk.CfnOutput(this, "KnowledgeBaseId", {
      value: knowledgeBase.knowledgeBaseId,
      description: "Knowledge Base ID",
    });

    new cdk.CfnOutput(this, "SourceCodeBucketName", {
      value: sourceCodeBucket.bucketName,
      description: "Source Code S3 Bucket Name",
    });

    new cdk.CfnOutput(this, "DataSourceId", {
      value: sourceCodeDataSource.dataSourceId,
      description: "Knowledge Base Data Source ID",
    });

    // CDK Nag Suppressions

    NagSuppressions.addResourceSuppressionsByPath(
      this,
      `/${projectName}Stack/${projectName}-sample-business-function-role/DefaultPolicy/Resource`,
      [
        {
          id: "AwsSolutions-IAM5",
          reason:
            "CloudWatch Logs requires wildcard for log streams within the function's log group.",
          appliesTo: [
            `Resource::arn:aws:logs:${this.region}:${this.account}:log-group:/aws/lambda/${projectName}-sample-business-function:*`,
          ],
        },
      ]
    );

    // Error Analyzer Agent - IAM role wildcards
    NagSuppressions.addResourceSuppressionsByPath(
      this,
      `/${projectName}Stack/${projectName}-error-analyzer-agent-role/DefaultPolicy/Resource`,
      [
        {
          id: "AwsSolutions-IAM5",
          reason:
            "Wildcards required for error analysis functionality: " +
            "1) Bedrock InvokeModel - model ARNs vary by region and version " +
            "2) Lambda GetFunction - analyzes any Lambda function dynamically " +
            "3) CloudWatch Logs - reads logs from any Lambda function " +
            "4) S3 GetObject - reads source code files from bucket",
          appliesTo: [
            "Resource::*",
            `Resource::arn:aws:logs:${this.region}:${this.account}:log-group:/aws/lambda/*:*`,
            `Resource::arn:aws:logs:${this.region}:${this.account}:log-group:/aws/lambda/${projectName}-error-analyzer-agent:*`,
            "Action::s3:GetBucket*",
            "Action::s3:GetObject*",
            "Action::s3:List*",
            "Resource::<LambdaErrorAnalysissourcecodebucketA1856DD0.Arn>/*",
          ],
        },
      ]
    );

    // CDK-generated helper resources (LogRetention, BucketDeployment, OpenSearchIndexCRProvider, Custom Resource Providers)
    // These are created automatically by CDK constructs and use standard CDK patterns
    NagSuppressions.addStackSuppressions(
      this,
      [
        {
          id: "AwsSolutions-IAM4",
          reason:
            "CDK-generated helper functions use AWS managed policies (AWSLambdaBasicExecutionRole). " +
            "These are maintained by the CDK team and follow AWS best practices.",
        },
        {
          id: "AwsSolutions-IAM5",
          reason:
            "CDK-generated helper functions require wildcard permissions for deployment operations: " +
            "S3 operations (GetBucket*, GetObject*, List*, Abort*, DeleteObject*), " +
            "CloudWatch Logs operations, and resource management during stack updates.",
        },
        {
          id: "AwsSolutions-L1",
          reason:
            "CDK-generated helper functions use CDK-managed runtimes. " +
            "These are automatically updated and maintained by the AWS CDK team.",
        },
      ],
      true // applyToChildren - applies to all resources in the stack
    );
  }
}
