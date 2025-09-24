#!/bin/bash

echo "🚀 Setting up VoiceGen Frontend"
echo "==============================="

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed"
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi

echo "✅ Node.js found: $(node --version)"

# Navigate to frontend directory
cd frontend-v2

# Install dependencies
echo "📦 Installing dependencies..."
npm install

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Create .env file template
if [ ! -f .env ]; then
    echo "📝 Creating .env template..."
    cat > .env << EOL
# AWS Configuration - Update these with your actual values
REACT_APP_API_URL=https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com/prod
REACT_APP_USER_POOL_ID=us-east-1_xxxxxxxxx
REACT_APP_USER_POOL_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxx
REACT_APP_IDENTITY_POOL_ID=us-east-1:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
REACT_APP_AWS_REGION=us-east-1
EOL
    echo "✅ .env template created"
    echo "⚠️  Please update .env with your actual AWS values"
else
    echo "⚠️  .env file already exists"
fi

echo ""
echo "🎉 Frontend setup complete!"
echo ""
echo "Next steps:"
echo "1. Update src/utils/config.js with your AWS settings"
echo "2. Update .env file with your actual values"
echo "3. Run: npm start"
echo ""
echo "The app will be available at http://localhost:3000"