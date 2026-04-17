import os
import subprocess
import operator
from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, START, END
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_ollama import ChatOllama

# Setup Ollama configuration
LLM_KWARGS = {"temperature": 0, "base_url": "http://localhost:11434"}

# PostgreSQL DB details from Docker Compose
DB_URI = "postgresql://postgres:postgres@localhost:5432/langgraph"

# 1. State Definition
class AutoCodeState(TypedDict):
    task: str
    plan: str
    code: str
    lint_errors: str
    iterations: int

# 2. Node Implementations
async def plan_node(state: AutoCodeState, config: RunnableConfig):
    """Generates an architectural plan using the 31B model."""
    print("--- [NODE] Planning ---")
    if state.get("plan"): 
        print("Plan already exists, skipping generation.")
        return {"iterations": state.get("iterations", 0)}
        
    llm = ChatOllama(model="gemma4:31b", **LLM_KWARGS)
    prompt = f"Create a brief bullet-point technical plan to implement this feature in Python: {state['task']}"
    response = await llm.ainvoke([HumanMessage(content=prompt)], config=config)
    
    return {"plan": response.content, "iterations": state.get("iterations", 0)}

async def code_node(state: AutoCodeState, config: RunnableConfig):
    """Writes the code using the 26B MoE model for speed."""
    print(f"--- [NODE] Coding (Iteration {state['iterations'] + 1}) ---")
    llm = ChatOllama(model="gemma4:26b", **LLM_KWARGS)
    
    if state.get("lint_errors") and state.get("lint_errors") != "PASS":
        # Reflection Fix Mode
        sys_prompt = "You are an expert Python debugger. Fix the code according to the errors. Output ONLY raw python code, no markdown blocks, no explanations."
        user_prompt = f"Previous Code:\n{state['code']}\n\nErrors:\n{state['lint_errors']}"
    else:
        # Initial Gen Mode
        sys_prompt = "You are an elite Python developer. Output ONLY raw python code, no markdown block syntax (` ` `python ...), no explanations. The code must be immediately executable."
        user_prompt = f"Plan: {state['plan']}\n\nTask: {state['task']}"

    response = await llm.ainvoke([
        SystemMessage(content=sys_prompt),
        HumanMessage(content=user_prompt)
    ], config=config)
    
    # Very basic cleaner if the model still drops markdown quotes
    clean_code = response.content.replace("```python", "").replace("```", "").strip()
    return {"code": clean_code, "iterations": state["iterations"] + 1}

async def lint_test_node(state: AutoCodeState):
    """Executes the code in a local subprocess to verify it runs."""
    print("--- [NODE] Native Sandbox Testing ---")
    code = state["code"]
    test_filepath = "/tmp/auto_coder_exec.py"
    
    with open(test_filepath, "w") as f:
        f.write(code)
        
    try:
        result = subprocess.run(
            ["python", test_filepath], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        if result.returncode != 0:
            print(f"⚠️ SandBox Failed: {result.stderr.strip()[:100]}...")
            return {"lint_errors": f"Execution Error:\n{result.stderr}"}
            
        print("✅ SandBox Passed!")
        return {"lint_errors": "PASS"}
    except Exception as e:
        print(f"⚠️ SandBox Exception: {str(e)}")
        return {"lint_errors": str(e)}

async def reflect_router(state: AutoCodeState) -> Literal["code_node", "eval_commit_node"]:
    """Determines whether to retry or finalize the code."""
    if state["lint_errors"] == "PASS" or state["iterations"] >= 3:
        return "eval_commit_node"
    return "code_node"

async def eval_commit_node(state: AutoCodeState):
    """Finalizes the successful execution."""
    print("--- [NODE] Commit ---")
    return {"plan": state["plan"]}

# 3. Graph Compilation
def build_graph() -> StateGraph:
    workflow = StateGraph(AutoCodeState)
    workflow.add_node("plan_node", plan_node)
    workflow.add_node("code_node", code_node)
    workflow.add_node("lint_test_node", lint_test_node)
    workflow.add_node("eval_commit_node", eval_commit_node)

    workflow.add_edge(START, "plan_node")
    workflow.add_edge("plan_node", "code_node")
    workflow.add_edge("code_node", "lint_test_node")
    workflow.add_conditional_edges("lint_test_node", reflect_router)
    workflow.add_edge("eval_commit_node", END)
    
    return workflow

# 4. Agent Invocation with Persistent PostgreSQL Saver
async def invoke_coding_agent(task: str, thread_id: str):
    workflow = build_graph()
    
    async with AsyncPostgresSaver.from_conn_string(DB_URI) as checkpointer:
        # Sets up persistent tables in postgres automatically
        await checkpointer.setup()
        
        # Compile graph with PG persistent memory
        app = workflow.compile(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": thread_id}}
        
        # Check if we have an existing state, if not provide inputs
        current_state = await app.aget_state(config)
        
        if not current_state.values:
            inputs = {"task": task, "iterations": 0, "lint_errors": ""}
            async for _ in app.astream(inputs, config=config):
                pass
        else:
            # Rehydrate/Resume from Postgres Memory
            print("Resuming from existing PostgreSQL State Thread:", thread_id)
            inputs = {"task": task} 
            async for _ in app.astream(inputs, config=config):
                pass
            
        final_state = await app.aget_state(config)
        return final_state.values

import json

# 5. SSE Streaming Generator
async def stream_coding_agent(task: str, thread_id: str):
    """Streams the Graph execution nodes step-by-step for the UI."""
    workflow = build_graph()
    
    async with AsyncPostgresSaver.from_conn_string(DB_URI) as checkpointer:
        await checkpointer.setup()
        app = workflow.compile(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": thread_id}}
        
        current_state = await app.aget_state(config)
        
        # Yield connection success
        yield f"data: {json.dumps({'type': 'status', 'message': 'Booting Enterprise Auto-Coder Thread...'})}\n\n"
        
        if not current_state.values:
            inputs = {"task": task, "iterations": 0, "lint_errors": ""}
        else:
            yield f"data: {json.dumps({'type': 'status', 'message': f'Resuming Context Thread: {thread_id}'})}\n\n"
            inputs = {"task": task} 
            
        async for output in app.astream(inputs, config=config):
            # Output is a dict with node name as key
            for node_name, state_update in output.items():
                payload = {
                    "type": "node_update",
                    "node": node_name,
                    # Safely pass simple telemetry to the frontend logger
                    "iterations": state_update.get("iterations", 0),
                    "lint_errors": state_update.get("lint_errors", "")
                }
                yield f"data: {json.dumps(payload)}\n\n"
                
        # Send final state snapshot
        final_state = await app.aget_state(config)
        payload = {
            "type": "finished",
            "state": final_state.values
        }
        yield f"data: {json.dumps(payload)}\n\n"
