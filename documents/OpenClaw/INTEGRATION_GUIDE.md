# OpenClaw Integration with LM Studio & Arize Phoenix

This document details the configuration and integration of OpenClaw with a local LM Studio instance and Arize Phoenix for observability.

> [!TIP]
> Having trouble with the onboarding wizard? See [ONBOARDING_TROUBLESHOOTING.md](ONBOARDING_TROUBLESHOOTING.md) for the "Verification failed" fix and direct config patching.

## 🏗️ Architecture Overview

| Service | External Port | Backend |
|---|---|---|
| `ollama-proxy` | `11435` | Ollama (`11434`) |
| `lms-proxy` | **`12345`** | LM Studio Win11 (`1234`) |
| OpenClaw | → `12345` | via `lms-proxy` |
| `runner.py` eval | → Ollama `11434` | independent |

- **OpenClaw**: Isolated WSL distribution (`OpenClaw`), managed by Pixi.
- **LLM Engine**: LM Studio on Windows Host, accessible at `host.docker.internal:1234`.
- **Observability**: Arize Phoenix (Docker) via `lms-proxy` on port **`12345`**.

> [!IMPORTANT]
> OpenClaw runs in a **separate WSL distribution**. `localhost` inside OpenClaw is not the same as the main WSL's `localhost`. Use the **Windows Host IP** (e.g. `10.0.50.228`) to reach Docker services.

## 🚀 Setup Steps

### 1. OpenClaw Environment (in `OpenClaw` WSL distribution)
```bash
mkdir -p ~/projects/openclaw && cd ~/projects/openclaw
pixi init .
pixi add nodejs
pixi run npm i -g openclaw
pixi run openclaw onboard
```

### 2. Configure `openclaw.json` (Source of Truth)

OpenClaw's CLI has limitations with complex model IDs. Use this Python script to set the exact configuration required for `lms-proxy`.

```python
import json, os
path = os.path.expanduser('~/.openclaw/openclaw.json')
with open(path, 'r') as f: config = json.load(f)

# Define custom provider pointing to lms-proxy
config.setdefault('models', {}).setdefault('providers', {})['lms-proxy'] = {
    'baseUrl': f'http://{WIN11_IP}:12345/v1',
    'api': 'openai-completions',
    'apiKey': 'sk-local',
    'models': [{'id': MID, 'name': 'Qwen 3.5 397B'}]
}

# Clean up agents models (no extra keys allowed)
config['agents']['defaults']['models']['lms-proxy/' + MID] = {}

with open(path, 'w') as f: json.dump(config, f, indent=2)
print('✅ Configuration patched!')
"
```

### 3. Restart Gateway and Run
```bash
pixi run openclaw gateway restart
pixi run openclaw tui --session new
```

### 4. Accessing the Dashboard (Web UI)
If you want to use the Web UI instead of the TUI, you need to provide the authentication token.

1.  **Retrieve Token**:
    ```bash
    grep -A 2 "auth" ~/.openclaw/openclaw.json
    ```
2.  **Login**: Open `http://localhost:18789` in your browser. Click the **key icon** in the top right or bottom left, and paste the `token` value (e.g., `1bfceb5289...`).

## �️ Adding Ollama Models via Dashboard (UI Steps)

Using the Dashboard is more stable for adding multiple models like `qwen2.5-coder:32b`.

### Step 1: Add/Configure Ollama Provider
1.  Go to **Settings** (Gear icon) -> **Models** -> **Model Providers**.
2.  Check if an `ollama` provider exists. If not, click **+ Add Entry**.
3.  **Name**: `ollama-local` (or any unique ID).
4.  **Provider API Adapter**: Select **Ollama**.
5.  **Model Provider Base URL**: `http://10.0.50.228:11435` (This uses the `ollama-proxy` for tracing).
6.  **Models**: Click the input and type your model ID exactly: `qwen2.5-coder:32b`.

### Step 2: Set as Primary Model
1.  Go to **Settings** -> **Agents**.
2.  Find **Default Model** -> **Primary**.
3.  Select your new model: `ollama-local/qwen2.5-coder:32b`.

### Step 3: Apply & Refresh
1.  Click **Apply** at the top right of the Settings page.
2.  Go to the **Chat** tab and start a **New Session**.

## �📊 Verification
- **TUI/Dashboard status bar**: Should show `ollama-local/qwen2.5-coder:32b` or `lms-proxy/qwen3.5-397b-a17b`.
- **Arize Phoenix**: Monitor traces at `http://localhost:16006`.

## 🔋 Service Management & Restarts
OpenClaw is modular. If you feel it's becoming unstable or want to apply global config changes, you can restart everything at once.

### The "Restart All" Command
Since your gateway runs as a systemd user service, the most reliable way to restart all potential OpenClaw components (including future nodes) is:
```bash
systemctl --user restart "openclaw*"
```

### Create a Shortcut (Recommended)
Add this to your `~/.zshrc` or `~/.bashrc` to make it a single word:
```bash
alias oc-restart='systemctl --user restart "openclaw*"'
```

### When to use which?
- **`pixi run openclaw gateway restart`**: Standard way, safe and fast.
- **`systemctl --user restart "openclaw*"`**: Use this if the UI is frozen or you suspect child processes (like nodes) are stuck.
- **`openclaw gateway --force`**: Hard reset of the port listener if you get "Port already in use" errors.

### Check Service Status
To see if the services are healthy:
```bash
# Check all OpenClaw services
systemctl --user status "openclaw*"

# View latest gateway logs
journalctl --user -u openclaw-gateway.service -n 50 --no-pager
```

## 🛠️ Troubleshooting & Optimization

### 0. Permission Denied on Workspace (RO vs RW)
- **Problem**: Mounting D: drive via `drvfs` as `ro` (Read-Only) in `/etc/fstab` prevents OpenClaw from saving logs and artifacts.
- **Diagnostics**: `touch /data/test_write` returns "Permission denied".
- **Fix**:
    1. Edit `/etc/fstab`: Change `ro` to `rw`.
    2. Remount: `sudo mount -o remount,rw /data`.
    3. Verify: `mkdir -p /data/openclaw/workspace`.

### 1. `Cannot truncate prompt with n_keep >= n_ctx`
- **Error**: OpenClaw's system prompt (12.6k tokens) is larger than LM Studio's default context window (8k).
- **Fix**: Eject model in LM Studio, set **Context Length** to `32768` (32k) or higher, and reload.

### 2. `run error: terminated`
- **Error**: The proxy or OpenClaw timed out while waitng for the 397B model to process the long system prompt.
- **Fix**:
    - Enable **Unified KV Cache (Experimental)** in LM Studio to avoid re-processing the prompt every turn.
    - Ensure **GPU Offload** is maxed out to avoid slow CPU inference.

### 3. Proxy Customization (`server.py`)
The proxy automatically handles OpenClaw's model addressing by stripping the provider prefix:
```python
# Strip lms-proxy/qwen... -> qwen...
if "/" in model_name:
    model_name = model_name.split("/")[-1]
```

### 4. Observability Mapping
Interactions through the `lms-proxy` are tagged with:
- `llm.system`: `lms`
- `llm.model`: Actual model ID from LM Studio.
- `llm.usage`: Token counts extracted from OpenAI-compatible response.

## 🧠 Model Selection Strategy

### 🏠 Local Hardware Recommendations
For a balance of intelligence and speed in OpenClaw, prioritize **Moderate MoE** models over massive ones:

| Model ID | Architecture | Verdict | Best For |
|---|---|---|---|
| `qwen3.5-35b-a3b` | 35B (3.5B active) | **Fastest** | Daily coding, unit tests, fast iteration. |
| `qwen2.5-coder-32b-instruct-128k` | Dense 32B | **Coder** | Code generation, repo-level tasks. |
| `qwen3.5-122b-a10b` | 122B (10B active) | **Sweet Spot** | Complex refactoring, architectural analysis. |
| `qwen3.5-397b-a17b` | 397B (17B active) | **Inefficient** | Do not use unless you have 256GB+ high-bandwidth RAM. |

> Run `curl -s http://10.0.50.228:12345/v1/models | python3 -m json.tool` to get the live list of models currently loaded in LM Studio.

### ⚠️ The "397B Trap"
Even though 397B only activates 17B parameters, it is often **unusable** on common local hardware because:
1. **Memory Bandwidth**: Fetching specialists from a 397B pool is the primary bottleneck, not the compute.
2. **Pre-fill Delays**: Processing OpenClaw's long system prompts (>12k tokens) on 397B can take 5+ minutes, triggering timeouts.
3. **Truncated Quality**: Frequent timeouts lead to incomplete JSON/code blocks, making the agent "hallucinate" errors that aren't there.

**Recommendation**: Use **122B-A10B** if you need high intelligence; use **35B-A3B** for maximum workflow speed.
