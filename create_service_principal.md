# Create Service Principal for GitHub Actions

## Step 1: Create Service Principal
```bash
# Replace with your subscription ID
SUBSCRIPTION_ID="your-subscription-id"
RESOURCE_GROUP="Default_Resource_Group"
WORKSPACE_NAME="GL_AZ_ML"

# Create service principal
az ad sp create-for-rbac --name "CarSales-GitHub-Actions" \
  --role contributor \
  --scopes /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP \
  --sdk-auth
```

## Step 2: Get the Output
The command will return JSON like this:
```json
{
  "clientId": "12345678-1234-1234-1234-123456789012",
  "clientSecret": "your-secret-here",
  "subscriptionId": "87654321-4321-4321-4321-210987654321",
  "tenantId": "11111111-2222-3333-4444-555555555555",
  "activeDirectoryEndpointUrl": "https://login.microsoftonline.com",
  "resourceManagerEndpointUrl": "https://management.azure.com/",
  "activeDirectoryGraphResourceId": "https://graph.windows.net/",
  "sqlManagementEndpointUrl": "https://management.core.windows.net:8443/",
  "galleryEndpointUrl": "https://gallery.azure.com/",
  "managementEndpointUrl": "https://management.core.windows.net/"
}
```

## Step 3: Add to GitHub Secrets
Use these values:
- `AZ_CLIENT_ID` = `clientId`
- `AZ_CLIENT_SECRET` = `clientSecret`
- `AZ_TENANT_ID` = `tenantId`
- `AZ_SUBSCRIPTION` = `subscriptionId`
