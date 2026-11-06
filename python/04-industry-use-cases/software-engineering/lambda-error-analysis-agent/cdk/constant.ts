import { RemovalPolicy, StackProps } from "aws-cdk-lib";

const projectName = "LambdaErrorAnalysis";

const ssmParamKnowledgeBaseId = "lambda-error-analysis-agent-kb-id";
const ssmParamDynamoDb = "lambda-error-analysis-agent-table-name";

const s3BucketProps = {
  autoDeleteObjects: true,
  removalPolicy: RemovalPolicy.DESTROY,
};

type envNameType = "sagemaker" | "local";

// Knowledge Base type: "VECTOR" (default, uses OpenSearch) or "MANAGED" (fully managed by Bedrock)
type knowledgeBaseType = "VECTOR" | "MANAGED";

export {
  projectName,
  s3BucketProps,
  ssmParamKnowledgeBaseId,
  ssmParamDynamoDb,
  envNameType,
  knowledgeBaseType,
};
