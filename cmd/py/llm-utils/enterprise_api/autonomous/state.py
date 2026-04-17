import operator
from typing import TypedDict, Annotated, Sequence

from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    """
    The deterministic memory structure for the fully autonomous coder.
    This replaces the simple message list from the basic ReAct agent.
    """
    objective: str
    context: str
    plan: str
    test_specs: str
    code_changes: str
    validation_status: str # "pending", "passed", "failed"
    lint_output: str
    test_output: str
    reflection_strategy: str
    retry_count: int
    
    # LangChain core messages for the fundamental interactions 
    messages: Annotated[Sequence[BaseMessage], operator.add]
