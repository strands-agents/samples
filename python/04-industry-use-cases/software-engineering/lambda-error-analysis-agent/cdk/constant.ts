import { RemovalPolicy, StackProps } from "aws-cdk-lib";

const projectName = "LambdaErrorAnalysis";

const ssmParamKnowledgeBaseId = "lambda-error-analysis-agent-kb-id";
const ssmParamDynamoDb = "lambda-error-analysis-agent-table-name";

const s3BucketProps = {
  autoDeleteObjects: true,
  removalPolicy: RemovalPolicy.DESTROY,
};

type envNameType = "sagemaker" | "local";

export {
  projectName,
  s3BucketProps,
  ssmParamKnowledgeBaseId,
  ssmParamDynamoDb,
  envNameType,
};
