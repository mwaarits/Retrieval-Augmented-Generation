output "app_url" {
  description = "aps url"
  value       = "https://${azurerm_container_app.app.ingress[0].fqdn}"
}

output "env_name" {
  description = "ontainer Apps environment"
  value       = azurerm_container_app_environment.env.name
}

output "identity_principal_id" {
  description = "principal id"
  value       = azurerm_user_assigned_identity.app.principal_id
}
