#!/usr/bin/env python3
"""
Simple script to run the Car Sales MLOps pipeline in Azure ML
This script will push files and execute the complete pipeline
"""

import os
import subprocess
import sys

def check_azure_cli():
    """Check if Azure CLI is installed and configured"""
    try:
        result = subprocess.run(["az", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Azure CLI is installed")
            return True
        else:
            print("❌ Azure CLI not found")
            return False
    except FileNotFoundError:
        print("❌ Azure CLI not found. Please install Azure CLI first.")
        return False

def check_environment_variables():
    """Check if required environment variables are set"""
    required_vars = ["AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET", "AZURE_TENANT_ID", "AZURE_SUBSCRIPTION"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        print("Please set these in your GitHub repository secrets or environment")
        return False
    else:
        print("✅ All required environment variables are set")
        return True

def run_azure_commands():
    """Run the Azure ML deployment commands"""
    
    # Azure ML Configuration
    subscription_id = "d818e748-e334-4df7-83c3-882fcc02b8b5"
    resource_group = "default_resource_group"
    workspace_name = "gl_az_ml"
    
    commands = [
        # Login to Azure
        f"az login --service-principal -u $env:AZURE_CLIENT_ID -p $env:AZURE_CLIENT_SECRET --tenant $env:AZURE_TENANT_ID",
        
        # Set subscription
        f"az account set --subscription {subscription_id}",
        
        # Create compute cluster
        f"az ml compute create --name cpu-cluster --type amlcompute --min-instances 0 --max-instances 4 --size Standard_DS3_v2 --idle-time-before-scale-down 1800 --resource-group {resource_group} --workspace-name {workspace_name}",
        
        # Create environment
        f"az ml environment create --file .github/workflows/train-env.yml --resource-group {resource_group} --workspace-name {workspace_name}",
        
        # Register dataset
        f"az ml data create --name used-cars-data --path data/used_cars.csv --type uri_file --resource-group {resource_group} --workspace-name {workspace_name}",
        
        # Submit training job
        f"az ml job create --file training_job.yml --resource-group {resource_group} --workspace-name {workspace_name}",
        
        # Create endpoint
        f"az ml online-endpoint create --file config/endpoint.yml --resource-group {resource_group} --workspace-name {workspace_name}",
        
        # Deploy model
        f"az ml online-deployment create --file config/deploy.yml --resource-group {resource_group} --workspace-name {workspace_name} --set-traffic blue=100"
    ]
    
    for i, command in enumerate(commands, 1):
        print(f"\n🔄 Step {i}: Running command...")
        print(f"Command: {command}")
        
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Step {i} completed successfully")
                if result.stdout:
                    print(f"Output: {result.stdout[:200]}...")
            else:
                print(f"⚠️ Step {i} had issues (this might be expected if resources already exist)")
                print(f"Error: {result.stderr[:200]}...")
        except Exception as e:
            print(f"❌ Step {i} failed with exception: {e}")

def main():
    print("🚀 Car Sales MLOps Pipeline - Azure ML Deployment")
    print("=" * 60)
    
    # Check prerequisites
    if not check_azure_cli():
        print("\n📋 To install Azure CLI:")
        print("1. Go to: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli")
        print("2. Install Azure CLI for your operating system")
        print("3. Run this script again")
        return
    
    if not check_environment_variables():
        print("\n📋 To set environment variables:")
        print("1. Go to your GitHub repository settings")
        print("2. Navigate to Secrets and variables > Actions")
        print("3. Add the required secrets:")
        print("   - AZURE_CLIENT_ID")
        print("   - AZURE_CLIENT_SECRET") 
        print("   - AZURE_TENANT_ID")
        print("   - AZURE_SUBSCRIPTION")
        return
    
    print("\n🎯 Starting Azure ML deployment...")
    run_azure_commands()
    
    print("\n🎉 Deployment process completed!")
    print("\n📋 Next steps:")
    print("1. Check Azure ML Studio: https://ml.azure.com")
    print("2. Navigate to your workspace: gl_az_ml")
    print("3. Check the Jobs section for training progress")
    print("4. Check the Endpoints section for deployment status")
    print("5. Test the endpoint with sample data")

if __name__ == "__main__":
    main()
