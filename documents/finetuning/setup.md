# Hugging Face Setup Guide

This guide explains how to set up your Hugging Face account and environment to access gated datasets like **The Stack v1**.

## 1. Create a Hugging Face Account
If you haven't already, sign up at [huggingface.co](https://huggingface.co/join).

## 2. Get your Access Token (HUGGINGFACE_TOKEN)
To download datasets via the API or Axolotl, you need an Access Token.

1.  Go to your **[Settings > Access Tokens](https://huggingface.co/settings/tokens)**.
2.  Click **"New token"**.
3.  **Name**: Give it a name (e.g., "Axolotl-Training").
4.  **Type**: Select **"Read"** (unless you plan to upload models, then use "Write").
5.  **Copy**: Save the token securely. You will need it for your `docker-compose.yml`.

Some datasets, like **The Stack v1**, require you to "Agree to Terms" before downloading.

1.  Visit the dataset page: [bigcode/the-stack](https://huggingface.co/datasets/bigcode/the-stack).
2.  Log in to your account.
3.  Read the terms and click **"Agree to Terms"** or **"Access Dataset"**.
4.  Once approved, your `HUGGINGFACE_TOKEN` will be authorized to pull the data.

## 4. Configure Environment
1.  Navigate to `deployments/axolotl`.
2.  Copy the example environment file: `cp .env.example .env` (In Windows: `copy .env.example .env`).
3.  Open `.env` and paste your token.

The `docker-compose.yml` is configured to use this token automatically:

```yaml
    environment:
      - HF_TOKEN=${HF_TOKEN}
      - WANDB_DISABLED=true
```

## 5. Troubleshooting
- **Error: 401 Unauthorized**: Check if your token is correct and has "Read" permissions.
- **Error: 403 Forbidden**: Ensure you have clicked "Agree to Terms" on the dataset's Hugging Face page.
- **Quota Issues**: Some datasets are very large; ensure you have enough disk space in your `dataset` and `output` volumes.
