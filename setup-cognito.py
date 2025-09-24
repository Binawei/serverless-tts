#!/usr/bin/env python3
import boto3
import json
import os
import sys
from botocore.exceptions import ClientError

def load_env_credentials():
    """Load AWS credentials from .env file"""
    try:
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
        return False
    except Exception as e:
        print(f"❌ Error loading .env file: {e}")
        return False

def create_cognito_resources():
    cognito = boto3.client('cognito-idp', region_name='us-east-1')
    
    try:
        # Create User Pool
        user_pool = cognito.create_user_pool(
            PoolName='tts-user-pool',
            Policies={
                'PasswordPolicy': {
                    'MinimumLength': 8,
                    'RequireUppercase': True,
                    'RequireLowercase': True,
                    'RequireNumbers': True,
                    'RequireSymbols': False
                }
            },
            LambdaConfig={},
            AutoVerifiedAttributes=['email'],
            UsernameAttributes=['email'],
            Schema=[
                {
                    'Name': 'email',
                    'AttributeDataType': 'String',
                    'Required': True,
                    'Mutable': True
                },
                {
                    'Name': 'phone_number',
                    'AttributeDataType': 'String',
                    'Required': False,
                    'Mutable': True
                },
                {
                    'Name': 'preferred_username',
                    'AttributeDataType': 'String',
                    'Required': False,
                    'Mutable': True
                }
            ],
            AccountRecoverySetting={
                'RecoveryMechanisms': [
                    {'Name': 'verified_email', 'Priority': 1}
                ]
            }
        )
        
        user_pool_id = user_pool['UserPool']['Id']
        print(f"User Pool created: {user_pool_id}")
        
        # Create Google Identity Provider with actual credentials
        google_client_id = os.environ.get('GOOGLE_CLIENT_ID')
        google_client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')
        
        if google_client_id and google_client_secret:
            try:
                cognito.create_identity_provider(
                    UserPoolId=user_pool_id,
                    ProviderName='Google',
                    ProviderType='Google',
                    ProviderDetails={
                        'client_id': google_client_id,
                        'client_secret': google_client_secret,
                        'authorize_scopes': 'email openid profile'
                    },
                    AttributeMapping={
                        'email': 'email',
                        'given_name': 'given_name',
                        'family_name': 'family_name',
                        'picture': 'picture'
                    }
                )
                print("Google Identity Provider created with credentials")
            except ClientError as e:
                if 'already exists' in str(e):
                    print("Google Identity Provider already exists")
                else:
                    print(f"Google provider creation failed: {e}")
        else:
            print("⚠️  Google credentials not found in .env file")
        
        # Create Facebook Identity Provider with actual credentials
        facebook_app_id = os.environ.get('FACEBOOK_APP_ID')
        facebook_app_secret = os.environ.get('FACEBOOK_APP_SECRET')
        
        if facebook_app_id and facebook_app_secret and facebook_app_id != 'YOUR_FACEBOOK_APP_ID':
            try:
                cognito.create_identity_provider(
                    UserPoolId=user_pool_id,
                    ProviderName='Facebook',
                    ProviderType='Facebook',
                    ProviderDetails={
                        'client_id': facebook_app_id,
                        'client_secret': facebook_app_secret,
                        'authorize_scopes': 'public_profile'
                    },
                    AttributeMapping={
                        'email': 'email',
                        'given_name': 'first_name',
                        'family_name': 'last_name',
                        'picture': 'picture'
                    }
                )
                print("Facebook Identity Provider created with credentials")
            except ClientError as e:
                if 'already exists' in str(e):
                    print("Facebook Identity Provider already exists")
                else:
                    print(f"Facebook provider creation failed: {e}")
        else:
            print("⚠️  Facebook credentials not found in .env file")
        
        # Create User Pool Client with social login support
        client = cognito.create_user_pool_client(
            UserPoolId=user_pool_id,
            ClientName='tts-web-client',
            GenerateSecret=False,
            ExplicitAuthFlows=[
                'ALLOW_USER_SRP_AUTH',
                'ALLOW_REFRESH_TOKEN_AUTH',
                'ALLOW_USER_PASSWORD_AUTH'
            ],
            SupportedIdentityProviders=['COGNITO', 'Google'],
            CallbackURLs=[
                'http://localhost:3000/callback',
                'https://your-domain.com/callback'
            ],
            LogoutURLs=[
                'http://localhost:3000/',
                'https://your-domain.com/'
            ],
            AllowedOAuthFlows=['code'],
            AllowedOAuthScopes=['email', 'openid', 'profile'],
            AllowedOAuthFlowsUserPoolClient=True
        )
        
        client_id = client['UserPoolClient']['ClientId']
        print(f"User Pool Client created: {client_id}")
        
        # Create Identity Pool
        cognito_identity = boto3.client('cognito-identity', region_name='us-east-1')
        
        identity_pool = cognito_identity.create_identity_pool(
            IdentityPoolName='tts_identity_pool',
            AllowUnauthenticatedIdentities=False,
            CognitoIdentityProviders=[
                {
                    'ProviderName': f'cognito-idp.us-east-1.amazonaws.com/{user_pool_id}',
                    'ClientId': client_id,
                    'ServerSideTokenCheck': True
                }
            ]
        )
        
        identity_pool_id = identity_pool['IdentityPoolId']
        print(f"Identity Pool created: {identity_pool_id}")
        
        # Create User Pool Domain - use existing Google-authorized domain
        domain_name = 'tts-app-wry4owok'  # This is already authorized in Google
        try:
            domain = cognito.create_user_pool_domain(
                Domain=domain_name,
                UserPoolId=user_pool_id
            )
            print(f"User Pool Domain created: {domain_name}")
        except ClientError as e:
            if 'already exists' in str(e):
                print(f"Domain {domain_name} already exists - this is fine!")
            else:
                print(f"Domain creation failed: {e}")
                # Don't try alternatives - we need this specific domain for Google OAuth
        
        # Output configuration
        config = {
            'USER_POOL_ID': user_pool_id,
            'USER_POOL_CLIENT_ID': client_id,
            'IDENTITY_POOL_ID': identity_pool_id,
            'USER_POOL_DOMAIN': domain_name,
            'AWS_REGION': 'us-east-1'
        }
        
        print("\nCognito Configuration:")
        print(json.dumps(config, indent=2))
        
        print("\nNext steps:")
        if google_client_id and google_client_secret:
            print("✅ Google OAuth configured automatically")
        else:
            print("1. Add Google credentials to .env file:")
            print("   GOOGLE_CLIENT_ID=your_client_id")
            print("   GOOGLE_CLIENT_SECRET=your_client_secret")
        print("2. Set up Facebook Login in Facebook Developers:")
        print(f"   - Redirect URI: https://{domain_name}.auth.us-east-1.amazoncognito.com/oauth2/idpresponse")
        print("3. Update frontend config with these values")
        
        return config
        
    except ClientError as e:
        print(f"Error creating Cognito resources: {e}")
        return None

def update_google_provider():
    """Update Google Identity Provider with credentials from .env"""
    
    print("🔄 Updating Google Identity Provider...")
    
    cognito = boto3.client('cognito-idp', region_name='us-east-1')
    
    user_pool_id = input("Enter User Pool ID: ").strip()
    if not user_pool_id:
        print("❌ User Pool ID required")
        return
    
    google_client_id = os.environ.get('GOOGLE_CLIENT_ID')
    google_client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')
    
    if not google_client_id or not google_client_secret:
        print("❌ Google credentials not found in .env file")
        return
    
    try:
        cognito.update_identity_provider(
            UserPoolId=user_pool_id,
            ProviderName='Google',
            ProviderDetails={
                'client_id': google_client_id,
                'client_secret': google_client_secret,
                'authorize_scopes': 'email openid profile'
            }
        )
        print("✅ Updated Google Identity Provider")
    except ClientError as e:
        print(f"❌ Error updating Google provider: {e}")

def update_facebook_provider():
    """Update Facebook Identity Provider with actual credentials"""
    
    print("🔄 Updating Facebook Identity Provider...")
    
    cognito = boto3.client('cognito-idp', region_name='us-east-1')
    
    user_pool_id = input("Enter User Pool ID: ").strip()
    if not user_pool_id:
        print("❌ User Pool ID required")
        return
    
    facebook_app_id = input("Enter Facebook App ID: ").strip()
    facebook_app_secret = input("Enter Facebook App Secret: ").strip()
    
    if not facebook_app_id or not facebook_app_secret:
        print("❌ Facebook credentials required")
        return
    
    try:
        cognito.update_identity_provider(
            UserPoolId=user_pool_id,
            ProviderName='Facebook',
            ProviderDetails={
                'client_id': facebook_app_id,
                'client_secret': facebook_app_secret,
                'authorize_scopes': 'email,public_profile'
            }
        )
        print("✅ Updated Facebook Identity Provider")
    except ClientError as e:
        print(f"❌ Error updating Facebook provider: {e}")

if __name__ == '__main__':
    if not load_env_credentials():
        sys.exit(1)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--update-google':
            update_google_provider()
        elif sys.argv[1] == '--update-facebook':
            update_facebook_provider()
        else:
            print("Usage: python3 setup-cognito.py [--update-google|--update-facebook]")
    else:
        create_cognito_resources()