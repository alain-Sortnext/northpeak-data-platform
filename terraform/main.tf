# NorthPeak Retail Group - Azure Infrastructure
# Phase 8: Terraform IaC
# 
# Deploys the Bronze layer storage infrastructure on Azure.
# Enterprise equivalent of local Parquet files -> Azure Data Lake Storage Gen2.
#
# Run: terraform plan -var-file=variables.tfvars
# Evidence: paste the plan output in your Phase 8 submission.

terraform {
  required_version = ">= 1.8.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.90"
    }
  }
  # Enterprise: use Azure Storage as remote state backend
  # backend "azurerm" {
  #   resource_group_name  = "northpeak-tfstate-rg"
  #   storage_account_name = "northpeaktfstate"
  #   container_name       = "tfstate"
  #   key                  = "data-platform.terraform.tfstate"
  # }
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
  tenant_id       = var.tenant_id
}

# ── Resource Group ────────────────────────────────────────────────
resource "azurerm_resource_group" "northpeak_data" {
  name     = var.resource_group_name
  location = var.location

  tags = {
    project     = "northpeak-data-platform"
    environment = var.environment
    team        = "data-platform-engineering"
    cost_centre = "DATA-PLATFORM-001"
  }
}

# ── Storage Account (ADLS Gen2) ───────────────────────────────────
resource "azurerm_storage_account" "northpeak_datalake" {
  name                     = var.storage_account_name
  resource_group_name      = azurerm_resource_group.northpeak_data.name
  location                 = azurerm_resource_group.northpeak_data.location
  account_tier             = "Standard"
  account_replication_type = "LRS"     # GRS for production
  account_kind             = "StorageV2"

  # Enable hierarchical namespace = ADLS Gen2
  is_hns_enabled = true

  # Security
  min_tls_version           = "TLS1_2"
  enable_https_traffic_only = true

  blob_properties {
    delete_retention_policy {
      days = 30
    }
    container_delete_retention_policy {
      days = 30
    }
  }

  tags = azurerm_resource_group.northpeak_data.tags
}

# ── Bronze Container ──────────────────────────────────────────────
resource "azurerm_storage_container" "bronze" {
  name                  = "bronze"
  storage_account_name  = azurerm_storage_account.northpeak_datalake.name
  container_access_type = "private"
}

# ── Silver Container ──────────────────────────────────────────────
resource "azurerm_storage_container" "silver" {
  name                  = "silver"
  storage_account_name  = azurerm_storage_account.northpeak_datalake.name
  container_access_type = "private"
}

# ── Gold Container ────────────────────────────────────────────────
resource "azurerm_storage_container" "gold" {
  name                  = "gold"
  storage_account_name  = azurerm_storage_account.northpeak_datalake.name
  container_access_type = "private"
}
