import { RemovalPolicy, StackProps } from "aws-cdk-lib";

const projectName = "StrandsAgent";

const ssmParamKnowledgeBaseId = "restaurant-assistant-kb-id";
const ssmParamDynamoDb = "restaurant-assistant-table-name";

const s3BucketProps = {
  autoDeleteObjects: true,
  removalPolicy: RemovalPolicy.DESTROY,
};

type envNameType = "sagemaker" | "local";

export { projectName, s3BucketProps, ssmParamKnowledgeBaseId, ssmParamDynamoDb, envNameType };