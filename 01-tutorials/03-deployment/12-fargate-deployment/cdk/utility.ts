import { Fn, Stack } from "aws-cdk-lib";
import * as iam from "aws-cdk-lib/aws-iam";
import * as s3 from "aws-cdk-lib/aws-s3";

function setSecureTransport(bucket: s3.Bucket) {
  // appsec requirement
  bucket.addToResourcePolicy(
    new iam.PolicyStatement({
      actions: ["s3:*"],
      effect: iam.Effect.DENY,
      principals: [new iam.AnyPrincipal()],
      resources: [`${bucket.bucketArn}/*`, `${bucket.bucketArn}`],
      conditions: {
        Bool: {
          "aws:SecureTransport": false,
        },
      },
    }),
  );
}

function getSuffixFromStackId(stack: Stack) {
  const shortStackId = Fn.select(2, Fn.split("/", stack.stackId));
  const suffix = Fn.select(4, Fn.split("-", shortStackId));
  return suffix;
}

export { setSecureTransport, getSuffixFromStackId };
