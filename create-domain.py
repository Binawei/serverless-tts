#!/usr/bin/env python3
import boto3
import os
from botocore.exceptions import ClientError

def load_env_credentials():
    with open('.env', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ[key] = value

def create_domain():
    load_env_credentials()
    cognito = boto3.client('cognito-idp', region_name='us-east-1')
    
    user_pool_id = 'us-east-1_wRy4OwOKR'
    domain_name = 'tts-app-wry4owok'
    
    try:
        cognito.create_user_pool_domain(
            Domain=domain_name,
            UserPoolId=user_pool_id
        )
        print(f"✅ Domain created: {domain_name}")
    except ClientError as e:
        print(f"❌ Domain creation failed: {e}")

if __name__ == '__main__':
    create_domain()