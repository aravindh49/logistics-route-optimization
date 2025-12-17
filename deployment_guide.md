# Deployment Guide (Free Hosting on Render)

This guide will help you deploy your Logistics Optimization app to the live web for free.

## Prerequisites
- A GitHub configuration (account).
- This project folder initialized as a Git repository.

## Step 1: Push Code to GitHub
1.  Initialize git if you haven't:
    ```bash
    git init
    git add .
    git commit -m "Ready for deploy"
    ```
2.  Create a new **Public Repository** on GitHub.
3.  Push your code:
    ```bash
    git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
    git branch -M main
    git push -u origin main
    ```

## Step 2: Create App on Render
1.  Go to [dashboard.render.com](https://dashboard.render.com/).
2.  Click **New +** and select **Web Service**.
3.  Choose **Build and deploy from a Git repository**.
4.  Connect your GitHub account and select your repository.

## Step 3: Configure Render Service
Fill in the details:
- **Name**: `logistics-optimizer` (or any name)
- **Region**: Closest to you (e.g., Singapore, Frankfurt)
- **Branch**: `main`
- **Root Directory**: `.` (leave empty)
- **Runtime**: **Python 3**
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn src.api:app --host 0.0.0.0 --port $PORT`
- **Instance Type**: **Free**

## Step 4: Deploy
- Click **Create Web Service**.
- Wait for the build to finish (it might take 2-3 minutes).
- Once green, click the URL (e.g., `https://logistics-optimizer.onrender.com`).

**Note on Free Tier**: The server puts itself to sleep after 15 minutes of inactivity. The first request after sleep might take 30-50 seconds to load.
