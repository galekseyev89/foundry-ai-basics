# First, create a resource group (if you haven't already)
az group create --name foundry-ai-basics-rg --location swedencentral

# Deploy the Bicep file
az deployment group create --resource-group foundry-ai-basics-rg --template-file foundry-ai-basics.bicep --parameters aiFoundryName=foundry-ai-basics

# Get your deployment outputs
az deployment group show --resource-group foundry-ai-basics-rg --name foundry-ai-basics --query properties.outputs

# Delete the entire deployment (So no more costs)
az group delete --name foundry-ai-basics-rg --yes --no-wait

# Verify deletion of deployed resources
az group list --output table

# View recently deleted Cognitive Services accounts in the region (to confirm deletion)
az cognitiveservices account list-deleted --output table

# The following commands permanently delete the soft-deleted accounts.
az cognitiveservices account purge --location swedencentral --resource-group foundry-ai-basics-rg --name foundry-ai-basics