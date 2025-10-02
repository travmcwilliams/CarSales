#!/usr/bin/env python3
"""
Azure ML Deployment Script for Car Sales MLOps Pipeline
This script deploys and runs the complete pipeline in Azure ML
"""

import os
import subprocess
import json
from pathlib import Path

def run_command(command, description):
    """Run a command and return the result"""
    print(f"\n🔄 {description}")
    print(f"Command: {command}")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            if result.stdout:
                print(f"Output: {result.stdout}")
        else:
            print(f"❌ {description} - FAILED")
            print(f"Error: {result.stderr}")
        return result
    except Exception as e:
        print(f"❌ {description} - EXCEPTION: {e}")
        return None

def deploy_to_azure():
    """Deploy the complete MLOps pipeline to Azure ML"""
    
    print("🚀 Starting Azure ML Deployment for Car Sales MLOps Pipeline")
    print("=" * 60)
    
    # Azure ML Configuration
    subscription_id = "d818e748-e334-4df7-83c3-882fcc02b8b5"
    resource_group = "default_resource_group"
    workspace_name = "gl_az_ml"
    
    print(f"📋 Azure ML Configuration:")
    print(f"  Subscription: {subscription_id}")
    print(f"  Resource Group: {resource_group}")
    print(f"  Workspace: {workspace_name}")
    
    # Step 1: Login to Azure
    login_cmd = f"az login --service-principal -u $env:AZURE_CLIENT_ID -p $env:AZURE_CLIENT_SECRET --tenant $env:AZURE_TENANT_ID"
    run_command(login_cmd, "Azure Login with Service Principal")
    
    # Step 2: Set subscription
    sub_cmd = f"az account set --subscription {subscription_id}"
    run_command(sub_cmd, "Set Azure Subscription")
    
    # Step 3: Create compute cluster (if not exists)
    compute_cmd = f"""
    az ml compute create --name cpu-cluster --type amlcompute --min-instances 0 --max-instances 4 --size Standard_DS3_v2 --idle-time-before-scale-down 1800 --resource-group {resource_group} --workspace-name {workspace_name}
    """
    run_command(compute_cmd, "Create/Update Compute Cluster")
    
    # Step 4: Create environment
    env_cmd = f"""
    az ml environment create --file .github/workflows/train-env.yml --resource-group {resource_group} --workspace-name {workspace_name}
    """
    run_command(env_cmd, "Create Training Environment")
    
    # Step 5: Register dataset
    dataset_cmd = f"""
    az ml data create --name used-cars-data --path data/used_cars.csv --type uri_file --resource-group {resource_group} --workspace-name {workspace_name}
    """
    run_command(dataset_cmd, "Register Dataset")
    
    # Step 6: Create and submit training job
    training_cmd = f"""
    az ml job create --file training_job.yml --resource-group {resource_group} --workspace-name {workspace_name}
    """
    run_command(training_cmd, "Submit Training Job")
    
    # Step 7: Create endpoint
    endpoint_cmd = f"""
    az ml online-endpoint create --file config/endpoint.yml --resource-group {resource_group} --workspace-name {workspace_name}
    """
    run_command(endpoint_cmd, "Create Online Endpoint")
    
    # Step 8: Deploy model
    deploy_cmd = f"""
    az ml online-deployment create --file config/deploy.yml --resource-group {resource_group} --workspace-name {workspace_name} --set-traffic blue=100
    """
    run_command(deploy_cmd, "Deploy Model to Endpoint")
    
    print("\n🎉 Azure ML Deployment Complete!")
    print("=" * 60)
    
    # Get endpoint details
    endpoint_info_cmd = f"""
    az ml online-endpoint show --name used-cars-price-endpoint --resource-group {resource_group} --workspace-name {workspace_name} --query scoring_uri -o tsv
    """
    result = run_command(endpoint_info_cmd, "Get Endpoint URL")
    
    if result and result.returncode == 0:
        endpoint_url = result.stdout.strip()
        print(f"\n🌐 Endpoint URL: {endpoint_url}")
        
        # Get authentication key
        key_cmd = f"""
        az ml online-endpoint get-credentials --name used-cars-price-endpoint --resource-group {resource_group} --workspace-name {workspace_name} --query primaryKey -o tsv
        """
        key_result = run_command(key_cmd, "Get Authentication Key")
        
        if key_result and key_result.returncode == 0:
            auth_key = key_result.stdout.strip()
            print(f"🔑 Authentication Key: {auth_key[:10]}...")
            
            # Test endpoint
            test_payload = {
                "input_data": {
                    "columns": ["Kilometers_Driven", "Mileage", "Engine", "Power", "Seats", "Segment"],
                    "data": [[50000, 18.5, 1500, 100, 5, "non-luxury segment"]]
                }
            }
            
            print(f"\n🧪 Test Payload:")
            print(json.dumps(test_payload, indent=2))
            print(f"\n📡 Test Command:")
            print(f"curl -X POST {endpoint_url}/score \\")
            print(f"  -H 'Authorization: Bearer {auth_key[:10]}...' \\")
            print(f"  -H 'Content-Type: application/json' \\")
            print(f"  -d '{json.dumps(test_payload)}'")

if __name__ == "__main__":
    deploy_to_azure()
