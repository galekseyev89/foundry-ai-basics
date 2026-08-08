
# Create a resource group
az group create --name foundry-ai-basics-rg --location swedencentral

# Deploy the Bicep file
az deployment group create --resource-group foundry-ai-basics-rg --template-file "deployment/foundry-ai-basics.bicep" --parameters aiFoundryName=foundry-ai-basics

# Get deployment outputs
az deployment group show --resource-group foundry-ai-basics-rg --name foundry-ai-basics --query properties.outputs

# Get the object ID of the currently signed-in user
az ad signed-in-user show --query id -o tsv

# Assign the "Search Service Contributor" role to the user for the Azure AI Search resource
az role assignment create --assignee-object-id "768e60ef-c8a0-40ff-8790-0b58a79b86b7" --assignee-principal-type "User" --role "Search Service Contributor" --scope "/subscriptions/8941652a-df9c-46af-b701-82e8d0437b92/resourceGroups/foundry-ai-basics-rg/providers/Microsoft.Search/searchServices/foundry-ai-basics-aisearch"

# Assign the "Search Index Data Contributor" role to the user for the Azure AI Search resource
az role assignment create --assignee-object-id "768e60ef-c8a0-40ff-8790-0b58a79b86b7" --assignee-principal-type "User" --role "Search Index Data Contributor" --scope "/subscriptions/8941652a-df9c-46af-b701-82e8d0437b92/resourceGroups/foundry-ai-basics-rg/providers/Microsoft.Search/searchServices/foundry-ai-basics-aisearch"

# Assign the "Search Index Data Reader" role to the user for the Azure AI Search resource
az role assignment create --assignee-object-id "768e60ef-c8a0-40ff-8790-0b58a79b86b7" --assignee-principal-type "User" --role "Search Index Data Reader" --scope "/subscriptions/8941652a-df9c-46af-b701-82e8d0437b92/resourceGroups/foundry-ai-basics-rg/providers/Microsoft.Search/searchServices/foundry-ai-basics-aisearch"

====================================================================

# Delete the deployment
az group delete --name foundry-ai-basics-rg --yes --no-wait

# Verify deletion of deployed resources
az group list --output table

# View recently deleted Cognitive Services accounts in the region
az cognitiveservices account list-deleted --output table

# Permanently delete the soft-deleted accounts.
az cognitiveservices account purge --location swedencentral --resource-group foundry-ai-basics-rg --name foundry-ai-basics
az cognitiveservices account purge --location swedencentral --resource-group foundry-ai-basics-rg --name foundry-ai-basics-csafety
