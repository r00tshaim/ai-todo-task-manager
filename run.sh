#!/bin/bash

# Run backend in new Terminal window
osascript <<EOF
tell application "Terminal"
    do script "cd \"$(pwd)/backend\" && source venv/bin/activate && uvicorn server:app --host 0.0.0.0 --port 8000 --reload"
end tell
EOF

# Run frontend in new Terminal window
osascript <<EOF
tell application "Terminal"
    do script "cd \"$(pwd)/frontend\" && npm start"
end tell
EOF

# Run worker in new Terminal window
osascript <<EOF
tell application "Terminal"
    do script "cd \"$(pwd)/backend\" && source venv/bin/activate && export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES && rq worker chat_jobs --url redis://localhost:6379"
end tell
EOF

# Start Docker containers
docker-compose -f docker-compose.yml up -d

echo "Backend, frontend, and worker are starting in new Terminal windows."