resource "azurerm_container_app_environment" "env" {
  name                = var.env_name
  resource_group_name = var.resource_group_name
  location            = var.location

  infrastructure_subnet_id = azurerm_subnet.infra.id

  workload_profile {
    name                  = "Consumption"
    workload_profile_type = "Consumption"
  }
}

resource "azurerm_container_app_environment_storage" "ragdata" {
  name                         = "ragdata"
  container_app_environment_id = azurerm_container_app_environment.env.id
  account_name                 = data.azurerm_storage_account.storage.name
  access_key                   = var.storage_access_key
  access_mode                  = "ReadWrite"
  share_name                   = var.storage_share_name
}

resource "azurerm_container_app" "app" {
  name                         = var.app_name
  container_app_environment_id = azurerm_container_app_environment.env.id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"

  ingress {
    external_enabled = true
    target_port      = 8000

    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  template {
    min_replicas = 1
    max_replicas = 1

    container {
      name   = "rag-app"
      image  = var.image
      cpu    = 0.5
      memory = "1.0Gi"

      env {
        name        = "GOOGLE_API_KEY"
        secret_name = "google-api-key"
      }

      env {
        name        = "AUTH_USERS"
        secret_name = "auth-users"
      }

      volume_mounts {
        name = "ragdata"
        path = "/app/chroma_db"
      }

      volume_mounts {
        name = "ragdata"
        path = "/app/data"
      }
    }

    volume {
      name          = "ragdata"
      storage_name  = azurerm_container_app_environment_storage.ragdata.name
      storage_type  = "AzureFile"
      mount_options = "uid=1000,gid=1000,mfsymlinks,nobrl,cache=none,dir_mode=0750,file_mode=0750"
    }
  }

  secret {
    name  = "google-api-key"
    value = "secretref:${data.azurerm_key_vault.kv.vault_uri}secrets/${var.kv_secret_google_api_key}"
  }

  secret {
    name  = "auth-users"
    value = "secretref:${data.azurerm_key_vault.kv.vault_uri}secrets/${var.kv_secret_auth_users}"
  }

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.app.id]
  }
}
