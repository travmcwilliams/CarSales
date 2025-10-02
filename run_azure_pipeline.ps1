# Car Sales MLOps Pipeline - Azure ML Deployment Script
# PowerShell script to deploy and run the complete pipeline in Azure ML

Write-Host "🚀 Car Sales MLOps Pipeline - Azure ML Deployment" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Green

# Azure ML Configuration
$subscriptionId = "d818e748-e334-4df7-83c3-882fcc02b8b5"
$resourceGroup = "default_resource_group"
$workspaceName = "gl_az_ml"

Write-Host "📋 Azure ML Configuration:" -ForegroundColor Yellow
Write-Host "  Subscription: $subscriptionId"
Write-Host "  Resource Group: $resourceGroup"
Write-Host "  Workspace: $workspaceName"

# Check if Azure CLI is installed
Write-Host "`n🔄 Checking Azure CLI..." -ForegroundColor Cyan
try {
    $azVersion = az --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Azure CLI is installed" -ForegroundColor Green
    } else {
        Write-Host "❌ Azure CLI not found" -ForegroundColor Red
        Write-Host "Please install Azure CLI from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "❌ Azure CLI not found" -ForegroundColor Red
    Write-Host "Please install Azure CLI from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli" -ForegroundColor Yellow
    exit 1
}

# Check environment variables
Write-Host "`n🔄 Checking environment variables..." -ForegroundColor Cyan
$requiredVars = @("AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET", "AZURE_TENANT_ID", "AZURE_SUBSCRIPTION")
$missingVars = @()

foreach ($var in $requiredVars) {
    if (-not $env:$var) {
        $missingVars += $var
    }
}

if ($missingVars.Count -gt 0) {
    Write-Host "❌ Missing environment variables: $($missingVars -join ', ')" -ForegroundColor Red
    Write-Host "Please set these in your GitHub repository secrets or environment" -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "✅ All required environment variables are set" -ForegroundColor Green
}

# Azure ML Commands
$commands = @(
    @{
        Name = "Azure Login"
        Command = "az login --service-principal -u `$env:AZURE_CLIENT_ID -p `$env:AZURE_CLIENT_SECRET --tenant `$env:AZURE_TENANT_ID"
    },
    @{
        Name = "Set Subscription"
        Command = "az account set --subscription $subscriptionId"
    },
    @{
        Name = "Create Compute Cluster"
        Command = "az ml compute create --name cpu-cluster --type amlcompute --min-instances 0 --max-instances 4 --size Standard_DS3_v2 --idle-time-before-scale-down 1800 --resource-group $resourceGroup --workspace-name $workspaceName"
    },
    @{
        Name = "Create Environment"
        Command = "az ml environment create --file .github/workflows/train-env.yml --resource-group $resourceGroup --workspace-name $workspaceName"
    },
    @{
        Name = "Register Dataset"
        Command = "az ml data create --name used-cars-data --path data/used_cars.csv --type uri_file --resource-group $resourceGroup --workspace-name $workspaceName"
    },
    @{
        Name = "Submit Training Job"
        Command = "az ml job create --file training_job.yml --resource-group $resourceGroup --workspace-name $workspaceName"
    },
    @{
        Name = "Create Endpoint"
        Command = "az ml online-endpoint create --file config/endpoint.yml --resource-group $resourceGroup --workspace-name $workspaceName"
    },
    @{
        Name = "Deploy Model"
        Command = "az ml online-deployment create --file config/deploy.yml --resource-group $resourceGroup --workspace-name $workspaceName --set-traffic blue=100"
    }
)

# Execute commands
Write-Host "`n🎯 Starting Azure ML deployment..." -ForegroundColor Green

foreach ($cmd in $commands) {
    Write-Host "`n🔄 $($cmd.Name)..." -ForegroundColor Cyan
    Write-Host "Command: $($cmd.Command)" -ForegroundColor Gray
    
    try {
        $result = Invoke-Expression $cmd.Command
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ $($cmd.Name) completed successfully" -ForegroundColor Green
        } else {
            Write-Host "⚠️ $($cmd.Name) had issues (this might be expected if resources already exist)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "❌ $($cmd.Name) failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`n🎉 Deployment process completed!" -ForegroundColor Green
Write-Host "`n📋 Next steps:" -ForegroundColor Yellow
Write-Host "1. Check Azure ML Studio: https://ml.azure.com" -ForegroundColor White
Write-Host "2. Navigate to your workspace: $workspaceName" -ForegroundColor White
Write-Host "3. Check the Jobs section for training progress" -ForegroundColor White
Write-Host "4. Check the Endpoints section for deployment status" -ForegroundColor White
Write-Host "5. Test the endpoint with sample data" -ForegroundColor White

Write-Host "`n🔗 Useful URLs:" -ForegroundColor Yellow
Write-Host "• Azure ML Studio: https://ml.azure.com" -ForegroundColor White
Write-Host "• GitHub Actions: https://github.com/travmcwilliams/CarSales/actions" -ForegroundColor White
Write-Host "• Repository: https://github.com/travmcwilliams/CarSales" -ForegroundColor White
