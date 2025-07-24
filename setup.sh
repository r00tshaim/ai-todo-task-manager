#!/bin/bash

set -e

PROJECT_ROOT="$(dirname "$(dirname "$0")")"  # absolute path to repo root
cd "$PROJECT_ROOT"

# --- .env discovery ---
if [ -f backend/.env ]; then
    ENV_FILE="backend/.env"
elif [ -f .env ]; then
    ENV_FILE=".env"
else
    echo "ERROR: .env file not found."
    exit 1
fi

# Export all .env variables
export $(grep -v '^#' "$ENV_FILE" | xargs)

# Check for required variables
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "ERROR: GOOGLE_API_KEY not found in $ENV_FILE"
    exit 1
fi
if [ -z "$POSTGRES_URL" ]; then
    echo "ERROR: POSTGRES_URL not found in $ENV_FILE"
    exit 1
fi
if [ -z "$REDIS_HOST" ] || [ -z "$REDIS_PORT" ]; then
    echo "ERROR: REDIS_HOST or REDIS_PORT not found in $ENV_FILE"
    exit 1
fi

# --- Backend setup ---
cd backend

# Create venv if not present
if [ ! -d "venv" ]; then
    if command -v pyenv &> /dev/null; then
        pyenv local 3.11
        pyenv exec python -m venv venv
    else
        python3 -m venv venv
    fi
fi

# Activate venv and install requirements
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt


# --- PostgreSQL setup: create table if needed ---
python - <<EOF
import os
import psycopg

pgurl = os.environ.get("POSTGRES_URL")
if not pgurl:
    raise SystemExit("POSTGRES_URL missing")
conn = psycopg.connect(pgurl)
with conn.cursor() as cur:
    cur.execute("SELECT EXISTS (SELECT FROM pg_tables WHERE tablename = 'store');")
    exists = cur.fetchone()[0]
    if not exists:
        print("Creating 'store' table...")
        cur.execute("""
        CREATE TABLE store (
            namespace VARCHAR(128) NOT NULL,
            key VARCHAR(512) NOT NULL,
            value JSONB NOT NULL,
            PRIMARY KEY (namespace, key)
        );
        """)
        cur.execute("""
        CREATE INDEX store_idx ON store(namespace, key);
        """)
        conn.commit()
    else:
        print("'store' table already exists.")
conn.close()
EOF

deactivate

# --- SQLAlchemy migration for custom models ---
cd ./db
python migrate.py
cd ..


# --- Redis health check ---
python - <<EOF
import os, redis
try:
    r = redis.Redis(host=os.environ.get("REDIS_HOST"), port=int(os.environ.get("REDIS_PORT", 6379)))
    r.ping()
    print("Redis connection OK.")
except Exception as e:
    raise SystemExit(f"ERROR: Cannot connect to Redis at {os.environ.get('REDIS_HOST')}:{os.environ.get('REDIS_PORT')}: {e}")
EOF

# --- Frontend setup ---
cd ../frontend
npm install

echo "Setup complete!"
