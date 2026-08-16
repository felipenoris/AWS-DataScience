# One output, and only so the console can be read. Everything here is [E]; nothing may
# reference it.

output "int09_instance_id" {
  description = "The INT-09 probe. Read with `aws ec2 get-console-output --instance-id <this> --latest`: no SSM endpoints exist in this account (Stage 3 step 8.7 lists them as not-here-yet), so the serial console is the reading path."
  value       = aws_instance.int09.id
}
