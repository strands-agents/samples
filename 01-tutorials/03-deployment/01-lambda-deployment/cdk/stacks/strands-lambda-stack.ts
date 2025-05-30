import { Duration, Stack, StackProps } from "aws-cdk-lib";
import { Construct } from "constructs";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as iam from "aws-cdk-lib/aws-iam";
import * as path from "path";
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { envNameType, projectName, s3BucketProps, ssmParamDynamoDb, ssmParamKnowledgeBaseId } from '../constant';
import { setSecureTransport } from '../utility';
import { NagSuppressions } from 'cdk-nag';
import * as ecrAssets from 'aws-cdk-lib/aws-ecr-assets';

interface StrandsLambdaStackProps extends StackProps {
  envName: envNameType;
}

export class StrandsLambdaStack extends Stack {
  constructor(scope: Construct, id: string, props: StrandsLambdaStackProps) {
    super(scope, id, props);

    const knowledgeBaseId = ssm.StringParameter.fromStringParameterName(
      this,
      `${projectName}-knowledge-base-id`,
      `/${ssmParamKnowledgeBaseId}`,
    );

    const dynamoDBName = ssm.StringParameter.fromStringParameterName(
      this,
      `${projectName}-dynamo-db-name`,
      `/${ssmParamDynamoDb}`,
    );

     const accessLogBucket = new s3.Bucket(this, `${projectName}-access-bucket-access-logs`, {
      objectOwnership: s3.ObjectOwnership.OBJECT_WRITER,
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      versioned: true,
      enforceSSL: true,
      ...s3BucketProps,
    });

    setSecureTransport(accessLogBucket);

    
    const agentBucket = new s3.Bucket(this, `${projectName}-agent-bucket`, {
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.S3_MANAGED,
      serverAccessLogsBucket: accessLogBucket,
      enforceSSL: true,
      versioned: true,
      serverAccessLogsPrefix: `${projectName}-agent-bucket-access-logs`,
      ...s3BucketProps,
    });

    setSecureTransport(agentBucket);
    
    const restaurantFunction = new lambda.DockerImageFunction(this, `${projectName}-agent-lambda`, {
      code: lambda.DockerImageCode.fromImageAsset(path.join(__dirname, '../lambda'), {
         ...(props.envName === "sagemaker" && { networkMode: ecrAssets.NetworkMode.custom("sagemaker") }),
      }),
      functionName: `${projectName}-agent-function`,
      description: "A function that deploys a restaurant agent",
      timeout: Duration.seconds(120),
      memorySize: 512,
      architecture: lambda.Architecture.X86_64,
      environment: {
        AGENT_BUCKET: agentBucket.bucketName,
        KNOWLEDGE_BASE_ID: knowledgeBaseId.stringValue,
      },
    });


    // Add permissions for the Lambda function to invoke Bedrock APIs
    restaurantFunction.addToRolePolicy(
      new iam.PolicyStatement({
        actions: ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
        resources: ["*"],
      }),
    );

    restaurantFunction.addToRolePolicy(
      new iam.PolicyStatement({
        actions: ["bedrock:Retrieve"],
        resources: [
          `arn:aws:bedrock:${process.env.CDK_DEFAULT_REGION}:${process.env.CDK_DEFAULT_ACCOUNT}:knowledge-base/${knowledgeBaseId.stringValue}`,
        ],
      }),
    );
    
    restaurantFunction.addToRolePolicy(
      new iam.PolicyStatement({
        actions: [
				"dynamodb:ListTables",
				"dynamodb:GetItem",
				"dynamodb:GetRecords",
				"dynamodb:DeleteItem",
				"dynamodb:DeleteTable",
				"dynamodb:UpdateItem",
				"dynamodb:UpdateTable",
        "dynamodb:PutItem"
			],
        resources: [`arn:aws:dynamodb:${process.env.CDK_DEFAULT_REGION}:${process.env.CDK_DEFAULT_ACCOUNT}:table/${dynamoDBName.stringValue}`],
      }),
    );
    
    restaurantFunction.addToRolePolicy(
      new iam.PolicyStatement({
        actions: ["ssm:GetParameter"],
        resources: [`arn:aws:ssm:${process.env.CDK_DEFAULT_REGION}:${process.env.CDK_DEFAULT_ACCOUNT}:parameter/${ssmParamDynamoDb}`,],
      }),
    );
    
    agentBucket.grantReadWrite(restaurantFunction);

    NagSuppressions.addResourceSuppressionsByPath(
      this,
      `/${projectName}LambdaStack/${projectName}-agent-lambda/ServiceRole/Resource`,
      [
        {
          id: "AwsSolutions-IAM4",
          reason: "AWSLambdaBasicExecutionRole is used intentionally.",
        },
      ],
    );

    NagSuppressions.addResourceSuppressionsByPath(
      this,
      `/${projectName}LambdaStack/${projectName}-agent-lambda/ServiceRole/DefaultPolicy/Resource`,
      [
        {
          id: "AwsSolutions-IAM5",
          reason: "AWSLambdaBasicExecutionRole is used intentionally.",
        },
      ],
    );

  }
}
