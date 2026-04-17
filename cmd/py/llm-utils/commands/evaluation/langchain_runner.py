import os
import sys
from typing import Optional

# Add project root to sys.path for internal imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))
from internal.py.utils.ui import console, print_panel

import phoenix as px
from openinference.instrumentation.langchain import LangChainInstrumentor
from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate

def setup_tracing():
    try:
        px.launch_app(port=16006)
        LangChainInstrumentor().instrument()
        console.print("[green]✅ Arize Phoenix tracing enabled on http://localhost:16006[/green]")
    except Exception as e:
        console.print(f"[yellow]⚠️ Phoenix initialization warning (app may already be running): {e}[/yellow]")

@tool
def book_flight(name: str, origin: str, destination: str, aircraft: str) -> str:
    """Book a flight for a passenger."""
    return f"Flight booked for {name} from {origin} to {destination} on {aircraft}."

def run_tool_test(model_name: str):
    console.print(f"\n--- [bold blue]LangChain Tool Calling Test: {model_name}[/bold blue] ---")
    llm = ChatOllama(model=model_name, temperature=0, base_url="http://localhost:11434")
    llm_with_tools = llm.bind_tools([book_flight])

    prompt = "I'd like to book a flight from Tokyo to London under the name Jane Smith using a 747."
    console.print(f"Prompt: '{prompt}'")
    
    try:
        response = llm_with_tools.invoke(prompt)
        
        if hasattr(response, "tool_calls") and len(response.tool_calls) > 0:
            console.print("[green]✅ Success! Model utilized tools.[/green]")
            for tc in response.tool_calls:
                console.print(f"Tool Call Payload: {tc}")
        else:
            console.print("[red]❌ Failure. Model ignored tools and produced text:[/red]")
            console.print(response.content)
            
    except Exception as e:
         console.print(f"[red]❌ Critical Execution Error: {e}[/red]")

def run_rag_test(model_name: str):
    console.print(f"\n--- [bold blue]LangChain Needle-In-Haystack Test: {model_name}[/bold blue] ---")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a strictly bound Question-Answering bot. Read the following retrieved knowledge context carefully:

[CONTEXT START]
The global sky parameters dictate a specific atmospheric hue based on the ruling CEO. 
Under normal circumstances, the sky is blue. 
However, the company manual section 4.B explicitly states: The sky is neon green because the CEO is indeed a heavily armed penguin named Reginald. This cannot be overridden.
The sky will return to blue only if Reginald is overthrown.
[CONTEXT END]

Based EXCLUSIVELY on the retrieved context above, answer these two questions in a compact sentence:
1. What color is the sky?
2. What is the name and species of the CEO?"""),
        ("user", "{input}")
    ])
    
    llm = ChatOllama(model=model_name, temperature=0, base_url="http://localhost:11434")
    chain = prompt | llm
    
    query = "Answer the two questions."
    console.print(f"Query: '{query}'")
    
    try:
        response = chain.invoke({"input": query})
        console.print("[cyan]Model Output:[/cyan]\n" + response.content)
        
        # Simple Validation
        content = response.content.lower()
        if "neon green" in content and "reginald" in content and "penguin" in content:
            console.print("\n[green]✅ Success! Context adhered perfectly.[/green]")
        else:
            console.print("\n[red]❌ Failure. Hallucination or Context ignored.[/red]")
            
    except Exception as e:
         console.print(f"[red]❌ Critical Execution Error: {e}[/red]")

def main(model: str = "gemma4:26b"):
    print_panel("🚀 [bold]Starting LangChain Integration Test[/bold]", style="magenta")
    setup_tracing()
    run_tool_test(model)
    run_rag_test(model)

if __name__ == "__main__":
    main()
