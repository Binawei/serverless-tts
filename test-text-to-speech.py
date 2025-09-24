#!/usr/bin/env python3
"""
Local test script for text-to-speech conversion
Tests the Lambda functions locally without API Gateway
"""

import json
import boto3
import uuid
import os
import sys
from datetime import datetime, timezone, timedelta

# Load credentials from .env file
def load_env():
    try:
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key] = value
    except FileNotFoundError:
        print("❌ .env file not found - using defaults")

load_env()

# Set environment variables
os.environ['DYNAMODB_TABLE'] = 'tts-requests'
os.environ['S3_BUCKET'] = 'tts-bucket-1758567505'

os.environ['SNS_TOPIC_NAME'] = 'tts-processing-topic'
os.environ['AWS_REGION'] = 'us-east-1'

# Import Lambda functions
sys.path.append('lambda-functions/upload-execution')
sys.path.append('lambda-functions/document-splitter')
sys.path.append('lambda-functions/polly-invoker')

import lambda_function as upload_lambda
import lambda_function as splitter_lambda
import lambda_function as polly_lambda

def test_text_to_speech():
    """Test the complete text-to-speech flow"""
    
    print("🚀 Starting Text-to-Speech Test...")
    
    # Test data
    test_text = "Hello world! This is a test of the text to speech conversion system."
    test_user = "test@example.com"
    
    # Step 1: Simulate upload-execution
    print("\n📤 Step 1: Testing upload-execution...")
    
    upload_event = {
        'body': json.dumps({
            'text': test_text,
            'language': 'english',
            'voice_id': 'Joanna'
        }),
        'requestContext': {
            'authorizer': {
                'claims': {
                    'email': test_user
                }
            }
        }
    }
    
    try:
        upload_result = upload_lambda.lambda_handler(upload_event, None)
        print(f"✅ Upload result: {upload_result['statusCode']}")
        
        if upload_result['statusCode'] == 200:
            response_body = json.loads(upload_result['body'])
            reference_key = response_body['reference_key']
            print(f"📋 Reference key: {reference_key}")
        else:
            print("❌ Upload failed")
            return
            
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return
    
    # Step 2: Simulate document-splitter (text passthrough)
    print(f"\n🔄 Step 2: Testing document-splitter for text input...")
    
    # Create mock DynamoDB stream event
    splitter_event = {
        'Records': [{
            'dynamodb': {
                'NewImage': {
                    'reference_key': {'S': reference_key},
                    'InputType': {'S': 'TEXT'},
                    'S3Path': {'S': f's3://{os.environ["S3_BUCKET"]}/upload/{reference_key}/input.txt'}
                }
            }
        }]
    }
    
    try:
        splitter_result = splitter_lambda.lambda_handler(splitter_event, None)
        print(f"✅ Document splitter result: {splitter_result['statusCode']}")
    except Exception as e:
        print(f"❌ Document splitter error: {e}")
        return
    
    # Step 3: Simulate polly-invoker (S3 event trigger)
    print(f"\n🎵 Step 3: Testing polly-invoker...")
    
    # Create mock S3 event
    polly_event = {
        'Records': [{
            's3': {
                'bucket': {'name': os.environ['S3_BUCKET']},
                'object': {'key': f'download/{reference_key}/formatted_output.txt'}
            }
        }]
    }
    
    try:
        polly_result = polly_lambda.lambda_handler(polly_event, None)
        print(f"✅ Polly converter result: {polly_result['statusCode']}")
        print(f"🎉 Audio file should be at: s3://{os.environ['S3_BUCKET']}/download/{reference_key}/Audio.mp3")
    except Exception as e:
        print(f"❌ Polly converter error: {e}")
        return
    
    print(f"\n✨ Test completed! Check S3 bucket for audio file.")
    return reference_key

def check_s3_files(reference_key):
    """Check what files were created in S3"""
    s3 = boto3.client('s3')
    bucket = os.environ['S3_BUCKET']
    
    print(f"\n📁 Files in S3 for {reference_key}:")
    
    try:
        response = s3.list_objects_v2(Bucket=bucket, Prefix=f'upload/{reference_key}/')
        if 'Contents' in response:
            for obj in response['Contents']:
                print(f"  📄 {obj['Key']}")
        
        response = s3.list_objects_v2(Bucket=bucket, Prefix=f'download/{reference_key}/')
        if 'Contents' in response:
            for obj in response['Contents']:
                print(f"  🎵 {obj['Key']}")
                
    except Exception as e:
        print(f"❌ Error listing S3 files: {e}")

if __name__ == "__main__":
    # Check if AWS credentials are configured
    try:
        boto3.client('sts').get_caller_identity()
        print("✅ AWS credentials configured")
    except Exception as e:
        print(f"❌ AWS credentials not configured: {e}")
        sys.exit(1)
    
    # Run the test
    reference_key = test_text_to_speech()
    
    if reference_key:
        input("\nPress Enter to check S3 files...")
        check_s3_files(reference_key)