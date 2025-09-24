#!/usr/bin/env python3
"""
Python-based AWS setup (no AWS CLI required)
Creates DynamoDB table, S3 bucket, and SNS topic
"""

import boto3
import time
from datetime import datetime

def create_dynamodb_table():
    """Create DynamoDB table with streams"""
    
    print("🗄️  Creating DynamoDB table...")
    
    dynamodb = boto3.client('dynamodb')
    table_name = 'tts-requests'
    
    try:
        response = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'reference_key',
                    'KeyType': 'HASH'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'reference_key',
                    'AttributeType': 'S'
                }
            ],
            BillingMode='PAY_PER_REQUEST',
            StreamSpecification={
                'StreamEnabled': True,
                'StreamViewType': 'NEW_AND_OLD_IMAGES'
            }
        )
        
        print(f"✅ DynamoDB table created: {table_name}")
        return table_name
        
    except dynamodb.exceptions.ResourceInUseException:
        print(f"⚠️  DynamoDB table {table_name} already exists")
        return table_name
    except Exception as e:
        print(f"❌ Error creating DynamoDB table: {e}")
        return None

def create_s3_bucket():
    """Create S3 bucket"""
    
    print("🪣 Creating S3 bucket...")
    
    s3 = boto3.client('s3')
    timestamp = int(time.time())
    bucket_name = f'tts-bucket-{timestamp}'
    
    try:
        # Create bucket
        s3.create_bucket(Bucket=bucket_name)
        
        print(f"✅ S3 bucket created: {bucket_name}")
        return bucket_name
        
    except Exception as e:
        print(f"❌ Error creating S3 bucket: {e}")
        return None

def create_sns_topic():
    """Create SNS topic"""
    
    print("📢 Creating SNS topic...")
    
    sns = boto3.client('sns')
    topic_name = 'tts-processing-topic'
    
    try:
        response = sns.create_topic(Name=topic_name)
        topic_arn = response['TopicArn']
        
        print(f"✅ SNS topic created: {topic_name}")
        return topic_arn
        
    except Exception as e:
        print(f"❌ Error creating SNS topic: {e}")
        return None

def load_env_credentials():
    """Load AWS credentials from .env file"""
    import os
    
    try:
        # Read .env file
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        
        print("✅ Loaded credentials from .env file")
        return True
        
    except FileNotFoundError:
        print("❌ .env file not found")
        print("📝 Create .env file with your AWS credentials")
        return False
    except Exception as e:
        print(f"❌ Error loading .env file: {e}")
        return False

def main():
    """Main setup function"""
    
    print("🔧 AWS Setup (Python Version)")
    print("=============================\n")
    
    # Load credentials from .env file
    if not load_env_credentials():
        return
    
    # Check AWS credentials
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ AWS Account: {identity['Account']}")
        print(f"✅ Region: us-east-1\n")
    except Exception as e:
        print(f"❌ AWS connection failed: {e}")
        print("📝 Check your credentials in .env file")
        return
    
    # Create resources
    table_name = create_dynamodb_table()
    bucket_name = create_s3_bucket()
    topic_arn = create_sns_topic()
    
    print(f"\n✨ Setup complete!")
    print(f"==================")
    print(f"DYNAMODB_TABLE={table_name}")
    print(f"S3_BUCKET={bucket_name}")
    print(f"SNS_TOPIC_ARN={topic_arn}")
    print(f"AWS_REGION=us-east-1")
    
    print(f"\n📝 Next steps:")
    print(f"1. Update test-text-to-speech.py:")
    print(f"   os.environ['S3_BUCKET'] = '{bucket_name}'")
    print(f"2. Run: python3 test-text-to-speech.py")

if __name__ == "__main__":
    main()