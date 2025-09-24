#!/usr/bin/env python3
import json
import sys
import os
import importlib.util

# Load environment variables from .env file
def load_env_credentials():
    try:
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        return True
    except Exception as e:
        print(f"Error loading .env: {e}")
        return False

# Load credentials and set environment
load_env_credentials()
os.environ['DYNAMODB_TABLE'] = 'tts-requests'
os.environ['S3_BUCKET'] = 'tts-bucket-1758569760'
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

# Load upload handler
upload_spec = importlib.util.spec_from_file_location(
    "upload_lambda", 
    "lambda-functions/upload-execution/lambda_function.py"
)
upload_module = importlib.util.module_from_spec(upload_spec)
upload_spec.loader.exec_module(upload_module)
upload_handler = upload_module.lambda_handler

# Load track handler
track_spec = importlib.util.spec_from_file_location(
    "track_lambda", 
    "lambda-functions/track-execution/lambda_function.py"
)
track_module = importlib.util.module_from_spec(track_spec)
track_spec.loader.exec_module(track_module)
track_handler = track_module.lambda_handler

def test_upload():
    event = {
        'httpMethod': 'POST',
        'body': json.dumps({
            'text': 'Hello world test',
            'voice_id': 'Joanna',
            'language': 'english'
        }),
        'requestContext': {
            'authorizer': {
                'claims': {
                    'email': 'test@example.com',
                    'sub': 'test-user-123'
                }
            }
        }
    }
    
    print("Testing upload...")
    try:
        result = upload_handler(event, {})
        print(f"Upload result: {result}")
        return result
    except Exception as e:
        print(f"Upload error: {e}")
        return None

def test_track():
    event = {
        'httpMethod': 'GET',
        'queryStringParameters': {'user_email': 'test@example.com'},
        'requestContext': {
            'authorizer': {
                'claims': {
                    'email': 'test@example.com'
                }
            }
        }
    }
    
    print("Testing track...")
    result = track_handler(event, {})
    print(f"Track result: {result}")
    return result

if __name__ == "__main__":
    test_upload()
    test_track()