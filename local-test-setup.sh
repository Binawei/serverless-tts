#!/bin/bash

# AWS Setup Script for Local Testing
# Make sure AWS CLI is configured with proper credentials

echo "Setting up AWS resources for TTS testing..."

# Variables
REGION="us-east-1"
TABLE_NAME="tts-requests"
BUCKET_NAME="tts-buccket-$(date +%s)"  # Unique bucket name
TOPIC_NAME="tts-processing-topic"

echo "Creating DynamoDB table..."
aws dynamodb create-table \
  --table-name $TABLE_NAME \
  --attribute-definitions AttributeName=reference_key,AttributeType=S \
  --key-schema AttributeName=reference_key,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --stream-specification StreamEnabled=true,StreamViewType=NEW_AND_OLD_IMAGES \
  --region $REGION

echo "Creating S3 bucket..."
aws s3 mb s3://$BUCKET_NAME --region $REGION

echo "Creating SNS topic..."
TOPIC_ARN=$(aws sns create-topic --name $TOPIC_NAME --region $REGION --output text --query 'TopicArn')

echo "Setup complete!"
echo "DYNAMODB_TABLE=$TABLE_NAME"
echo "S3_BUCKET=$BUCKET_NAME"
echo "SNS_TOPIC_ARN=$TOPIC_ARN"
echo "AWS_REGION=$REGION"