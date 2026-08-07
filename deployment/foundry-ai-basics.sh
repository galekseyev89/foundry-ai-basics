SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Create a resource group
az group create --name foundry-ai-basics-rg --location swedencentral

# Deploy the Bicep file
az deployment group create --resource-group foundry-ai-basics-rg --template-file "$SCRIPT_DIR/foundry-ai-basics.bicep" --parameters aiFoundryName=foundry-ai-basics

# Get deployment outputs
az deployment group show --resource-group foundry-ai-basics-rg --name foundry-ai-basics --query properties.outputs

# Delete the deployment
az group delete --name foundry-ai-basics-rg --yes --no-wait

# Verify deletion of deployed resources
az group list --output table

# View recently deleted Cognitive Services accounts in the region
az cognitiveservices account list-deleted --output table

# Permanently delete the soft-deleted accounts.
az cognitiveservices account purge --location swedencentral --resource-group foundry-ai-basics-rg --name foundry-ai-basics
az cognitiveservices account purge --location swedencentral --resource-group foundry-ai-basics-rg --name foundry-ai-basics-csafety
