#!/usr/bin/env python3
import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()

def create_api_gateway():
    client = boto3.client(
        'apigateway',
        region_name='us-east-1',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    
    lambda_client = boto3.client(
        'lambda',
        region_name='us-east-1',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    
    try:
        # Create REST API
        api = client.create_rest_api(
            name='tts-api',
            description='Text-to-Speech API'
        )
        
        api_id = api['id']
        print(f"API Gateway created: {api_id}")
        
        # Get root resource
        resources = client.get_resources(restApiId=api_id)
        root_id = resources['items'][0]['id']
        
        # Create /upload resource
        upload_resource = client.create_resource(
            restApiId=api_id,
            parentId=root_id,
            pathPart='upload'
        )
        
        # Create /track resource
        track_resource = client.create_resource(
            restApiId=api_id,
            parentId=root_id,
            pathPart='track'
        )
        
        print("Resources created: /upload, /track")
        
        # Deploy API
        deployment = client.create_deployment(
            restApiId=api_id,
            stageName='prod'
        )
        
        api_url = f"https://{api_id}.execute-api.us-east-1.amazonaws.com/prod"
        print(f"API Gateway URL: {api_url}")
        
        return {
            'API_ID': api_id,
            'API_URL': api_url
        }
        
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    result = create_api_gateway()
    if result:
        print(f"\nUpdate frontend config:")
        print(f"API_GATEWAY_URL: '{result['API_URL']}'")