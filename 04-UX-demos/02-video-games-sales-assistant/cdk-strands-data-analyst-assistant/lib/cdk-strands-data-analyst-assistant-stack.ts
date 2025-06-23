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

export class CdkStrandsDataAnalystAssistantStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const projectId = new cdk.CfnParameter(this, "ProjectId", {
      type: "String",
      description: "Project identifier used for naming resources",
      default: "strands-data-analyst-assistant",
    });

    const databaseName = new cdk.CfnParameter(this, "DatabaseName", {
      type: "String",
      description: "Nombre de la base de datos",
      default: "video_games_sales",
    });

    // Add a new parameter for max response size in bytes
    const maxResponseSize = new cdk.CfnParameter(this, "MaxResponseSize", {
      type: "Number",
      description: "Maximum size for row query results in bytes",
      default: 25600, // 25K default
    });

    // Add new parameters for Fargate task configuration
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

    // Create the DynamoDB table for raw query results
    const rawQueryResults = new dynamodb.Table(this, "RawQueryResults", {
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

    // Create the conversation table
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

    // Keep only gateway endpoints, removing all interface endpoints
    vpc.addGatewayEndpoint("S3Endpoint", {
      service: ec2.GatewayVpcEndpointAwsService.S3,
      subnets: [{ subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS }],
    });

    vpc.addGatewayEndpoint("DynamoDBEndpoint", {
      service: ec2.GatewayVpcEndpointAwsService.DYNAMODB,
      subnets: [{ subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS }],
    });

    const sg_db_proxy = new ec2.SecurityGroup(
      this,
      "AssistantDBSecurityGroup",
      {
        vpc: vpc,
        allowAllOutbound: true,
      }
    );

    sg_db_proxy.addIngressRule(
      sg_db_proxy,
      ec2.Port.tcp(5432),
      "Allow PostgreSQL connections"
    );

    const databaseUsername = "postgres";

    const secret = new rds.DatabaseSecret(this, "AssistantSecret", {
      username: databaseUsername,
      secretName: `${projectId.valueAsString}-db-secret`,
    });

    // Create IAM role for Aurora to access S3
    const auroraS3Role = new iam.Role(this, "AuroraS3Role", {
      assumedBy: new iam.ServicePrincipal("rds.amazonaws.com"),
    });

    let cluster = new rds.DatabaseCluster(this, "AssistantCluster", {
      engine: rds.DatabaseClusterEngine.auroraPostgres({
        version: rds.AuroraPostgresEngineVersion.VER_15_4,
      }),
      writer: rds.ClusterInstance.serverlessV2("writer"),
      serverlessV2MinCapacity: 2,
      serverlessV2MaxCapacity: 4,
      defaultDatabaseName: databaseName.valueAsString,
      vpc,
      vpcSubnets: {
        subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
      },
      securityGroups: [sg_db_proxy],
      credentials: rds.Credentials.fromSecret(secret),
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      enableDataApi: true,
      s3ImportRole: auroraS3Role,
    });

    // Grant S3 access to the role
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

    // Add additional RDS permissions similar to your CloudFormation template
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

    const proxy = cluster.addProxy("AssistantProxy", {
      dbProxyName: `${projectId.valueAsString}-db-proxy`,
      secrets: [secret],
      debugLogging: true,
      vpc,
      securityGroups: [sg_db_proxy],
      requireTLS: false,
      iamAuth: false,
    });

    // S3 bucket for temporal resources to use with aws_s3.table_import_from_s3
    const importBucket = new s3.Bucket(this, "ImportBucket", {
      bucketName: `${projectId.valueAsString}-${this.region}-${this.account}-import`,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
      lifecycleRules: [
        {
          expiration: cdk.Duration.days(7), // Auto-delete objects after 7 days
        },
      ],
    });

    // =================== FARGATE SERVICE SETUP ===================

    // Create ECS Cluster
    const ecsCluster = new ecs.Cluster(this, "AgentCluster", {
      vpc: vpc,
      clusterName: `${projectId.valueAsString}-cluster`,
      containerInsightsV2: ecs.ContainerInsights.ENHANCED,
    });

    // Create log group for Fargate service
    const logGroup = new logs.LogGroup(this, "AgentLogGroup", {
      logGroupName: `/ecs/${projectId.valueAsString}-agent-service`,
      retention: logs.RetentionDays.ONE_MONTH,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // Create execution role for Fargate task
    const executionRole = new iam.Role(this, "AgentTaskExecutionRole", {
      assumedBy: new iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
      roleName: `${projectId.valueAsString}-task-execution-role`,
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName(
          "service-role/AmazonECSTaskExecutionRolePolicy"
        ),
      ],
    });

    // Create task role for Fargate task
    const taskRole = new iam.Role(this, "AgentTaskRole", {
      assumedBy: new iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
      roleName: `${projectId.valueAsString}-task-role`,
    });

    // Add Bedrock permissions to task role
    taskRole.addToPolicy(
      new iam.PolicyStatement({
        actions: [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
        ],
        resources: ["*"],
      })
    );

    // Add permissions to access the database
    taskRole.addToPolicy(
      new iam.PolicyStatement({
        actions: ["rds-db:connect", "secretsmanager:GetSecretValue"],
        resources: [
          secret.secretArn,
          `arn:aws:rds-db:${this.region}:${this.account}:dbuser:*/${databaseUsername}`,
        ],
      })
    );

    // Add permissions to put/update items in DynamoDB
    taskRole.addToPolicy(
      new iam.PolicyStatement({
        actions: [
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:BatchWriteItem",
          "dynamodb:GetItem",
          "dynamodb:Query"
        ],
        resources: [rawQueryResults.tableArn, conversationTable.tableArn],
      })
    );

    // Create a task definition with parameterized CPU and memory
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

    // This will use the Dockerfile in the docker directory
    const dockerAsset = new ecrAssets.DockerImageAsset(this, "AgentImage", {
      directory: path.join(__dirname, "../docker"),
      file: "./Dockerfile",
      platform: ecrAssets.Platform.LINUX_ARM64,
    });

    // Define the container port
    const containerPort = 8000;

    // Add container to the task definition
    const container = taskDefinition.addContainer("AgentContainer", {
      image: ecs.ContainerImage.fromDockerImageAsset(dockerAsset),
      logging: ecs.LogDrivers.awsLogs({
        streamPrefix: "agent-service",
        logGroup,
      }),
      environment: {
        // Add any environment variables needed by your application
        SECRET_NAME: `${projectId.valueAsString}-db-secret`,
        DATABASE_NAME: databaseName.valueAsString,
        POSTGRESQL_HOST: proxy.endpoint,
        AWS_REGION: this.region,
        RAW_QUERY_RESULTS_TABLE_NAME: rawQueryResults.tableName,
        CONVERSATION_TABLE_NAME: conversationTable.tableName,
        MAX_RESPONSE_SIZE_BYTES: maxResponseSize.valueAsString,
      },
      portMappings: [
        {
          containerPort: containerPort,
          hostPort: containerPort,
          protocol: ecs.Protocol.TCP,
        },
      ],
    });

    // Create a security group for the Fargate service
    const agentServiceSG = new ec2.SecurityGroup(this, "AgentServiceSG", {
      vpc,
      description: "Security group for Agent Fargate Service",
      allowAllOutbound: true,
    });

    sg_db_proxy.addIngressRule(
      agentServiceSG,
      ec2.Port.tcp(5432),
      "Allow PostgreSQL connections"
    );

    // Create a Fargate service with parameterized desired count
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

    // =================== ADD APPLICATION LOAD BALANCER ===================

    // Create a security group for the ALB
    const albSG = new ec2.SecurityGroup(this, "AlbSecurityGroup", {
      vpc,
      description: "Security group for Agent Application Load Balancer",
      allowAllOutbound: true,
    });

    // Allow inbound HTTP traffic to the ALB on port 80
    albSG.addIngressRule(
      ec2.Peer.anyIpv4(),
      ec2.Port.tcp(80),
      "Allow HTTP traffic on port 80 from anywhere"
    );

    // Allow the ALB to communicate with the Fargate service
    agentServiceSG.addIngressRule(
      albSG,
      ec2.Port.tcp(containerPort),
      `Allow traffic from ALB to Fargate service on port ${containerPort}`
    );

    // Create an Application Load Balancer
    const lb = new elbv2.ApplicationLoadBalancer(this, "AgentLB", {
      vpc,
      internetFacing: true,
    });

    // Create a listener
    const listener = lb.addListener("AgentListener", {
      port: 80,
    });

    // Add target group to the listener
    listener.addTargets("AgentTargets", {
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

    // Stack outputs

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
      value: rawQueryResults.tableName,
      description: "The name of the DynamoDB table for storing query results",
      exportName: `${projectId.valueAsString}-QuestionAnswersTableName`,
    });

    new cdk.CfnOutput(this, "AgentEndpointURL", {
      value: lb.loadBalancerDnsName,
      description: "The DNS name of the Application Load Balancer for the Strands Agent",
      exportName: `${projectId.valueAsString}-LoadBalancerDnsName`,
    });
  }
}
