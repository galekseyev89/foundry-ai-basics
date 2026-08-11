//https://github.com/microsoft-foundry/foundry-samples/blob/main/infrastructure/infrastructure-setup-bicep/00-basic/main.bicep

param aiFoundryName string = 'foundry-ai-basics'
param aiProjectName string = '${aiFoundryName}-proj'
param contentSafetyName string = '${aiFoundryName}-csafety'
param aiSearchName string = '${aiFoundryName}-aisearch'
param appInsightsName string = '${aiFoundryName}-appinsights'
param logAnalyticsWorkspaceName string = '${aiFoundryName}-logs'
param aiFoundryDiagnosticsName string = '${aiFoundryName}-diag'
param location string = resourceGroup().location

/*
  An AI Foundry resources is a variant of a CognitiveServices/account resource type
*/
resource aiFoundry 'Microsoft.CognitiveServices/accounts@2025-06-01' = {
  name: aiFoundryName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  sku: {
    name: 'S0'
  }
  kind: 'AIServices'
  properties: {
    // required to work in AI Foundry
    allowProjectManagement: true

    // Defines developer API endpoint subdomain
    customSubDomainName: aiFoundryName

    disableLocalAuth: false
  }
}

/*
  Developer APIs are exposed via a project, which groups in- and outputs that relate to one use case, including files.
  Its advisable to create one project right away, so development teams can directly get started.
  Projects may be granted individual RBAC permissions and identities on top of what account provides.
*/
resource aiProject 'Microsoft.CognitiveServices/accounts/projects@2025-06-01' = {
  name: aiProjectName
  parent: aiFoundry
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {}
}

/*
  Optionally deploy a model to use in playground, agents and other tools.
*/
resource llmModelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2025-06-01' = {
  parent: aiFoundry
  name: 'gpt-5.4-mini'
  sku: {
    capacity: 3
    name: 'GlobalStandard'
  }
  properties: {
    model: {
      name: 'gpt-5.4-mini'
      format: 'OpenAI'
      version: '2026-03-17'
    }
  }
}

resource slmModelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2025-06-01' = {
  parent: aiFoundry
  name: 'gpt-5.4-nano'
  dependsOn: [
    llmModelDeployment
  ]
  sku: {
    capacity: 3
    name: 'GlobalStandard'
  }
  properties: {
    model: {
      name: 'gpt-5.4-nano'
      format: 'OpenAI'
      version: '2026-03-17'
    }
  }
}

/*
  Content Safety service to moderate text, images, and other content
*/
resource contentSafety 'Microsoft.CognitiveServices/accounts@2025-06-01' = {
  name: contentSafetyName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  sku: {
    name: 'S0'
  }
  kind: 'ContentSafety'
  properties: {
    customSubDomainName: contentSafetyName
    disableLocalAuth: false
  }
}

/*
  Deploying models to use in playground, agents and other tools.
*/

// https://ai.azure.com/catalog/models/text-embedding-3-small
resource embeddingModelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2025-06-01'= {
  parent: aiFoundry
  name: 'text-embedding-3-small'
  dependsOn: [
    slmModelDeployment
  ]
  sku : {
    capacity: 3
    name: 'GlobalStandard'
  }
  properties: {
    model:{
      name: 'text-embedding-3-small' // 1536 dimensions, good for semantic search and embedding use cases
      format: 'OpenAI'
      version: '1'
    }
  }
}

// Azure AI Search resource
resource searchService 'Microsoft.Search/searchServices@2023-11-01' = {
  name: aiSearchName
  location: location
  sku: {
    name: 'standard'
  }
  properties: {
    replicaCount: 1
    partitionCount: 1
    hostingMode: 'default'
    disableLocalAuth: true
  }
}

/*
  Application Insights for Foundry Trace
  This enables distributed tracing and telemetry collection
*/
resource applicationInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalyticsWorkspace.id  // Optional but recommended
    DisableLocalAuth: false
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

/*
  Log Analytics Workspace for storing traces
*/
resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logAnalyticsWorkspaceName
  location: location
  properties: {
    retentionInDays: 30
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
  }
}

/*
  Enable diagnostic settings to send traces to Log Analytics
  This allows you to query traces using KQL
*/
resource aiFoundryDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: aiFoundryDiagnosticsName
  scope: aiFoundry
  properties: {
    workspaceId: logAnalyticsWorkspace.id
    logs: [
      {
        category: 'Trace'
        enabled: true
      }
      {
        category: 'Audit'
        enabled: true
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
      }
    ]
  }
}

output OPENAI_ENDPOINT string = 'https://${aiFoundry.properties.customSubDomainName}.services.ai.azure.com/openai/v1'
output LLM_DEPLOYMENT_NAME string = llmModelDeployment.name
output SLM_DEPLOYMENT_NAME string = slmModelDeployment.name
output CONTENT_SAFETY_ENDPOINT string = 'https://${contentSafety.properties.customSubDomainName}.cognitiveservices.azure.com/'
output SEARCH_SERVICE_ENDPOINT string = 'https://${searchService.name}.search.windows.net'
output SEARCH_SERVICE_NAME string = searchService.name
output EMBEDDING_MODEL_DEPLOYMENT_NAME string = embeddingModelDeployment.name
output APPLICATIONINSIGHTS_CONNECTION_STRING string = applicationInsights.properties.ConnectionString
