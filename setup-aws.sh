#!/bin/bash

echo "🔧 AWS Setup Helper"
echo "==================="

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not installed"
    echo "Install with: brew install awscli"
    exit 1
fi

echo "✅ AWS CLI found"

# Check current configuration
echo ""
echo "📋 Current AWS Configuration:"
aws configure list 2>/dev/null || echo "❌ No AWS configuration found"

echo ""
echo "🚀 Quick Setup Options:"
echo "1. Configure AWS CLI interactively"
echo "2. Set environment variables for this session"
echo "3. Check current configuration"

read -p "Choose option (1-3): " choice

case $choice in
    1)
        echo "🔧 Running AWS configure..."
        aws configure
        ;;
    2)
        echo "🔧 Setting environment variables..."
        read -p "Enter AWS Access Key ID: " access_key
        read -s -p "Enter AWS Secret Access Key: " secret_key
        echo ""
        read -p "Enter AWS Region (default: us-east-1): " region
        region=${region:-us-east-1}
        
        export AWS_ACCESS_KEY_ID=$access_key
        export AWS_SECRET_ACCESS_KEY=$secret_key
        export AWS_DEFAULT_REGION=$region
        
        echo "✅ Environment variables set for this session"
        echo "To make permanent, add to your ~/.bashrc or ~/.zshrc:"
        echo "export AWS_ACCESS_KEY_ID=$access_key"
        echo "export AWS_SECRET_ACCESS_KEY=$secret_key"
        echo "export AWS_DEFAULT_REGION=$region"
        ;;
    3)
        echo "📋 Current Configuration:"
        aws configure list
        aws sts get-caller-identity 2>/dev/null || echo "❌ Cannot verify credentials"
        ;;
    *)
        echo "❌ Invalid choice"
        ;;
esac

echo ""
echo "🧪 Test AWS connection:"
echo "python3 quick-test.py"