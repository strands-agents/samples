#!/bin/bash

# Function to check input values
check_input() {
    if [ -z "$1" ] || [ -z "$2" ]; then
        echo "Error: No parameter was added on invocation."
        echo "Usage: $0 <s3-bucket> <s3-key> <python-version>"
        echo "Example: $0 my-s3-bucket my-key-assets py-version"
        echo "Python Version: default is 3.11 if omitted"
        exit 1
    fi

    # Default Python version
    PYTHON_VERSION="3.11"

    # Check if the third parameter is provided
    if [ -n "$3" ]; then
        PYTHON_VERSION="$3"
    fi

    echo "Using Python version: $PYTHON_VERSION"
}

# Calling function to validate params
check_input "$@"

# Adding parameters into variables
BUCKET="$1"
KEY="$2"

echo "Bucket: $BUCKET"
echo "Key: $KEY"

# Build and Uploading layer.zip to the specified S3 bucket and key
echo "Build lambda layer"
pip install -r requirements.txt --platform manylinux2014_x86_64 --only-binary=:all: -t python/lib/python$PYTHON_VERSION/site-packages/
# clean up layer directory
cd python && find . -type d -name "__pycache__" -exec rm -r {} + && cd ..
# Creating Zip file 
if [ ! -d "binaries" ]; then
    mkdir binaries
fi
zip -r binaries/boto3-lambda-layer.zip python/
# Uploading to S3
echo "Uploading boto3-lambda-layer.zip into: $BUCKET/layer.zip"
aws s3 cp binaries/boto3-lambda-layer.zip s3://$BUCKET/$KEY/layer.zip
rm binaries/boto3-lambda-layer.zip

# Creating a zip file from the contents of the lambda directory
echo "Creating lambda.zip from the contents of the lambda directory"
(cd lambdas && zip -r ../lambda.zip *.py)

# Uploading the lambda.zip to the specified S3 bucket and key
echo "Uploading lambda.zip into: $BUCKET"
aws s3 cp lambda.zip s3://$BUCKET/$KEY/lambda.zip
rm lambda.zip

REGION=$(aws configure get region)
CFN_FILE=template.yaml

echo "Creating CloudFormation Stack"
aws cloudformation create-stack --region $REGION \
  --stack-name aws-whatsapp-stack \
  --template-body file://$CFN_FILE \
  --parameters ParameterKey=S3BucketName,ParameterValue=$BUCKET \
               ParameterKey=S3BucketPath,ParameterValue=$KEY \
               ParameterKey=PythonVersion,ParameterValue=python$PYTHON_VERSION \
  --capabilities CAPABILITY_IAM