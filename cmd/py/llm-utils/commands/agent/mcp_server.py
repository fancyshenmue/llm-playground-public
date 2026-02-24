import asyncio
import os
import sys
import httpx
from mcp.server.fastmcp import FastMCP

# Ensure we use the PROXY port for telemetry
OLLAMA_PROXY_URL = os.getenv("OLLAMA_PROXY_URL", "http://localhost:11435")

mcp = FastMCP("Local Ollama Agent")

@mcp.tool()
async def chat_with_local_model(prompt: str, model: str = "llama3.2") -> str:
    """
    Chat with a local LLM hosted on Ollama (via Phoenix Telemetry Proxy).
    Use this tool when the user asks to use the 'local model', 'fine-tuned model', or 'Ollama'.

    Args:
        prompt: The user's message or instruction.
        model: The model name to use (default: llama3.2).
    """
    url = f"{OLLAMA_PROXY_URL}/api/chat"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False
    }

    try:
        async with httpx.AsyncClient(timeout=600.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content", "No response content")
    except Exception as e:
        return f"Error communicating with local model: {str(e)}"

if __name__ == "__main__":
    print(f"Starting MCP server on stdio. Proxy URL: {OLLAMA_PROXY_URL}", file=sys.stderr)
    mcp.run()
