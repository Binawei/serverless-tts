# Serverless TTS Application

React frontend + AWS Lambda backend for text-to-speech conversion.

## Architecture
- **Frontend**: React (S3 + CloudFront)
- **Backend**: Lambda functions (Python)
- **Flow**: Text → Bedrock → Polly → S3 → Audio
- **Auth**: Cognito
- **Storage**: S3 + DynamoDB
- **Events**: SNS + DynamoDB Streams

## Architecture
![Architecture Diagram](/images/architecture.png)

### Architecture Walkthrough

1. During `terraform apply` deployment, assets are uploaded to the build artifacts Simple Storage Service (S3) bucket.
2. An AWS Lambda function triggers an AWS CodeBuild project that builds the container image for the Document Splitter function and stores it in the Amazon Elastic Container Registry (ECR).
3. The Document Splitter AWS Lambda function is deployed using the image from ECR.
4. After deployment, a user loads the website via the Amazon CloudFront domain url, which serves the static website content from the associated Amazon S3 bucket.
5. The user authenticates via Amazon Cognito and receives temporary credentials for interacting with the service AWS Lambda functions.
6. Via the website UI, the user uploads a PDF document to the Upload Execution AWS Lambda function. It creates a job entry in the Amazon DynamoDB table and stores the PDF in the Document Data Amazon S3 bucket.
7. The new job entry in the Amazon DynamoDB table is processed by the associated DynamoDB Stream which triggers the Document Splitter function. It converts the pages of the document it got from the Amazon S3 bucket to images, stores them back in it, updates the job status in the Amazon DynamoDB table and sends a notification to an Amazon Simple Notification Service (SNS) topic.
8. The Image To Text AWS Lambda function is subscribed to the SNS topic and triggered with the notification. It uses Amazon Bedrock to extract the text from the images it got from the Amazon S3 bucket and puts the result back into it.
9. An Amazon S3 event notification triggers the Text To Voice AWS Lambda function which gets the text file from the bucket, uses Amazon Polly to convert it to an audio file in MP3 format and stores it back in the bucket.
10. Navigating to the Existing Requests page in the UI, the website triggers the Track Execution AWS Lambda function. It lists all jobs including their current status and provides pre-signed URLs for the audio files of the finished jobs for downloading the MP3 files and playing them directly in supported browsers.


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