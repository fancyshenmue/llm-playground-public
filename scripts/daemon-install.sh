#!/bin/bash
set -e

# Find absolute project path
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." >/dev/null 2>&1 && pwd)"
PIXI_PATH="$(which pixi)"

if [ -z "$PIXI_PATH" ]; then
    echo "Error: pixi not found in PATH."
    exit 1
fi

LOG_DIR="$HOME/.llm-playground/logs"
mkdir -p "$LOG_DIR"

PLIST_PATH="$HOME/Library/LaunchAgents/com.llmplayground.vllm.plist"

cat <<EOF > "$PLIST_PATH"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.llmplayground.vllm</string>
    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PIXI_PATH</string>
        <string>run</string>
        <string>serve-gemma-31b</string>
    </array>
    <key>RunAtLoad</key>
    <false/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$LOG_DIR/vllm.log</string>
    <key>StandardErrorPath</key>
    <string>$LOG_DIR/vllm.log</string>
</dict>
</plist>
EOF

echo "Successfully created LaunchAgent plist at $PLIST_PATH."
echo "You can start the daemon using: pixi run daemon-start"
