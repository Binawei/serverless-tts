# AWS Setup Guide - Serverless TTS

## Processing Flow
1. **Upload Document/Text** → **S3 Storage** → **DynamoDB Record** (Upload-Completed)
2. **DynamoDB Stream** → Document Splitter/Text Processor → Bedrock → S3 → SNS
3. **S3 Event** → Polly Converter → Audio → S3
4. **Track Requests** → List/Download

## 1. DynamoDB Table
```bash
aws dynamodb create-table \
  --table-name tts-requests \
  --attribute-definitions AttributeName=reference_key,AttributeType=S \
  --key-schema AttributeName=reference_key,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --stream-specification StreamEnabled=true,StreamViewType=NEW_AND_OLD_IMAGES
```

## 2. S3 Bucket
```bash
aws s3 mb s3://your-tts-bucket
# Enable event notifications for download/ prefix, .txt suffix
```

## 3. SNS Topic
```bash
aws sns create-topic --name tts-processing-topic
```

## 4. Lambda Functions

### upload-text
- **Trigger**: API Gateway POST /upload
- **Environment**: DYNAMODB_TABLE, S3_BUCKET
- **IAM**: DynamoDB:PutItem, S3:PutObject

### text-processor  
- **Trigger**: DynamoDB Stream (filter: TaskStatus = Upload-Completed)
- **Environment**: DYNAMODB_TABLE, SNS_TOPIC_NAME
- **IAM**: DynamoDB:UpdateItem, S3:GetObject/PutObject, Bedrock:InvokeModel, SNS:Publish

### polly-converter
- **Trigger**: S3 Event (download/ prefix, .txt suffix)
- **Environment**: DYNAMODB_TABLE, S3_BUCKET
- **IAM**: DynamoDB:GetItem/UpdateItem, S3:GetObject/PutObject, Polly:SynthesizeSpeech

### track-requests
- **Trigger**: API Gateway GET/POST /track
- **Environment**: DYNAMODB_TABLE, S3_BUCKET
- **IAM**: DynamoDB:Scan/GetItem, S3:GeneratePresignedUrl

## 5. API Gateway
```bash
# Create REST API with:
# POST /upload → upload-text Lambda
# GET /track → track-requests Lambda  
# POST /track → track-requests Lambda
# Enable CORS and Cognito Authorizer
```

## 6. Cognito Setup
```bash
# Create User Pool
aws cognito-idp create-user-pool --pool-name tts-users

# Create User Pool Client
aws cognito-idp create-user-pool-client \
  --user-pool-id <pool-id> \
  --client-name tts-client

# Create Identity Pool
aws cognito-identity create-identity-pool \
  --identity-pool-name tts-identity \
  --allow-unauthenticated-identities false
```

## 7. Event Configurations

### DynamoDB Stream Filter
```json
{
  "eventName": ["INSERT", "MODIFY"],
  "dynamodb": {
    "NewImage": {
      "TaskStatus": {
        "S": ["Upload-Completed"]
      }
    }
  }
}
```

### S3 Event Notification
- **Prefix**: download/
- **Suffix**: .txt
- **Events**: s3:ObjectCreated:*

## GitHub Secrets
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY  
- AWS_REGION
- USER_POOL_ID
- USER_POOL_CLIENT_ID
- IDENTITY_POOL_ID
- API_GATEWAY_URL
- S3_BUCKET_NAME
- CLOUDFRONT_DISTRIBUTION_ID

## Local Testing
```bash
# Test Lambda locally
sam local start-api

# Frontend
cd frontend
npm install
npm start
```