# OAuth Authentication Setup Guide

This guide explains how to set up OAuth authentication for the Prizm-Agent system, enabling users to log in using Google and GitHub accounts.

## Prerequisites

Before setting up OAuth authentication, you'll need:

1. A Google Developer account and project (for Google OAuth)
2. A GitHub account and OAuth App (for GitHub OAuth)
3. Access to set environment variables on your system

## Setting Up Google OAuth

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to "APIs & Services" > "Credentials"
4. Click "Create Credentials" and select "OAuth client ID"
5. Configure the consent screen if prompted
6. For application type, select "Web application"
7. Add authorized redirect URIs:
   - `http://localhost:5000/api/auth/callback/google` (for local development)
   - Add your production URLs if deploying to a server
8. Click "Create" and note your Client ID and Client Secret

## Setting Up GitHub OAuth

1. Go to your [GitHub Developer Settings](https://github.com/settings/developers)
2. Click "New OAuth App"
3. Fill in the application details:
   - Application name: "Prizm Agent" (or your preferred name)
   - Homepage URL: `http://localhost:5000` (or your production URL)
   - Authorization callback URL: `http://localhost:5000/api/auth/callback/github`
4. Click "Register application"
5. Note your Client ID and generate a Client Secret

## Configuring OAuth Credentials

### Option 1: Using a .env File (Recommended for Development)

The project supports loading OAuth credentials from a `.env` file in the project root directory. This is the recommended approach for local development.

1. Create or edit the `.env` file in the project root directory
2. Add the following configuration variables:

```
# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# GitHub OAuth
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret

# Flask Session Secret (generate a random string)
SECRET_KEY=your_random_secret_key
```

3. Make sure you have `python-dotenv` installed:

```bash
pip install python-dotenv
```

### Option 2: Using Environment Variables

Alternatively, you can set the environment variables directly in your system:

For Linux/Mac:

```bash
# Google OAuth
export GOOGLE_CLIENT_ID="your_google_client_id"
export GOOGLE_CLIENT_SECRET="your_google_client_secret"

# GitHub OAuth
export GITHUB_CLIENT_ID="your_github_client_id"
export GITHUB_CLIENT_SECRET="your_github_client_secret"

# Flask Session Secret (generate a random string)
export SECRET_KEY="your_random_secret_key"
```

For Windows PowerShell:

```powershell
# Google OAuth
$env:GOOGLE_CLIENT_ID="your_google_client_id"
$env:GOOGLE_CLIENT_SECRET="your_google_client_secret"

# GitHub OAuth
$env:GITHUB_CLIENT_ID="your_github_client_id"
$env:GITHUB_CLIENT_SECRET="your_github_client_secret"

# Flask Session Secret (generate a random string)
$env:SECRET_KEY="your_random_secret_key"
```

## Testing the OAuth Setup

1. Start the Prizm-Agent server:
   ```bash
   python surreal_api_server.py
   ```

2. Open your browser and navigate to `http://localhost:5000`

3. You should be redirected to the login page where you can choose to log in with Google or GitHub

4. After successful login, you'll be redirected to your profile page

## Troubleshooting

If you encounter issues with OAuth login:

1. Check that all environment variables are correctly set
2. Verify that your redirect URIs match exactly what's configured in Google/GitHub
3. Check the server logs for specific error messages
4. Ensure your OAuth applications have the necessary permissions enabled

## Security Considerations

- Never commit OAuth client secrets to your code repository
- Use HTTPS in production environments
- Regularly rotate your client secrets
- Consider using a secure environment variable management system in production
