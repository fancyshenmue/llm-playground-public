from typing import Literal
from langgraph.graph import StateGraph, START, END

from .state import AgentState
from .nodes import AutonomousNodes

def should_continue(state: AgentState) -> Literal["reflect_node", "__end__"]:
    """
    Conditional edge router evaluating the test results and loop limit.
    """
    status = state.get("validation_status", "failed")
    retries = state.get("retry_count", 0)
    MAX_RETRIES = 3
    
    if status == "passed":
        return END
    
    if retries >= MAX_RETRIES:
        # Break the infinite loop if tests keep failing.
        print("\n[red]Max retries exceeded. Exiting closed loop.[/red]")
        return END
    
    return "reflect_node"

def build_autonomous_graph(models: dict, mcp_tools, allowed_dirs: list[str] = None):
    """
    Constructs the deterministic State Machine for the Autonomous Coder.
    """
    builder = StateGraph(AgentState)
    
    # Initialize the node logic wrapper
    nodes = AutonomousNodes(models, mcp_tools, allowed_dirs)
    
    # Add all dedicated nodes
    builder.add_node("plan_node", nodes.plan_node)
    builder.add_node("coder_node", nodes.coder_node)
    builder.add_node("test_node", nodes.test_node)
    builder.add_node("reflect_node", nodes.reflect_node)
    
    # Define rigid edges
    builder.add_edge(START, "plan_node")
    builder.add_edge("plan_node", "coder_node")
    builder.add_edge("coder_node", "test_node")
    
    # Conditional edge after testing
    builder.add_conditional_edges(
        "test_node",
        should_continue,
        {
            "reflect_node": "reflect_node",
            END: END
        }
    )
    
    # Cycle back from reflect to coder
    builder.add_edge("reflect_node", "coder_node")
    
    return builder
