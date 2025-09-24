#!/usr/bin/env python3
import boto3
import time
import os

def load_env_credentials():
    """Load AWS credentials from .env file"""
    try:
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        return True
    except:
        return False

def check_domain_status():
    """Check Cognito domain status"""
    
    load_env_credentials()
    cognito = boto3.client('cognito-idp', region_name='us-east-1')
    
    # Get your User Pool ID
    user_pool_id = input("Enter your User Pool ID (us-east-1_WnLjHfr4I): ").strip()
    if not user_pool_id:
        user_pool_id = "us-east-1_WnLjHfr4I"  # Default from your error
    
    try:
        # Check domain
        response = cognito.describe_user_pool_domain(
            Domain=f'tts-app-{user_pool_id.split("_")[1][:8]}'
        )
        
        domain_info = response['DomainDescription']
        print(f"Domain: {domain_info['Domain']}")
        print(f"Status: {domain_info['Status']}")
        print(f"CloudFront Distribution: {domain_info.get('CloudFrontDistribution', 'N/A')}")
        
        if domain_info['Status'] == 'ACTIVE':
            print("✅ Domain is ACTIVE and ready to use")
        else:
            print(f"⏳ Domain status: {domain_info['Status']} - wait a few minutes")
            
    except Exception as e:
        print(f"❌ Error checking domain: {e}")
        print("Domain might not exist or still being created")

if __name__ == "__main__":
    check_domain_status()