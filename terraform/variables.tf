variable "resource_group_name" {
  description = "Resource group yang dibuat manual di portal"
  type        = string
}

variable "location" {
  description = "Region Azure (contoh: indonesiacentral / southeastasia)"
  type        = string
}

variable "vnet_name" {
  description = "Nama Virtual Network"
  type        = string
}

variable "vnet_cidr" {
  description = "Address space VNet (contoh: 10.0.0.0/16)"
  type        = string
  default     = "10.0.0.0/16"
}

variable "infra_subnet_name" {
  description = "Nama subnet untuk Container Apps environment"
  type        = string
}

variable "infra_subnet_cidr" {
  description = "CIDR subnet infrastruktur (minimal /23)"
  type        = string
  default     = "10.0.0.0/23"
}

variable "identity_name" {
  description = "Nama user-assigned managed identity"
  type        = string
}

variable "env_name" {
  description = "Nama Container Apps environment"
  type        = string
}

variable "app_name" {
  description = "Nama Container App (rag-app)"
  type        = string
}

variable "image" {
  description = "Image lengkap di ACR (contoh: myrag.azurecr.io/rag-app:latest)"
  type        = string
}

variable "acr_name" {
  description = "Nama ACR yang dibuat manual"
  type        = string
}

variable "key_vault_name" {
  description = "Nama Key Vault yang dibuat manual"
  type        = string
}

variable "kv_secret_google_api_key" {
  description = "Nama secret di Key Vault untuk GOOGLE_API_KEY"
  type        = string
  default     = "google-api-key"
}

variable "kv_secret_auth_users" {
  description = "Nama secret di Key Vault untuk AUTH_USERS"
  type        = string
  default     = "auth-users"
}

variable "storage_account_name" {
  description = "Nama storage account yang dibuat manual"
  type        = string
}

variable "storage_share_name" {
  description = "Nama file share (ragdata)"
  type        = string
}

variable "storage_access_key" {
  description = "Access key storage account (key1)"
  type        = string
  sensitive   = true
}
