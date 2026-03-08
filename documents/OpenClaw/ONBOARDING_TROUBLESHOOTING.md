# OpenClaw Onboarding Troubleshooting

This document covers known pitfalls during the `openclaw onboard` wizard flow and how to resolve them using direct config patching.

## 🔍 Diagnosis Cheatsheet

Before troubleshooting, confirm the proxy stack is alive and the model ID is correct:

```bash
# 1. Check proxy is reachable and list available model IDs
curl -s http://10.0.50.228:12345/v1/models | python3 -c "
import json, sys
data = json.load(sys.stdin)
for m in data.get('data', []):
    print(m['id'])
"

# 2. Smoke-test a chat completion (replace MODEL_ID with output from above)
curl -s http://10.0.50.228:12345/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-local" \
  -d '{
    "model": "MODEL_ID",
    "messages": [{"role": "user", "content": "hi"}],
    "max_tokens": 10
  }' | python3 -m json.tool
```

If step 2 returns a valid response, the proxy and LM Studio are healthy. The issue is in OpenClaw's verification step (see below).

---

## ❌ Known Issue: "Verification failed: This operation was aborted"

### Root Cause

OpenClaw's onboarding wizard sends a verification request to the model and waits for a response. Large MoE models (e.g., `qwen3.5-35b-a3b`) take **10–20 seconds** to respond, which exceeds the wizard's internal timeout — even though the model is working correctly.

This affects all model IDs tried through the wizard, regardless of correctness.

### How to Confirm

Check LM Studio's Developer Logs. If you see lines like:

```
[qwen3.5-35b-a3b] Prompt processing progress: 100.0%
[qwen3.5-35b-a3b] Generated prediction:   ← model DID respond
```

…then the model is fine. OpenClaw just timed out before receiving the response.

---

## ✅ Fix: Directly Patch `openclaw.json`

This bypasses the verification wizard entirely.

### Step 1: Backup

```bash
cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.bak
```

### Step 2: Patch (update `WIN11_IP` and `MID` as needed)

```bash
python3 << 'EOF'
import json, os

WIN11_IP = "10.0.50.228"   # Windows host IP visible from OpenClaw WSL
MID = "qwen3.5-35b-a3b"   # Exact model ID from /v1/models

path = os.path.expanduser('~/.openclaw/openclaw.json')
with open(path, 'r') as f:
    config = json.load(f)

# Add provider (safe: does not overwrite existing providers)
config.setdefault('models', {}).setdefault('providers', {})['lms-proxy'] = {
    'baseUrl': f'http://{WIN11_IP}:12345/v1',
    'api': 'openai-completions',
    'apiKey': 'sk-local',
    'models': [{'id': MID, 'name': 'Qwen3.5 35B A3B'}]
}

# Register as agent model (safe: setdefault prevents KeyError on fresh installs)
(config
    .setdefault('agents', {})
    .setdefault('defaults', {})
    .setdefault('models', {}))['lms-proxy/' + MID] = {}

with open(path, 'w') as f:
    json.dump(config, f, indent=2)
print('✅ Done! Model: lms-proxy/' + MID)
EOF
```

### Step 3: Restart Gateway

```bash
systemctl --user restart "openclaw*"
```

### Step 4: Rollback (if needed)

```bash
cp ~/.openclaw/openclaw.json.bak ~/.openclaw/openclaw.json
systemctl --user restart "openclaw*"
```

---

## 🗂️ Available Model IDs (as of 2026-02-26)

These are the model IDs exposed by `lms-proxy` at `http://10.0.50.228:12345/v1`:

| Model ID | Description |
|---|---|
| `qwen3.5-35b-a3b` | 35B MoE (3.5B active) — fastest local option |
| `qwen2.5-coder-32b-instruct-128k` | Dense 32B coder model |
| `qwen3.5-122b-a10b` | 122B MoE (10B active) — sweet spot for quality |
| `qwen3.5-397b-a17b` | 397B MoE — avoid unless 256GB+ RAM |
| `google/gemma-3-4b` | Lightweight Gemma 4B |
| `text-embedding-nomic-embed-text-v1.5` | Text embeddings |

> Model availability depends on what is loaded in LM Studio. Run the diagnosis above to get a live list.

---

## 🧩 Onboarding Wizard Reference

For context, the wizard screens and correct answers when connecting to `lms-proxy`:

| Screen | Choice |
|---|---|
| Model/auth provider | **Custom Provider** |
| API Base URL | `http://10.0.50.228:12345/v1` |
| API Key | `sk-local` |
| Endpoint compatibility | **OpenAI-compatible** |
| Model ID | Exact ID from `/v1/models` (see table above) |

> If verification fails despite correct settings, skip the wizard and use the patch script above.
