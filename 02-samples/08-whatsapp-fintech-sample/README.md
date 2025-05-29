## WhatsApp and Agents SDK Demo + Amazon Bedrock

This demo intends to show how to use Meta's WhatsApp Business integrated with **Amazon Agents SDK (aka Strands)** and Amazon Bedrock.

It's a multi-agent orchestrator, that will handle tasks for two subagents. One is responsible for loading daily promotions, based on the day of the week (Fake Data). And other one is responsible for handle credit card operations, being able to load last X days of fake transactions and schedule payment.

This is overall architecture diagram:

![Arquitecture](img/architecture.png)

1. User interact with WhatsApp Number
2. AWS End User Messaging get message and add it on SNS Topic
3. Lambda function listening this topic handle this message
4. Multi-agent process this message and redirect it to desired agent.

## 1 - Getting started with AWS End User Messaging Social (Mandatory)

1. Have a Meta Business Account. Check if your company already has a [Meta Business Account](https://business.facebook.com/). If you don't have a Meta Business Account, you can create one during the sign-up process.

1. To use a phone number that's already in use with the WhatsApp Messenger application or WhatsApp Business application, you must delete it first.

1. A phone number that can receive either an SMS or a voice One-Time Passcode (OTP). The phone number used for sign-up becomes associated with your WhatsApp account and the phone number is used when you send messages. The phone number can still be used for SMS, MMS, and voice messaging.

1. Them, follow up "Sign up through the console" step by step guide from [AWS End User Messaging Documentation](https://docs.aws.amazon.com/social-messaging/latest/userguide/getting-started-whatsapp.html).

## 2 - AWS Envirnoment Setup

### 2.1 Amazon Bedrock Model Access

Make sure you have access on Bedrock Models, if you are using a cross region profile, make sure that model is enabled in both regions that are necessary for profile to work.

[Here](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access-modify.html) is more information on how to enable model access on Amazon Bedrock.

### 2.2 - Virtual Env Setup

Create virtualenv and install dependencies

```
python3 -m venv .env
source .env/bin/activate
pip install -r requirements.txt
```

### 2.3 Create Lambdas, upload to S3 and deploy Cloudformation

This project is created to support two languages:

1. Brazilian Portuguese (pt_BR)
1. US English (en_US)

**Note: By default, pack_and_deploy.sh will deploy English locale, but you can change on `template.yaml` file. Change the parameter `LocaleConfig` for the desired locale at the beginning of the CloudFormation Template file, to change solution language!**

This shell script will pack all Lambda functions and deploy Cloudformation stack.

```
chmod +x lambda_pack.sh

export S3_BUCKET=<S3_BUCKET>
export S3_KEY=<S3_KEY>

./pack_and_deploy.sh $S3_BUCKET $S3_KEY

```

Example:

```
./pack_and_deploy.sh my-s3-bucket my-folder-assets
```

**By default, this project is building using Python 3.11, but you can change with an optional parameter PYTHON_VERSION, by calling bash with following args:**

```
./pack_and_deploy.sh my-s3-bucket my-folder-assets "3.11"
```

### 2.4 Cloudformation post-step

After stack is created with CloudFormation, on Outputs get SNS topic.

This will be used as entry-point on AWS End User Messaging.

### 2.5 Demo

<img src="img/whatsapp-demo.gif" alt="demo" width="350"/>

## 3. Delete Resources

```
./destroy.sh
```
