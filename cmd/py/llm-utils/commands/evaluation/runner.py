import requests
import json
import os
import sys
import subprocess
import tempfile
from typing import List, Dict, Any

# Add project root to sys.path for internal imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))
from internal.py.utils.ui import console, print_panel
from internal.py.utils.config import config

# Telemetry Proxy URL (tracked by Arize Phoenix)
DEBUG_DIR = "evaluation_debug"
if not os.path.exists(DEBUG_DIR):
    os.makedirs(DEBUG_DIR)

# Networking for WSL -> Windows Host
def get_host_ip():
    try:
        # Try to get the default gateway IP in WSL
        import subprocess
        result = subprocess.run(["ip", "route", "show", "default"], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.split()[2]
    except:
        pass
    return "127.0.0.1"

HOST_IP = get_host_ip()
OLLAMA_PROXY_URL = f"http://localhost:11435"
LM_STUDIO_PROXY_URL = f"http://localhost:12345/v1"

def call_llm(model: str, prompt: str, system: str = None, is_json: bool = False) -> str:
    """
    Unified caller for Ollama and OpenAI-compatible (LM Studio) APIs.
    If model starts with 'lms/', it uses LM Studio via lms-proxy.
    """
    if model.startswith("lms/"):
        real_model = model.replace("lms/", "")
        url = f"{LM_STUDIO_PROXY_URL}/responses"

        # Responses API uses 'input' instead of 'messages' array, but allows previous_response_id
        # For evaluation, we only need single turn, so we format input directly
        input_text = f"{system}\n\n{prompt}" if system else prompt

        payload = {
            "model": real_model,
            "input": input_text,
            "temperature": 0.1,
            "max_tokens": 1024,
            "stream": False
        }
        if is_json:
            payload["response_format"] = {"type": "json_object"}

        try:
            response = requests.post(url, json=payload, timeout=600)
            response.raise_for_status()
            data = response.json()
            if "content" in data:
                return data["content"]
            return f"API Error (LMS): Unexpected response format: {data}"
        except Exception as e:
            return f"{{\"error\": \"{str(e)}\"}}" if is_json else f"API Error (LMS): {e}"
    else:
        # Ollama / Proxy path
        url = f"{OLLAMA_PROXY_URL}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {"num_predict": 1024}
        }
        if is_json:
            payload["format"] = "json"

        try:
            response = requests.post(url, json=payload, timeout=600)
            response.raise_for_status()
            return response.json().get("response", "")
        except Exception as e:
            return f"{{\"error\": \"{str(e)}\"}}" if is_json else f"API Error (Ollama): {e}"

def extract_code(text: str) -> str:
    """
    Extracts the first markdown code block from the text.
    If no code block is found, returns the original text.
    """
    import re
    match = re.search(r"```(?:\w+)?\n(.*?)\n```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()

def judge_output(prompt: str, output: str, judge_model: str) -> Dict[str, Any]:
    """
    Uses a stronger model to grade the student's output.
    """
    judge_prompt = f"""
You are an expert code reviewer. Please grade the following LLM-generated code response based on:
1. Correctness: Does it fulfill the instructions? (0-5)
2. Idiomatic: Does it follow best practices for the language? (0-5)
3. Readability: Is it well-structured and commented if necessary? (0-5)

Input Prompt: {prompt}

Generated Output:
---
{output}
---

Provide your response in JSON format:
{{
  "correctness": <int>,
  "idiomatic": <int>,
  "readability": <int>,
  "feedback": "<concise_string>"
}}
"""
    raw_response = call_llm(judge_model, judge_prompt, is_json=True)
    try:
        return json.loads(raw_response)
    except Exception as e:
        return {"error": str(e), "correctness": 0, "idiomatic": 0, "readability": 0, "feedback": f"Judge failed: {raw_response[:100]}"}

def verify_execution(code: str, cmd: str, script: str) -> bool:
    """
    Attempts to run the generated code combined with a verification script.
    """
    suffix = ".py" if "python" in cmd else ".go" if "go" in cmd else ".txt"

    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False) as tmp:
            tmp_name = tmp.name
            # For Go, we might need a more sophisticated wrapper if the LLM didn't provide package main
            full_code = code + "\n" + script
            tmp.write(full_code)

        # Run the command
        # Note: 'go run' needs the file path
        # 'python' needs the file path
        run_cmd = cmd.split() + [tmp_name]

        result = subprocess.run(
            run_cmd,
            capture_output=True,
            text=True,
            timeout=15 # Guard against infinite loops
        )

        # Cleanup
        os.unlink(tmp_name)

        return result.returncode == 0
    except Exception as e:
        console.print(f"    [dim red]Execution failed: {e}[/dim red]")
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        return False

def run_evaluation(models: List[str], eval_set_path: str, judge_model: str = None):
    """
    Runs evaluation against a set of prompts for multiple models and logs to Phoenix.
    """
    if not os.path.exists(eval_set_path):
        console.print(f"[bold red]❌ Error: Eval set file not found at {eval_set_path}[/bold red]")
        return

    with open(eval_set_path, "r") as f:
        eval_set = json.load(f)

    print_panel(f"🚀 [bold]Starting Multi-Model Evaluation (Batch Optimized)[/bold]", style="magenta")
    console.print(f"Models: [yellow]{', '.join(models)}[/yellow]")
    console.print(f"Judge: [cyan]{judge_model if judge_model else 'None'}[/cyan]")
    console.print(f"Eval Set: [cyan]{eval_set_path}[/cyan]\n")

    url_gen = OLLAMA_PROXY_URL + "/api/generate"
    overall_results = {}

    for model in models:
        console.print(f"--- [bold blue]Phase 1: Generating Responses ({model})[/bold blue] ---")
        model_results = []

        system_prompt = "You are a professional coding assistant. Provide ONLY the requested code within a single markdown code block. Do not include any explanation, preamble, or irrelevant content."

        for item in eval_set:
            task_id = item.get("id", "unknown")
            prompt = item.get("prompt", "")
            category = item.get("category", "General")
            expected_keywords = item.get("expected_keywords", [])

            console.print(f"[{category}] [bold]{task_id}[/bold]...")

            try:
                import time
                start_time = time.time()
                raw_output = call_llm(model, prompt, system=system_prompt)
                duration = time.time() - start_time
                output = extract_code(raw_output)
                console.print(f"    [dim]Inference took {duration:.2f}s[/dim]")

                model_results.append({
                    "id": task_id,
                    "prompt": prompt,
                    "raw_output": raw_output,
                    "output": output,
                    "expected_keywords": expected_keywords,
                    "verification_cmd": item.get("verification_cmd"),
                    "verification_script": item.get("verification_script")
                })

            except Exception as e:
                console.print(f"  └─ [bold red]Error: {e}[/bold red]")
                model_results.append({"id": task_id, "error": str(e)})

        # Explicitly unload student model before Judging to free up memory (Ollama only)
        if not model.startswith("lms/"):
            console.print(f"\n[dim]Unloading model {model} to free memory...[/dim]")
            try:
                requests.post(url_gen, json={"model": model, "keep_alive": 0})
            except:
                pass

        # Phase 2: Scoring
        console.print(f"\n--- [bold blue]Phase 2: Scoring Responses[/bold blue] ---")
        final_scores = []
        for res in model_results:
            if "error" in res:
                final_scores.append(res)
                continue

            task_id = res["id"]
            output = res["output"]
            expected_keywords = res["expected_keywords"]
            console.print(f"Scoring [bold]{task_id}[/bold]...")

            # 1. Keyword Check
            found_keywords = [k for k in expected_keywords if k.lower() in output.lower()]
            pass_count = len(found_keywords)
            total_keywords = len(expected_keywords)
            kw_score = (pass_count / total_keywords) if total_keywords > 0 else 1.0

            # 2. Judge (Subjective)
            judge_score = {}
            if judge_model:
                console.print(f"  [dim]Grading with {judge_model}...[/dim]")
                judge_score = judge_output(res["prompt"], output, judge_model)

            # 3. Execution
            exec_pass = None
            if res.get("verification_cmd") and res.get("verification_script"):
                console.print(f"  [dim]Executing verification...[/dim]")
                exec_pass = verify_execution(output, res["verification_cmd"], res["verification_script"])

            # 4. Weighted Score
            j_norm = (judge_score.get('correctness', 0) / 5.0) if judge_score.get('correctness') is not None else kw_score
            e_norm = 1.0 if exec_pass is True else 0.0 if exec_pass is False else j_norm
            weighted_score = (kw_score * 0.2) + (j_norm * 0.4) + (e_norm * 0.4)

            final_scores.append({
                "id": task_id,
                "kw_score": kw_score,
                "judge_score": judge_score,
                "exec_pass": exec_pass,
                "weighted_score": weighted_score,
                "pass_count": pass_count,
                "total_keywords": total_keywords
            })

            # Debug save
            # Sanitize model name for filename
            safe_model_name = model.replace("/", "_").replace(":", "_")
            debug_file = os.path.join(DEBUG_DIR, f"{safe_model_name}_{task_id}.txt")
            with open(debug_file, "w") as f:
                f.write(f"PROMPT:\n{res['prompt']}\n\nRAW_OUTPUT:\n{res['raw_output']}\n\nEXTRACTED_CODE:\n{output}")

        overall_results[model] = final_scores

        # Unload judge model (Ollama only)
        if judge_model and not judge_model.startswith("lms/"):
            console.print(f"[dim]Unloading judge {judge_model}...[/dim]\n")
            try:
                requests.post(url_gen, json={"model": judge_model, "keep_alive": 0})
            except:
                pass

    # Final summary
    console.print("\n" + "="*60)
    console.print("[bold cyan]Multi-Model Summary[/bold cyan]")
    for model, results in overall_results.items():
        avg_kw = sum(r.get('kw_score', 0) for r in results) / len(results) if results else 0
        avg_judge = sum(r.get('judge_score', {}).get('correctness', 0) for r in results if 'judge_score' in r) / len(results) if results else 0
        avg_weighted = sum(r.get('weighted_score', 0) for r in results) / len(results) if results else 0

        exec_results = [r.get('exec_pass') for r in results if r.get('exec_pass') is not None]
        avg_exec = (sum(1 for p in exec_results if p) / len(exec_results)) if exec_results else 0.0
        exec_info = f" | Exec: [cyan]{avg_exec:6.1%}[/cyan]" if exec_results else " | Exec: N/A    "

        console.print(f"[yellow]{model:35}[/yellow] | KW: [green]{avg_kw:6.1%}[/green]{exec_info} | Judge: [magenta]{avg_judge:3.1f}/5[/magenta] | [bold cyan]Score: {avg_weighted:4.2f}[/bold cyan]")
    console.print(f"\nCheck Phoenix at http://localhost:16006 for full traces.")
    console.print("="*60)


def main(model=None, eval_set=None, split_models: str = None, judge: str = None):
    # Determine models to run
    models = []
    if split_models:
        models = [m.strip() for m in split_models.split(",")]
    elif model:
        models = [model]
    else:
        models = [config.get("ollama.base_model", "qwen2.5-coder-14b-ft:latest")]

    # Defaults for judge
    if not judge and config.get("ollama.judge_model"):
        judge = config.get("ollama.judge_model")

    if not eval_set:
        # Try to find eval_set.json in several locations
        locations = [
            "documents/evaluation/eval_set.json",
            "documents/evaluation/eval_set.example.json",
            "eval_set.json"
        ]
        # Fixed path calculation to reach repo root (5 levels up from commands/evaluation/runner.py)
        # runner.py -> evaluation -> commands -> llm-utils -> py -> cmd -> root
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))

        for loc in locations:
            path = os.path.join(repo_root, loc)
            if os.path.exists(path):
                eval_set = path
                break

        if not eval_set:
            console.print(f"[bold yellow]⚠️ No eval set specified and default files not found.[/bold yellow]")
            console.print(f"[dim]Checked project root: {repo_root}[/dim]")
            return

    run_evaluation(models, eval_set, judge)

if __name__ == "__main__":
    main()
