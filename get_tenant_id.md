# Get Your Tenant ID - Quick Methods

## Method 1: Azure Portal (Recommended)
1. Go to: https://portal.azure.com
2. Click your profile picture (top right)
3. Click "Switch directory" or "Directory + subscription"
4. Copy the Tenant ID from the list

## Method 2: Azure Cloud Shell
1. Go to: https://shell.azure.com
2. Run: `az account show --query tenantId --output tsv`

## Method 3: Create Service Principal (Gets All Values)
Run this in Azure Cloud Shell:
```bash
az ad sp create-for-rbac --name "CarSales-Class" \
  --role contributor \
  --scopes /subscriptions/d818e748-e334-4df7-83c3-882fcc02b8b5 \
  --sdk-auth
```

This will give you:
- clientId (use for AZ_CLIENT_ID)
- clientSecret (use for AZ_CLIENT_SECRET)  
- tenantId (use for AZ_TENANT_ID)
- subscriptionId (use for AZ_SUBSCRIPTION)

## Your Current Values:
- Subscription ID: `d818e748-e334-4df7-83c3-882fcc02b8b5`
- Resource Group: `Default_Resource_Group`
- Workspace: `GL_AZ_ML`
