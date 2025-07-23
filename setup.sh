#!/bin/bash

set -e

# --- Backend setup ---
cd backend

# Check for GOOGLE_API_KEY in .env (backend or project root)
if [ -f .env ]; then
    ENV_FILE=".env"
elif [ -f ../.env ]; then
    ENV_FILE="../.env"
else
    echo "ERROR: .env file not found in backend or project root."
    exit 1
fi

if ! grep -q "^GOOGLE_API_KEY=" "$ENV_FILE"; then
    echo "ERROR: GOOGLE_API_KEY not found in $ENV_FILE"
    exit 1
fi

# Create venv if not present
if [ ! -d "venv" ]; then
    pyenv local 3.11
    pyenv exec python -m venv venv
fi

# Activate venv and install requirements
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

# --- Frontend setup ---
cd ../frontend
npm install

echo "Setup complete!"