# GitHub Setup Instructions

This document explains how to configure your GitHub repository for the Check-In Bot.

## Step 1: Enable GitHub Actions

1. Go to your repository on GitHub
2. Click **Settings** → **Actions** → **General**
3. Ensure "Allow all actions and reusable workflows" is enabled
4. Click **Save**

## Step 2: Add Secrets and Variables

### Accessing Secrets and Variables

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. You'll see two tabs: **Repository secrets** and **Variables**

### Add Secrets (Private)

Click **New repository secret** and add:

| Name | Value | Example |
|------|-------|---------|
| `PRACTICE_API_TOKEN` | Your Practice Hub API token | `eyJhbGc...` |
| `PRACTICE_API_URL` | Practice Hub API URL | `https://practice.fhsucyber.com` |

**⚠️ WARNING**: Do not share these secrets. They are only used by GitHub Actions and are never logged.

### Add Variables (Public)

Click **New repository variable** and add:

| Name | Value |
|------|-------|
| `INSTRUCTOR_ID` | `7` |

## Step 3: Verify Configuration

1. Go to **Actions** tab in your repository
2. Click **Scheduled Check-In Bot** workflow
3. Click **Run workflow** → **Run workflow** (manual trigger)

The workflow should:
- ✅ Successfully run Python script
- ✅ Create `artifact/` directory
- ✅ Generate `collected.json`
- ✅ Commit and push to repository

## Step 4: Monitor Scheduled Runs

### View Scheduled Workflow Runs

1. Go to **Actions** tab
2. Select **Scheduled Check-In Bot**
3. View run history and logs

### Check Schedule

The workflow is scheduled to run daily at **10:00 AM UTC**.

To change the schedule, edit `.github/workflows/checkin.yml`:
```yaml
schedule:
  - cron: '0 10 * * *'  # Minutes Hours Day Month DayOfWeek (UTC)
```

## Step 5: Verify Artifact Storage

1. After first run, check that `artifact/` folder exists in your repository
2. Verify `artifact/collected.json` contains posts
3. Check `artifact/files/` for downloaded attachments

## Troubleshooting

### Workflow Won't Run

**Problem**: Workflow doesn't appear in Actions tab
- **Solution**: Ensure workflow file is in `.github/workflows/` with `.yml` extension
- Ensure workflow has valid YAML syntax

### Authentication Error

**Problem**: Workflow fails with 401 Unauthorized
- **Solution**: Verify `PRACTICE_API_TOKEN` secret is set correctly
- Check token hasn't expired on Practice Hub

### No Artifacts Generated

**Problem**: `artifact/` folder not created
- **Solution**: Check GitHub Actions logs for errors
- Verify API token has permission to access posts
- Check if `INSTRUCTOR_ID` is correct

### Workflow Timeout

**Problem**: Workflow takes too long and times out
- **Solution**: Reduce number of posts or files (if API has many)
- Increase GitHub Actions timeout in workflow settings

## Accessing GitHub Secrets in Workflow

The workflow accesses secrets via environment variables:

```yaml
env:
  PRACTICE_API_TOKEN: ${{ secrets.PRACTICE_API_TOKEN }}
  PRACTICE_API_URL: ${{ secrets.PRACTICE_API_URL }}
  INSTRUCTOR_ID: ${{ vars.INSTRUCTOR_ID }}
```

The Python script reads these via `os.getenv()`:
```python
API_TOKEN = os.getenv("PRACTICE_API_TOKEN")
API_URL = os.getenv("PRACTICE_API_URL")
INSTRUCTOR_ID = int(os.getenv("INSTRUCTOR_ID", "7"))
```

## Security Best Practices

✅ **DO**:
- Store API tokens as **Secrets** (not Variables)
- Use environment variables in workflow
- Never hardcode credentials in Python code
- Keep `.env` files out of git (in `.gitignore`)
- Review who has access to repository settings

❌ **DON'T**:
- Print secrets in workflow logs
- Commit `.env` files to repository
- Share secret values in code or comments
- Use the same token across multiple projects
- Leave workflows running unnecessarily

## Manual Token Refresh

If you need to update your API token:

1. Get new token from Practice Hub
2. Go to **Settings** → **Secrets and variables** → **Actions**
3. Click the `PRACTICE_API_TOKEN` secret
4. Click **Update secret**
5. Paste new token
6. Click **Update secret**

## Reference

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Secrets Documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Schedule Syntax (Cron)](https://docs.github.com/en/actions/using-workflows/scheduling-workflows)
- [Practice Hub API Documentation](https://practice.fhsucyber.com/docs)
