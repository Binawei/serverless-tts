# Serverless TTS Application

React frontend + AWS Lambda backend for text-to-speech conversion.

## Architecture
- **Frontend**: React (S3 + CloudFront)
- **Backend**: Lambda functions (Python)
- **Flow**: Text → Bedrock → Polly → S3 → Audio
- **Auth**: Cognito
- **Storage**: S3 + DynamoDB
- **Events**: SNS + DynamoDB Streams

## AWS Services Required
- Lambda Functions (4)
- DynamoDB Table + Streams
- S3 Bucket
- SNS Topic
- Cognito User Pool + Identity Pool
- CloudFront Distribution
- IAM Roles

## Event Flow
1. User submits text → Upload Lambda
2. DynamoDB record → Stream triggers Text Processor
3. Bedrock processes text → SNS notification
4. Polly Lambda converts to audio → S3
5. Track Lambda provides status/download URLs

## Local Testing Setup

### Prerequisites
- AWS CLI configured with credentials
- Python 3.8+ with pip
- Node.js 16+ with npm
- AWS account with Bedrock access enabled

### Step-by-Step Setup

#### 1. Create AWS Resources
```bash
python3 setup-aws-python.py
```
Note the S3 bucket name from output (e.g., `tts-bucket-1758569760`)

#### 2. Create Cognito Authentication
```bash
python3 setup-cognito.py
```
Note the output values:
- `USER_POOL_ID`
- `USER_POOL_CLIENT_ID`
- `IDENTITY_POOL_ID`

#### 3. Update Frontend Configuration
Edit `frontend-v2/src/utils/config.js`:
```javascript
export const config = {
  API_GATEWAY_URL: 'http://localhost:5001',
  
  // Update with values from step 2
  USER_POOL_ID: 'us-east-1_XXXXXXXX',
  USER_POOL_CLIENT_ID: 'xxxxxxxxxxxxxxxxxx', 
  IDENTITY_POOL_ID: 'us-east-1:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
  
  AWS_REGION: 'us-east-1',
  
  // Update with bucket from step 1
  S3_BUCKET: 'tts-bucket-1758569760',
  
  // ... rest of config
};
```

#### 4. Update Mock API Server
Edit `mock-api-server.py` - replace all bucket references with your actual bucket name

#### 5. Install Dependencies
```bash
pip3 install flask flask-cors python-dotenv PyJWT PyPDF2 boto3
```

#### 6. Start Backend API Server
```bash
python3 mock-api-server.py
```

#### 7. Start Frontend (New Terminal)
```bash
cd frontend-v2
npm install
npm start
```

#### 8. Test End-to-End Flow
1. Open browser to `http://localhost:3000`
2. Register new account with email
3. Login with credentials
4. Convert text to speech
5. Check audio library
6. Download/play audio files

### Quick Test (All Steps)
```bash
python3 test-complete.py
```

### Cleanup Resources
```bash
python3 cleanup-all.py
```