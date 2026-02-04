# Connecting GitHub to Azure for Deployment

To enable the GitHub Action to deploy to your Azure Web App, you need to add your **Publish Profile** as a secret in your GitHub repository.

## Step 1: Get the Publish Profile
You already have the Publish Profile XML data (the `<publishData>` snippet you provided).

## Step 2: Add Secret to GitHub
1. Go to your GitHub repository.
2. Navigate to **Settings** > **Secrets and variables** > **Actions**.
3. Click **New repository secret**.
4. Name: `AZURE_WEBAPP_PUBLISH_PROFILE`
5. Value: Paste the **entire** XML content (from `<publishData>` to `</publishData>`).
6. Click **Add secret**.

## Step 3: Trigger Deployment
Once the secret is added, every push to the `master` branch will deploy automatically. (Note: Your workflow is currently configured for the `master` branch).

You can also trigger it manually from the **Actions** tab in GitHub.
