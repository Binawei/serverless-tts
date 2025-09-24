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

def delete_domain():
    load_env_credentials()
    cognito = boto3.client('cognito-idp', region_name='us-east-1')
    
    user_pool_id = 'us-east-1_LB524uPY2'
    domain_name = 'tts-app-lb524upy'
    
    try:
        cognito.delete_user_pool_domain(
            Domain=domain_name,
            UserPoolId=user_pool_id
        )
        print(f"✅ Deleted domain: {domain_name}")
        
        # Now delete the User Pool
        cognito.delete_user_pool(UserPoolId=user_pool_id)
        print(f"✅ Deleted User Pool: {user_pool_id}")
        
    except ClientError as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    delete_domain()