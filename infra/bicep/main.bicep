// infra/bicep/main.bicep
// Azure Container Apps reference deployment for EARP, matching the
// resource-naming conventions in Azure/Azure.txt:
//
//   rg-earp-<env>-<region>          resource group (outside this template)
//   law-earp-<env>-<region>         Log Analytics workspace
//   ai-earp-<env>-<region>          Application Insights
//   kv-earp-<env>-<region>          Key Vault
//   cae-earp-<env>-<region>         Container Apps Environment
//   ca-earp-api-<env>-<region>      API container app
//   ca-earp-web-<env>-<region>      Web container app
//   pg-earp-<env>-<region>          PostgreSQL Flexible Server
//   redis-earp-<env>-<region>       Azure Cache for Redis
//
// All secrets (JWT_SECRET, DATABASE_URL, REDIS_URL, OPENAI_API_KEY)
// are resolved from Key Vault at container startup via managed identity.

@description('Short environment name (dev, staging, prod).')
@allowed(['dev', 'staging', 'prod'])
param env string = 'dev'

@description('Azure region short code (eastus, westus2, etc.).')
param region string = 'eastus'

@description('Container image tag for the API (e.g. git SHA or semver).')
param apiImageTag string = 'latest'

@description('Container image tag for the web app.')
param webImageTag string = 'latest'

@description('Container registry hostname, e.g. ghcr.io or acrcontoso.azurecr.io.')
param registryHost string = 'ghcr.io'

@description('Repository path prefix inside the registry.')
param registryRepo string = 'enterprise-ai-reliability-platform-v1'

@description('Fully qualified resource ID of an existing user-assigned managed identity.')
param managedIdentityId string

@description('Key Vault URI, e.g. https://kv-earp-dev-eastus.vault.azure.net/.')
param keyVaultUri string

var shortEnv = env
var loc = region

// --- Observability -----------------------------------------------------------

resource law 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: 'law-earp-${shortEnv}-${loc}'
  location: loc
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: 'ai-earp-${shortEnv}-${loc}'
  location: loc
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: law.id
  }
}

// --- Container Apps environment ---------------------------------------------

resource cae 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: 'cae-earp-${shortEnv}-${loc}'
  location: loc
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: law.properties.customerId
        sharedKey: law.listKeys().primarySharedKey
      }
    }
  }
}

// --- API container app -------------------------------------------------------

resource caApi 'Microsoft.App/containerApps@2024-03-01' = {
  name: 'ca-earp-api-${shortEnv}-${loc}'
  location: loc
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${managedIdentityId}': {}
    }
  }
  properties: {
    environmentId: cae.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
      }
      secrets: [
        {
          name: 'jwt-secret'
          keyVaultUrl: '${keyVaultUri}secrets/jwt-secret'
          identity: managedIdentityId
        }
        {
          name: 'database-url'
          keyVaultUrl: '${keyVaultUri}secrets/database-url'
          identity: managedIdentityId
        }
        {
          name: 'redis-url'
          keyVaultUrl: '${keyVaultUri}secrets/redis-url'
          identity: managedIdentityId
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'api'
          image: '${registryHost}/${registryRepo}/api:${apiImageTag}'
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            { name: 'APP_ENV', value: shortEnv }
            { name: 'JWT_SECRET', secretRef: 'jwt-secret' }
            { name: 'DATABASE_URL', secretRef: 'database-url' }
            { name: 'REDIS_URL', secretRef: 'redis-url' }
            {
              name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
              value: appInsights.properties.ConnectionString
            }
            { name: 'KEY_VAULT_URI', value: keyVaultUri }
          ]
          probes: [
            {
              type: 'Liveness'
              httpGet: { path: '/health', port: 8000 }
              periodSeconds: 30
              failureThreshold: 3
            }
            {
              type: 'Readiness'
              httpGet: { path: '/health', port: 8000 }
              periodSeconds: 10
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 5
      }
    }
  }
}

// --- Web container app -------------------------------------------------------

resource caWeb 'Microsoft.App/containerApps@2024-03-01' = {
  name: 'ca-earp-web-${shortEnv}-${loc}'
  location: loc
  properties: {
    environmentId: cae.id
    configuration: {
      ingress: {
        external: true
        targetPort: 80
        transport: 'auto'
      }
    }
    template: {
      containers: [
        {
          name: 'web'
          image: '${registryHost}/${registryRepo}/web:${webImageTag}'
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
          env: [
            {
              name: 'API_BASE_URL'
              value: 'https://${caApi.properties.configuration.ingress.fqdn}'
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
      }
    }
  }
}

output apiFqdn string = caApi.properties.configuration.ingress.fqdn
output webFqdn string = caWeb.properties.configuration.ingress.fqdn
output appInsightsConnectionString string = appInsights.properties.ConnectionString
