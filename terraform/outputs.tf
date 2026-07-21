output "resource_group_name" {
  description = "Name of the resource group created"
  value       = azurerm_resource_group.northpeak_data.name
}

output "storage_account_name" {
  description = "Name of the ADLS Gen2 storage account"
  value       = azurerm_storage_account.northpeak_datalake.name
}

output "storage_account_id" {
  description = "Resource ID of the storage account"
  value       = azurerm_storage_account.northpeak_datalake.id
}

output "dfs_endpoint" {
  description = "ADLS Gen2 DFS endpoint for PySpark connection"
  value       = azurerm_storage_account.northpeak_datalake.primary_dfs_endpoint
}

output "bronze_container_url" {
  description = "abfss:// URL for Bronze container (use in Databricks)"
  value       = "abfss://bronze@${azurerm_storage_account.northpeak_datalake.name}.dfs.core.windows.net/"
}

output "silver_container_url" {
  value = "abfss://silver@${azurerm_storage_account.northpeak_datalake.name}.dfs.core.windows.net/"
}

output "gold_container_url" {
  value = "abfss://gold@${azurerm_storage_account.northpeak_datalake.name}.dfs.core.windows.net/"
}
