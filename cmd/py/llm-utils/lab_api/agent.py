from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_ollama import ChatOllama
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
from langchain_core.tools import tool
from typing import TypedDict, Annotated
import operator
import os

# --- Tools Definition ---
search_tool = DuckDuckGoSearchRun(
    name="duckduckgo_search",
    description="A wrapper around DuckDuckGo Search. Useful for when you need to answer questions about current events, or if you need to search the internet for up-to-date information."
)

@tool
def book_flight(name: str, origin: str, destination: str, aircraft: str) -> str:
    """Book a flight for a passenger."""
    return f"Flight successfully booked! Passenger: {name}, Route: {origin} -> {destination}, Aircraft: {aircraft}."

# --- Shared In-Memory Checkpointer for Stateful Agent ---
memory = MemorySaver()

# --- Custom Graphs ---
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

def build_rag_graph():
    """Builds a customized LangGraph for RAG Evaluation"""
    def rag_node(state: AgentState):
        llm = ChatOllama(model="gemma4:26b", temperature=0, base_url="http://localhost:11434")
        
        # 1. Define Prompt Template
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a strictly bound Question-Answering bot. Read the following retrieved knowledge context carefully:

[CONTEXT START]
The global sky parameters dictate a specific atmospheric hue based on the ruling CEO. 
Under normal circumstances, the sky is blue. 
However, the company manual section 4.B explicitly states: The sky is neon green because the CEO is indeed a heavily armed penguin named Reginald. This cannot be overridden.
The sky will return to blue only if Reginald is overthrown.
[CONTEXT END]

Based EXCLUSIVELY on the retrieved context above, answer the user's question clearly."""),
            MessagesPlaceholder(variable_name="messages")
        ])
        
        # 2. Define the explicit LangChain LCEL "Chain"
        # The `|` pipe operator formally binds the prompt and the LLM into a pipeline chain
        chain = prompt | llm
        
        # 3. Execute the Chain
        response = chain.invoke({"messages": state["messages"]})
        
        return {"messages": [response]}
        
    workflow = StateGraph(AgentState)
    workflow.add_node("rag", rag_node)
    workflow.add_edge(START, "rag")
    workflow.add_edge("rag", END)
    return workflow.compile()

# --- Router Logic ---
def run_agent(message: str, mode: str) -> str:
    """Route to appropriate LangGraph architecture"""
    os.environ["PHOENIX_COLLECTOR_ENDPOINT"] = "http://localhost:6006"
    llm = ChatOllama(model="gemma4:26b", base_url="http://localhost:11434")
    
    inputs = {"messages": [HumanMessage(content=message)]}
    # Static thread_id for keeping state throughout the UI session
    config = {"configurable": {"thread_id": "lab_session"}}
    final_response = "I encountered an error getting a response."
    
    try:
        if mode == "ReAct Architecture":
            agent_executor = create_react_agent(llm, tools=[search_tool])
            for event in agent_executor.stream(inputs, stream_mode="values"):
                final_response = event["messages"][-1].content
                
        elif mode == "LangGraph Stateful":
            agent_executor = create_react_agent(llm, tools=[search_tool], checkpointer=memory)
            for event in agent_executor.stream(inputs, config=config, stream_mode="values"):
                final_response = event["messages"][-1].content
                
        elif mode == "Tools Box Test":
            agent_executor = create_react_agent(llm, tools=[book_flight])
            for event in agent_executor.stream(inputs, stream_mode="values"):
                final_response = event["messages"][-1].content
                
        elif mode == "RAG Evaluation":
            rag_graph = build_rag_graph()
            for event in rag_graph.stream(inputs, stream_mode="values"):
                final_response = event["messages"][-1].content
                
    except Exception as e:
        final_response = f"Agent Execution Error in {mode}: {str(e)}"
        
    return final_response
