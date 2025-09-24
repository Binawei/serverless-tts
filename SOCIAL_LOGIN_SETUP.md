# Social Login Setup Guide

This guide will help you set up Google and Facebook social login for your TTS application.

## Prerequisites

- AWS CLI configured with appropriate permissions
- Existing Cognito User Pool (already created)
- Google Cloud Console account
- Facebook Developer account

## Step 1: Run the Setup Script

```bash
python3 setup-cognito.py
```

This will:
- Create Cognito User Pool and Identity Pool
- Create a Cognito domain for OAuth
- Configure OAuth settings
- Create placeholder identity providers for Google and Facebook

## Step 2: Set up Google OAuth

### 2.1 Create Google OAuth App

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google+ API
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client IDs"
5. Choose "Web application"
6. Add authorized redirect URIs:
   ```
   https://tts-app-auth.auth.us-east-1.amazoncognito.com/oauth2/idpresponse
   ```
7. Note down the Client ID and Client Secret

### 2.2 Update Google Provider

```bash
python3 setup-cognito.py --update-google
```

Enter your Google Client ID and Client Secret when prompted.

## Step 3: Set up Facebook Login

### 3.1 Create Facebook App

1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Create a new app → "Consumer" type
3. Add "Facebook Login" product
4. In Facebook Login settings:
   - Add Valid OAuth Redirect URIs:
     ```
     https://tts-app-auth.auth.us-east-1.amazoncognito.com/oauth2/idpresponse
     ```
   - Enable "Client OAuth Login"
   - Enable "Web OAuth Login"
5. Note down the App ID and App Secret

### 3.2 Update Facebook Provider

```bash
python3 setup-cognito.py --update-facebook
```

Enter your Facebook App ID and App Secret when prompted.

## Step 4: Update Frontend Configuration

Update your `frontend-v2/src/utils/config.js` with the values from the setup script output:

```javascript
export const config = {
  // ... other config
  USER_POOL_ID: 'us-east-1_XXXXXXXXX',
  USER_POOL_CLIENT_ID: 'xxxxxxxxxxxxxxxxxx',
  IDENTITY_POOL_ID: 'us-east-1:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
  USER_POOL_DOMAIN: 'tts-app-xxxxxxxx',
  // ... rest of config
};
```

## Step 5: Test Social Login

1. Start your frontend:
   ```bash
   cd frontend-v2
   npm start
   ```

2. Navigate to the login page
3. Click "Google" or "Facebook" buttons
4. Complete the OAuth flow
5. You should be redirected back to your app

## Troubleshooting

### Common Issues

1. **Domain already exists error**
   - This is normal if you've run the setup before
   - The script will continue with other configurations

2. **Invalid redirect URI**
   - Ensure the redirect URI in Google/Facebook matches exactly:
     `https://tts-app-auth.auth.us-east-1.amazoncognito.com/oauth2/idpresponse`

3. **Callback page not loading**
   - Check that the Callback component is properly imported in App.js
   - Verify the route `/callback` is handled

4. **Social login button not working**
   - Check browser console for errors
   - Verify USER_POOL_DOMAIN is set in config.js
   - Ensure the domain is active (can take a few minutes after creation)

### Testing Locally

For local development, you may need to:

1. Add localhost callback URLs to your OAuth apps:
   - Google: `http://localhost:3000/callback`
   - Facebook: `http://localhost:3000/callback`

2. Update the Cognito User Pool Client callback URLs to include localhost

## Production Deployment

When deploying to production:

1. Update callback URLs in Google and Facebook apps to use your production domain
2. Update Cognito User Pool Client callback URLs
3. Update the redirect URIs in the OAuth providers to use your production Cognito domain

## Security Considerations

- Never commit OAuth secrets to version control
- Use environment variables for sensitive configuration
- Regularly rotate OAuth secrets
- Monitor OAuth usage in Google/Facebook consoles
- Enable additional security features like App Secret Proof for Facebook

## Additional Features

You can extend social login by:

1. **Adding more providers** (Twitter, LinkedIn, etc.)
2. **Customizing user attributes** mapping
3. **Adding custom scopes** for additional permissions
4. **Implementing logout** from social providers

## Support

If you encounter issues:

1. Check AWS CloudWatch logs for Cognito errors
2. Use browser developer tools to inspect network requests
3. Verify OAuth app configurations in Google/Facebook consoles
4. Test with different browsers/incognito mode