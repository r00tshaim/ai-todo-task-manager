#!/bin/bash

# Run backend in new Terminal window
osascript <<EOF
tell application "Terminal"
    do script "cd \"$(pwd)/backend\" && source venv/bin/activate && python server.py"
end tell
EOF

# Run frontend in new Terminal window
osascript <<EOF
tell application "Terminal"
    do script "cd \"$(pwd)/frontend\" && npm start"
end tell
EOF

echo "Both backend and frontend are starting in new Terminal windows."