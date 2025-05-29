#!/bin/bash

echo "Deleting CloudFormation Stack"
aws cloudformation delete-stack --stack-name aws-whatsapp-stack