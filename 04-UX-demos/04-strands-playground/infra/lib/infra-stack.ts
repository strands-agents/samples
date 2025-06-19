import { Stack, StackProps, Duration, RemovalPolicy } from "aws-cdk-lib";
import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as logs from "aws-cdk-lib/aws-logs";
import * as elbv2 from "aws-cdk-lib/aws-elasticloadbalancingv2";
import * as dynamo from "aws-cdk-lib/aws-dynamodb";
import * as ecrAssets from "aws-cdk-lib/aws-ecr-assets";
import * as path from "path";

import { Construct } from 'constructs';
// import * as sqs from 'aws-cdk-lib/aws-sqs';

export class InfraStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const PRIMARY_KEY = "sessionID";

    // Create a new VPC with public and private subnets
    const vpc = new ec2.Vpc(this, 'VPC', {
      maxAzs: 2,
      natGateways: 1
    });

    // Create an ECS cluster
    const cluster = new ecs.Cluster(this, "AgentCluster", {
      vpc,
    });

    // Create a dynamodb table
    const table = new dynamo.Table(this, "AgentTable", {
      partitionKey: {
        name: PRIMARY_KEY,
        type: dynamo.AttributeType.STRING,
      },
      billingMode: dynamo.BillingMode.PAY_PER_REQUEST,
      timeToLiveAttribute: "TTL",
      removalPolicy: RemovalPolicy.DESTROY,
    });

    // Create a log group for the container
    const logGroup = new logs.LogGroup(this, "AgentServiceLogs", {
      retention: logs.RetentionDays.ONE_WEEK,
    });

    // Create a task execution role
    const executionRole = new iam.Role(this, "AgentTaskExecutionRole", {
      assumedBy: new iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
      managedPolicies: [iam.ManagedPolicy.fromAwsManagedPolicyName("service-role/AmazonECSTaskExecutionRolePolicy")],
    });

    // Create a task role with permissions to invoke Bedrock APIs
    const taskRole = new iam.Role(this, "AgentTaskRole", {
      assumedBy: new iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
    });

    // Add permissions for the task to invoke Bedrock APIs
    taskRole.addToPolicy(
      new iam.PolicyStatement({
        actions: ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
        resources: ["*"],
      }),
    );

    // Grant ECS task role access to dynamoDB for session management
    table.grantReadWriteData(taskRole)

    // Create a task definition
    const taskDefinition = new ecs.FargateTaskDefinition(this, "AgentTaskDefinition", {
      memoryLimitMiB: 512,
      cpu: 256,
      executionRole,
      taskRole,
      runtimePlatform: {
        cpuArchitecture: ecs.CpuArchitecture.X86_64,
        operatingSystemFamily: ecs.OperatingSystemFamily.LINUX,
      },
    });

    // This will use the Dockerfile in the docker directory
    const dockerAsset = new ecrAssets.DockerImageAsset(this, "AgentImage", {
      directory: path.join(__dirname, "../../app"),
      file: "./Dockerfile",
      platform: ecrAssets.Platform.LINUX_AMD64,
    });

    // Add container to the task definition
    taskDefinition.addContainer("AgentContainer", {
      image: ecs.ContainerImage.fromDockerImageAsset(dockerAsset),
      logging: ecs.LogDrivers.awsLogs({
        streamPrefix: "agent-service",
        logGroup,
      }),
      environment: {
        LOG_LEVEL: "INFO",
        TABLE_NAME: table.tableName,
        TABLE_REGION: this.region,
        PRIMARY_KEY: PRIMARY_KEY
      },
      portMappings: [
        {
          containerPort: 8003, // The port your application listens on
          protocol: ecs.Protocol.TCP,
        },
      ],
    });
    // Create a Fargate service
    const service = new ecs.FargateService(this, "AgentService", {
      cluster,
      taskDefinition,
      desiredCount: 2, // Run 2 instances for high availability
      assignPublicIp: false, // Use private subnets with NAT gateway
      vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS },
      circuitBreaker: {
        rollback: true,
      },
      securityGroups: [
        new ec2.SecurityGroup(this, "AgentServiceSG", {
          vpc,
          description: "Security group for Agent Fargate Service",
          allowAllOutbound: true,
        }),
      ],
      minHealthyPercent: 100,
      maxHealthyPercent: 200,
      healthCheckGracePeriod: Duration.seconds(60),
    });

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
      port: 8003,
      protocol: elbv2.ApplicationProtocol.HTTP,
      targets: [service],
      healthCheck: {
        path: "/health",
        interval: Duration.seconds(30),
        timeout: Duration.seconds(5),
        healthyHttpCodes: "200",
      },
      deregistrationDelay: Duration.seconds(30),
    });

    // Output the load balancer DNS name
    this.exportValue(lb.loadBalancerDnsName, {
      name: "AgentServiceEndpoint",
      description: "The DNS name of the load balancer for the Agent Service",
    });

    cdk.Tags.of(this).add('Project', 'Simple-Agentic-Strands-Chatbot')
  }
}
