# Output values
output "instance_id" {
  description = "The ID of the EC2 instance"
  value       = aws_instance.audit_assistant_instance.id
}

output "instance_public_ip" {
  description = "The public IP address of the EC2 instance"
  value       = aws_instance.audit_assistant_instance.public_ip
}

output "ssh_key_filepath" {
  description = "The local path to the generated SSH private key file"
  value       = local_file.private_key.filename
}

output "ssh_command" {
  description = "SSH command to connect to the instance"
  value       = "ssh -i ${local_file.private_key.filename} ec2-user@${aws_instance.audit_assistant_instance.public_ip}"
}

output "scp_command" {
  description = "SCP command to copy files to the instance"
  value       = "scp -i ${local_file.private_key.filename} -r /path/to/files/* ec2-user@${aws_instance.audit_assistant_instance.public_ip}:/home/ec2-user/audit-assistant/"
}

output "bedrock_policy_arn" {
  description = "ARN of the Bedrock policy created"
  value       = aws_iam_policy.bedrock_invoke_policy.arn
}
