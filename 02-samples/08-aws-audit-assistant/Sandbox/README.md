Terraform script deploys the EC2 instance and attaches a read only role to it.
    Intitialize terraform :terraform init
    Plan deployment : terraform plan (ensure all necessary resources are being created)
    Deploy resources : terraform deploy
    
Once deployed, copy the files in the aws-audit-assistant folder to /home/ec2-user/ folder
Copy the following files to the instance
    Command : 
        scp -i ./audit-assistant-key.pem /path/to/file ec2-user@<instance public ip>:/home/ec2-user/

    Files:

        ai_assistant.py
        aws_document_agent.py
        strands_boto_agent.py
        requirements.txt

Install requirements.txt from the cli (pip3 install -r requirements.txt)

Run cli command (python3 ai_assistant.py)