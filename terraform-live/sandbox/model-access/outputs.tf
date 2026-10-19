output "model_provisioning_role_arn" {
  description = "The role DataZone assumes to create a project's application inference profile of a model; the console's Manage adopts it by its name."
  value       = module.model_provisioning_role.role_arn
}

output "model_consumption_role_arn" {
  description = "The role a playground model's connection vends to the person's browser; chosen per model in the console's Manage roles dialog."
  value       = module.model_consumption_role.role_arn
}
