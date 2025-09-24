#!/usr/bin/env python3
import boto3
import os
from botocore.exceptions import ClientError

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

def cleanup_all_aws_resources():
    print("🧹 Starting complete AWS cleanup...")
    
    if not load_env_credentials():
        return
    
    # AWS clients
    cognito = boto3.client('cognito-idp', region_name='us-east-1')
    cognito_identity = boto3.client('cognito-identity', region_name='us-east-1')
    dynamodb = boto3.client('dynamodb', region_name='us-east-1')
    s3 = boto3.client('s3', region_name='us-east-1')
    sns = boto3.client('sns', region_name='us-east-1')
    
    # 1. Cleanup Cognito
    print("\n1️⃣ Cleaning up Cognito...")
    try:
        # Find and delete Identity Pools
        pools = cognito_identity.list_identity_pools(MaxResults=60)['IdentityPools']
        for pool in pools:
            if 'tts' in pool['IdentityPoolName'].lower():
                cognito_identity.delete_identity_pool(IdentityPoolId=pool['IdentityPoolId'])
                print(f"✅ Deleted Identity Pool: {pool['IdentityPoolId']}")
    except Exception as e:
        print(f"❌ Identity Pool: {e}")
    
    try:
        # Find and delete User Pool domains first
        pools = cognito.list_user_pools(MaxResults=60)['UserPools']
        for pool in pools:
            if 'tts' in pool['Name'].lower():
                pool_id = pool['Id']
                # Try to get domain info from the User Pool
                try:
                    pool_details = cognito.describe_user_pool(UserPoolId=pool_id)
                    domain = pool_details.get('UserPool', {}).get('Domain')
                    if domain:
                        cognito.delete_user_pool_domain(Domain=domain, UserPoolId=pool_id)
                        print(f"✅ Deleted User Pool Domain: {domain}")
                        import time
                        time.sleep(3)  # Wait for domain deletion
                except Exception as domain_e:
                    print(f"⚠️ Domain deletion: {domain_e}")
                
                # Now delete the User Pool
                try:
                    cognito.delete_user_pool(UserPoolId=pool_id)
                    print(f"✅ Deleted User Pool: {pool_id}")
                except Exception as pool_e:
                    print(f"❌ User Pool deletion: {pool_e}")
    except Exception as e:
        print(f"❌ User Pool: {e}")
    
    # 2. Cleanup DynamoDB
    print("\n2️⃣ Cleaning up DynamoDB...")
    try:
        tables = dynamodb.list_tables()['TableNames']
        for table_name in tables:
            if 'tts' in table_name.lower():
                dynamodb.delete_table(TableName=table_name)
                print(f"✅ Deleted DynamoDB table: {table_name}")
    except Exception as e:
        print(f"❌ DynamoDB: {e}")
    
    # 3. Cleanup S3
    print("\n3️⃣ Cleaning up S3...")
    try:
        buckets = s3.list_buckets()['Buckets']
        for bucket in buckets:
            if 'tts' in bucket['Name'].lower():
                bucket_name = bucket['Name']
                # Delete all objects first
                try:
                    response = s3.list_objects_v2(Bucket=bucket_name)
                    if 'Contents' in response:
                        objects = [{'Key': obj['Key']} for obj in response['Contents']]
                        s3.delete_objects(Bucket=bucket_name, Delete={'Objects': objects})
                        print(f"✅ Deleted {len(objects)} objects from S3")
                    
                    s3.delete_bucket(Bucket=bucket_name)
                    print(f"✅ Deleted S3 bucket: {bucket_name}")
                except Exception as e:
                    print(f"❌ S3 bucket {bucket_name}: {e}")
    except Exception as e:
        print(f"❌ S3: {e}")
    
    # 4. Cleanup SNS
    print("\n4️⃣ Cleaning up SNS...")
    try:
        topics = sns.list_topics()['Topics']
        for topic in topics:
            topic_arn = topic['TopicArn']
            if 'tts' in topic_arn.lower():
                sns.delete_topic(TopicArn=topic_arn)
                topic_name = topic_arn.split(':')[-1]
                print(f"✅ Deleted SNS topic: {topic_name}")
    except Exception as e:
        print(f"❌ SNS: {e}")
    
    # 5. Cleanup local files
    print("\n5️⃣ Cleaning up local files...")
    try:
        import glob
        test_files = glob.glob('test-*.mp3') + glob.glob('test-*.txt') + glob.glob('*.mp3')
        for file in test_files:
            os.remove(file)
            print(f"✅ Deleted local file: {file}")
        if not test_files:
            print("✅ No local test files to clean")
    except Exception as e:
        print(f"❌ Local files: {e}")
    
    print("\n🎉 Complete AWS cleanup finished!")
    print("All resources have been removed to avoid charges.")

if __name__ == "__main__":
    cleanup_all_aws_resources()