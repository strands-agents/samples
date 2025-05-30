class app_config:
    BEDROCK_REGION = "us-east-1" #change region based on your deployment

    #Bedrock Model Id, update these with correct values for your deployment, you might have to use inference profile
    AMZ_BEDROCK_CLAUDE_MODEL_ID = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
    AMZ_BEDROCK_NOVA_PRO_MODEL_ID = "us.amazon.nova-pro-v1:0"
    AMZ_BEDROCK_NOVE_LITE_MODEL_ID ="amazon.nova-lite-v1:0"

    #AWS CLI Profile for getting credential to your AWS account. Make sure the profile has access to invoke Bedrock LLM models above
    AWS_PROFILE_NAME = 'default'
