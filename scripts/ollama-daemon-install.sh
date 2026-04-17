#!/bin/bash
set -e

# Define variables
PLIST_NAME="com.llmplayground.ollama"
PLIST_PATH="$HOME/Library/LaunchAgents/$PLIST_NAME.plist"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PIXI_ENV_DIR="$PROJECT_DIR/.pixi/envs/default"

# Path to the Ollama executable located within the Pixi environment
OLLAMA_EXECUTABLE="$PIXI_ENV_DIR/bin/ollama"

# Log & Model directories
LOG_DIR="$HOME/.llm-playground/logs"
MODELS_DIR="$HOME/.llm-playground/ollama-models"
mkdir -p "$LOG_DIR"
mkdir -p "$MODELS_DIR"

if [ ! -f "$OLLAMA_EXECUTABLE" ]; then
    echo "Error: Ollama executable not found at $OLLAMA_EXECUTABLE"
    echo "Please ensure 'pixi install' has run successfully and 'ollama' is present in the conda dependencies."
    exit 1
fi

cat <<EOF > "$PLIST_PATH"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$PLIST_NAME</string>

    <key>ProgramArguments</key>
    <array>
        <string>$OLLAMA_EXECUTABLE</string>
        <string>serve</string>
    </array>

    <key>EnvironmentVariables</key>
    <dict>
        <key>OLLAMA_HOST</key>
        <string>0.0.0.0:11434</string>
        <key>OLLAMA_MODELS</key>
        <string>$MODELS_DIR</string>
    </dict>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>

    <key>StandardOutPath</key>
    <string>$LOG_DIR/ollama.log</string>
    
    <key>StandardErrorPath</key>
    <string>$LOG_DIR/ollama.log</string>
</dict>
</plist>
EOF

echo "Successfully created LaunchAgent plist at $PLIST_PATH."
echo "You can start the daemon using: pixi run ollama-daemon-start"
