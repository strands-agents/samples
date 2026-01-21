import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as rds from "aws-cdk-lib/aws-rds";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as ecs from "aws-cdk-lib/aws-ecs";
import * as logs from "aws-cdk-lib/aws-logs";
import * as iam from "aws-cdk-lib/aws-iam";
import * as ecrAssets from "aws-cdk-lib/aws-ecr-assets";
import * as elbv2 from "aws-cdk-lib/aws-elasticloadbalancingv2";
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as path from "path";
import { Duration } from "aws-cdk-lib";
import * as ssm from 'aws-cdk-lib/aws-ssm';


// Strands Data Analyst Assistant Stack
export class CdkStrandsDataAnalystAssistantStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Parameters
    const projectId = new cdk.CfnParameter(this, "ProjectId", {
      type: "String",
      description: "Project identifier used for naming resources",
      default: "strands-data-analyst-assistant",
    });

    const databaseName = new cdk.CfnParameter(this, "DatabaseName", {
      type: "String",
      description: "Database name for video games sales data",
      default: "video_games_sales",
    });

    // Query response size limit
    const maxResponseSize = new cdk.CfnParameter(this, "MaxResponseSize", {
      type: "Number",
      description: "Maximum size for row query results in bytes",
      default: 25600, // 25K default
    });

    // Fargate configuration
    const taskCpu = new cdk.CfnParameter(this, "TaskCpu", {
      type: "Number",
      description:
        "CPU units for Fargate task (256=0.25vCPU, 512=0.5vCPU, 1024=1vCPU, 2048=2vCPU, 4096=4vCPU)",
      default: 2048,
    });

    const taskMemory = new cdk.CfnParameter(this, "TaskMemory", {
      type: "Number",
      description: "Memory (in MiB) for Fargate task",
      default: 4096,
    });

    const serviceDesiredCount = new cdk.CfnParameter(
      this,
      "ServiceDesiredCount",
      {
        type: "Number",
        description: "Desired count of tasks for the Fargate service",
        default: 1,
        minValue: 1,
        maxValue: 10,
      }
    );

    const lastNumberOfMessages = new cdk.CfnParameter(
      this,
      "LastNumberOfMessages",
      {
        type: "Number",
        description: "Number of last messages to retrieve from chat history",
        default: 20,
        minValue: 1,
        maxValue: 100,
      }
    );

    const webApplicationUrl = new cdk.CfnParameter(this, "WebApplicationUrl", {
      type: "String",
      description: "URL of the web application frontend",
      default: "http://localhost:3000",
    });

    // Cognito parameter
    const cognitoUserPoolId = new cdk.CfnParameter(this, "CognitoUserPoolId", {
      type: "String",
      description: "Cognito User Pool ID for frontend authentication",
      default: "N/A",
    });

    // DynamoDB tables
    const rawQueryResultsTable = new dynamodb.Table(this, "rawQueryResultsTableTable", {
      partitionKey: {
        name: "id",
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: "my_timestamp",
        type: dynamodb.AttributeType.NUMBER,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      encryption: dynamodb.TableEncryption.AWS_MANAGED,
      removalPolicy: cdk.RemovalPolicy.DESTROY
    });

    // Conversation table
    const conversationTable = new dynamodb.Table(this, 'ConversationTable', {
      partitionKey: {
        name: 'session_id',
        type: dynamodb.AttributeType.STRING
      },
      sortKey: {
        name: "message_id",
        type: dynamodb.AttributeType.NUMBER,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      encryption: dynamodb.TableEncryption.AWS_MANAGED,
      removalPolicy: cdk.RemovalPolicy.DESTROY
    });

    // VPC
    const vpc = new ec2.Vpc(this, "AssistantVPC", {
      vpcName: `${projectId.valueAsString}-vpc`,
      ipAddresses: ec2.IpAddresses.cidr("10.0.0.0/21"),
      maxAzs: 3,
      natGateways: 1,
      subnetConfiguration: [
        {
          subnetType: ec2.SubnetType.PUBLIC,
          name: "Ingress",
          cidrMask: 24,
        },
        {
          cidrMask: 24,
          name: "Private",
          subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
        },
      ],
    });

    // VPC endpoints
    vpc.addGatewayEndpoint("S3Endpoint", {
      service: ec2.GatewayVpcEndpointAwsService.S3,
      subnets: [{ subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS }],
    });

    vpc.addGatewayEndpoint("DynamoDBEndpoint", {
      service: ec2.GatewayVpcEndpointAwsService.DYNAMODB,
      subnets: [{ subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS }],
    });

    // Database security group
    const sg_db = new ec2.SecurityGroup(
      this,
      "AssistantDBSecurityGroup",
      {
        vpc: vpc,
        allowAllOutbound: true,
        description: "Security group for Aurora PostgreSQL cluster"
      }
    );

    const databaseUsername = "postgres";

    const secret = new rds.DatabaseSecret(this, "AssistantSecret", {
      username: databaseUsername,
      secretName: `${projectId.valueAsString}-db-secret`,
    });

    // Aurora S3 role
    const auroraS3Role = new iam.Role(this, "AuroraS3Role", {
      assumedBy: new iam.ServicePrincipal("rds.amazonaws.com"),
    });

    let cluster = new rds.DatabaseCluster(this, "AssistantCluster", {
      engine: rds.DatabaseClusterEngine.auroraPostgres({
        version: rds.AuroraPostgresEngineVersion.VER_17_4,
      }),
      writer: rds.ClusterInstance.serverlessV2("writer"),
      serverlessV2MinCapacity: 2,
      serverlessV2MaxCapacity: 4,
      defaultDatabaseName: databaseName.valueAsString,
      vpc,
      vpcSubnets: {
        subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
      },
      securityGroups: [sg_db],
      credentials: rds.Credentials.fromSecret(secret),
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      enableDataApi: true,
      s3ImportRole: auroraS3Role,
      storageEncrypted: true,
    });

    // S3 permissions
    auroraS3Role.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ["s3:GetObject", "s3:ListBucket", "s3:GetBucketLocation"],
        resources: [
          `arn:aws:s3:::${projectId.valueAsString}-${this.region}-${this.account}-import`,
          `arn:aws:s3:::${projectId.valueAsString}-${this.region}-${this.account}-import/*`,
        ],
      })
    );

    // RDS permissions
    auroraS3Role.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          "rds:CreateDBSnapshot",
          "rds:CreateDBClusterSnapshot",
          "rds:RestoreDBClusterFromSnapshot",
          "rds:RestoreDBClusterToPointInTime",
          "rds:RestoreDBInstanceFromDBSnapshot",
          "rds:RestoreDBInstanceToPointInTime",
        ],
        resources: [cluster.clusterArn],
      })
    );

    // S3 import bucket
    const importBucket = new s3.Bucket(this, "ImportBucket", {
      bucketName: `${projectId.valueAsString}-${this.region}-${this.account}-import`,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
      lifecycleRules: [
        {
          expiration: cdk.Duration.days(7),
        },
      ],
    });

    // SSM parameters

    new ssm.CfnParameter(this, 'SecretArnParameter', {
      name: cdk.Fn.sub('/${ProjectId}/SECRET_ARN', { ProjectId: projectId.valueAsString }),
      value: secret.secretArn,
      description: 'ARN of the database credentials secret',
      type: 'String'
    });

    new ssm.CfnParameter(this, 'ClusterArnParameter', {
      name: cdk.Fn.sub('/${ProjectId}/AURORA_RESOURCE_ARN', { ProjectId: projectId.valueAsString }),
      value: cluster.clusterArn,
      description: 'ARN of the Aurora Serverless DB Cluster',
      type: 'String'
    });

    new ssm.CfnParameter(this, 'DatabaseNameParameter', {
      name: cdk.Fn.sub('/${ProjectId}/DATABASE_NAME', { ProjectId: projectId.valueAsString }),
      value: databaseName.valueAsString,
      description: 'Database name for video games sales data',
      type: 'String'
    });

    new ssm.CfnParameter(this, 'DatabaseUsernameParameter', {
      name: cdk.Fn.sub('/${ProjectId}/DATABASE_USERNAME', { ProjectId: projectId.valueAsString }),
      value: databaseUsername,
      description: 'Database username for IAM authentication',
      type: 'String'
    });

    new ssm.CfnParameter(this, 'rawQueryResultsTableTableParameter', {
      name: cdk.Fn.sub('/${ProjectId}/RAW_QUERY_RESULTS_TABLE_NAME', { ProjectId: projectId.valueAsString }),
      value: rawQueryResultsTable.tableName,
      description: 'DynamoDB table name for storing query results',
      type: 'String'
    });

    new ssm.CfnParameter(this, 'ConversationTableParameter', {
      name: cdk.Fn.sub('/${ProjectId}/CONVERSATION_TABLE_NAME', { ProjectId: projectId.valueAsString }),
      value: conversationTable.tableName,
      description: 'DynamoDB table name for storing conversation history',
      type: 'String'
    });

    new ssm.CfnParameter(this, 'MaxResponseSizeParameter', {
      name: cdk.Fn.sub('/${ProjectId}/MAX_RESPONSE_SIZE_BYTES', { ProjectId: projectId.valueAsString }),
      value: maxResponseSize.valueAsString,
      description: 'Maximum size for row query results in bytes',
      type: 'String'
    });

    new ssm.CfnParameter(this, 'LastNumberOfMessagesParameter', {
      name: cdk.Fn.sub('/${ProjectId}/LAST_NUMBER_OF_MESSAGES', { ProjectId: projectId.valueAsString }),
      value: lastNumberOfMessages.valueAsString,
      description: 'Number of last messages to retrieve from chat history',
      type: 'String'
    });



    // ECS cluster
    const ecsCluster = new ecs.Cluster(this, "AgentCluster", {
      vpc: vpc,
      clusterName: `${projectId.valueAsString}-cluster`,
      containerInsightsV2: ecs.ContainerInsights.ENHANCED,
    });

    // Log group
    const logGroup = new logs.LogGroup(this, "AgentLogGroup", {
      logGroupName: `/ecs/${projectId.valueAsString}-agent-service`,
      retention: logs.RetentionDays.ONE_MONTH,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // Task execution role
    const executionRole = new iam.Role(this, "AgentTaskExecutionRole", {
      assumedBy: new iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
      roleName: `${projectId.valueAsString}-${this.region}-task-execution-role`,
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName(
          "service-role/AmazonECSTaskExecutionRolePolicy"
        ),
      ],
    });

    // Task role
    const taskRole = new iam.Role(this, "AgentTaskRole", {
      assumedBy: new iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
      roleName: `${projectId.valueAsString}-${this.region}-task-role`,
    });

    // Bedrock permissions
    taskRole.addToPolicy(
      new iam.PolicyStatement({
        actions: [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
        ],
        resources: ["*"],
      })
    );

    // RDS Data API permissions
    taskRole.addToPolicy(
      new iam.PolicyStatement({
        actions: [
          "rds-data:ExecuteStatement",
          "rds-data:BatchExecuteStatement",
          "rds-data:BeginTransaction",
          "rds-data:CommitTransaction",
          "rds-data:RollbackTransaction",
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ],
        resources: [
          secret.secretArn,
          cluster.clusterArn,
        ],
      })
    );

    // DynamoDB permissions
    taskRole.addToPolicy(
      new iam.PolicyStatement({
        actions: [
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:BatchWriteItem",
          "dynamodb:GetItem",
          "dynamodb:Query"
        ],
        resources: [rawQueryResultsTable.tableArn, conversationTable.tableArn],
      })
    );

    // SSM permissions
    taskRole.addToPolicy(
      new iam.PolicyStatement({
        sid: 'SSMParameterAccess',
        effect: iam.Effect.ALLOW,
        actions: [
          'ssm:GetParameter',
          'ssm:GetParameters'
        ],
        resources: [`arn:aws:ssm:${this.region}:${this.account}:parameter/${projectId.valueAsString}/*`]
      })
    );

    // Task definition
    const taskDefinition = new ecs.FargateTaskDefinition(
      this,
      "AgentTaskDefinition",
      {
        memoryLimitMiB: taskMemory.valueAsNumber,
        cpu: taskCpu.valueAsNumber,
        executionRole,
        taskRole,
        runtimePlatform: {
          cpuArchitecture: ecs.CpuArchitecture.ARM64,
          operatingSystemFamily: ecs.OperatingSystemFamily.LINUX,
        },
      }
    );

    // Docker image
    const dockerAsset = new ecrAssets.DockerImageAsset(this, "AgentImage", {
      directory: path.join(__dirname, "../docker"),
      file: "./Dockerfile",
      platform: ecrAssets.Platform.LINUX_ARM64,
    });

    // Container port
    const containerPort = 8000;

    // Container
    const container = taskDefinition.addContainer("AgentContainer", {
      image: ecs.ContainerImage.fromDockerImageAsset(dockerAsset),
      logging: ecs.LogDrivers.awsLogs({
        streamPrefix: "agent-service",
        logGroup,
      }),
      environment: {
        PROJECT_ID: projectId.valueAsString,
        COGNITO_USER_POOL_ID: cognitoUserPoolId.valueAsString,
        WEB_APPLICATION_URL: webApplicationUrl.valueAsString,
      },
      portMappings: [
        {
          containerPort: containerPort,
          hostPort: containerPort,
          protocol: ecs.Protocol.TCP,
        },
      ],
    });

    // Fargate security group
    const agentServiceSG = new ec2.SecurityGroup(this, "AgentServiceSG", {
      vpc,
      description: "Security group for Agent Fargate Service",
      allowAllOutbound: true,
    });



    // Fargate service
    const service = new ecs.FargateService(this, "AgentService", {
      cluster: ecsCluster,
      taskDefinition,
      desiredCount: serviceDesiredCount.valueAsNumber,
      assignPublicIp: false,
      vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS },
      circuitBreaker: {
        rollback: true,
      },
      securityGroups: [agentServiceSG],
      minHealthyPercent: 100,
      maxHealthyPercent: 200,
      healthCheckGracePeriod: Duration.seconds(60),
    });

    // ALB security group
    const albSG = new ec2.SecurityGroup(this, "AlbSecurityGroup", {
      vpc,
      description: "Security group for Agent Application Load Balancer",
      allowAllOutbound: true,
    });

    // HTTP access
    albSG.addIngressRule(
      ec2.Peer.anyIpv4(),
      ec2.Port.tcp(80),
      "Allow HTTP traffic on port 80 from anywhere"
    );

    // HTTPS access
    albSG.addIngressRule(
      ec2.Peer.anyIpv4(),
      ec2.Port.tcp(443),
      "Allow HTTPS traffic on port 443 from anywhere"
    );

    // ALB to Fargate access
    agentServiceSG.addIngressRule(
      albSG,
      ec2.Port.tcp(containerPort),
      `Allow traffic from ALB to Fargate service on port ${containerPort}`
    );

    // Load balancer
    const lb = new elbv2.ApplicationLoadBalancer(this, "AgentLB", {
      vpc,
      internetFacing: true,
    });

    // HTTP listener
    const listener = lb.addListener("AgentListener", {
      port: 80,
    });

    // Target group
    const targetGroup = listener.addTargets("AgentTargets", {
      port: containerPort,
      targets: [service],
      healthCheck: {
        path: "/health",
        interval: Duration.seconds(30),
        timeout: Duration.seconds(5),
        healthyHttpCodes: "200",
      },
      deregistrationDelay: Duration.seconds(30),
    });

    // Configure target group attributes for streaming responses
    targetGroup.setAttribute("load_balancing.algorithm.type", "least_outstanding_requests");
    targetGroup.setAttribute("target_group_health.unhealthy_state_routing.minimum_healthy_targets.count", "1");
    targetGroup.setAttribute("target_group_health.unhealthy_state_routing.minimum_healthy_targets.percentage", "off");
    targetGroup.setAttribute('stickiness.enabled', 'true');
    targetGroup.setAttribute('stickiness.type', 'lb_cookie');
    targetGroup.setAttribute('stickiness.lb_cookie.duration_seconds', '86400');

    // Outputs

    new cdk.CfnOutput(this, "AuroraServerlessDBClusterARN", {
      value: cluster.clusterArn,
      description: "The ARN of the Aurora Serverless DB Cluster",
      exportName: `${projectId.valueAsString}-AuroraServerlessDBClusterARN`,
    });

    new cdk.CfnOutput(this, "SecretARN", {
      value: secret.secretArn,
      description: "The ARN of the database credentials secret",
      exportName: `${projectId.valueAsString}-SecretArn`,
    });

    new cdk.CfnOutput(this, "DataSourceBucketName", {
      value: importBucket.bucketName,
      description:
        "S3 bucket for importing data into Aurora using aws_s3 extension",
      exportName: `${projectId.valueAsString}-ImportBucketName`,
    });

    new cdk.CfnOutput(this, "QuestionAnswersTableName", {
      value: rawQueryResultsTable.tableName,
      description: "The name of the DynamoDB table for storing query results",
      exportName: `${projectId.valueAsString}-QuestionAnswersTableName`,
    });

    new cdk.CfnOutput(this, "ConversationTableName", {
      value: conversationTable.tableName,
      description: "The name of the DynamoDB table for storing conversation history",
      exportName: `${projectId.valueAsString}-ConversationTableName`,
    });

    new cdk.CfnOutput(this, "AgentEndpointURL", {
      value: lb.loadBalancerDnsName,
      description: "The DNS name of the Application Load Balancer for the Strands Agent",
      exportName: `${projectId.valueAsString}-LoadBalancerDnsName`,
    });

  }
}