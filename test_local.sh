#!/bin/bash

# Local testing script for the check-in bot
# Use this to test the bot before pushing to GitHub

echo "🤖 Check-In Bot - Local Testing"
echo "=================================="
echo ""

# Check if .env file exists for local testing
if [ -f .env ]; then
    echo "Loading .env file..."
    source .env
else
    echo "⚠️  .env file not found"
    echo "Create .env with:"
    echo "  export PRACTICE_API_TOKEN='your_token'"
    echo "  export PRACTICE_API_URL='https://practice.fhsucyber.com'"
    echo "  export INSTRUCTOR_ID='7'"
    exit 1
fi

# Verify environment variables are set
if [ -z "$PRACTICE_API_TOKEN" ]; then
    echo "❌ PRACTICE_API_TOKEN not set"
    exit 1
fi

if [ -z "$PRACTICE_API_URL" ]; then
    echo "❌ PRACTICE_API_URL not set"
    exit 1
fi

if [ -z "$INSTRUCTOR_ID" ]; then
    echo "❌ INSTRUCTOR_ID not set"
    exit 1
fi

echo "✓ Environment variables loaded"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Run the bot
echo "Running bot..."
python checkin_bot.py

echo ""
echo "✅ Local test complete"
echo "Check artifact/ folder for results"
