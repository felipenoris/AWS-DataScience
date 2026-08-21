output "json" {
  description = "The rendered document - composed by each caller through source_policy_documents, never attached directly. There is no aws_iam_policy resource here on purpose: this module describes an intent, and the two objects that carry it are a permission-set inline policy and a permissions boundary, in two different accounts."
  value       = data.aws_iam_policy_document.this.json
}

output "sids" {
  description = "The Sids this fragment contributes, so a caller can assert what it composed. The first two are contracts with ./aws/studio.py (US-9)."
  value       = [for s in jsondecode(data.aws_iam_policy_document.this.json).Statement : s.Sid]
}
