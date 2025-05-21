import { RemovalPolicy, StackProps } from "aws-cdk-lib";

const projectName = "StrandsAgent";

const ssmParamKnowledgeBaseId = "restaurant-assistant-kb-id";
const ssmParamDynamoDb = "restaurant-assistant-table-name";

const s3BucketProps = {
  autoDeleteObjects: true,
  removalPolicy: RemovalPolicy.DESTROY,
};

const agentModelId = "anthropic.claude-3-7-sonnet-20250219-v1:0";
export { projectName, s3BucketProps, ssmParamKnowledgeBaseId, ssmParamDynamoDb, agentModelId };
