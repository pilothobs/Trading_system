from langgraph.graph import StateGraph
from langchain_openai import ChatOpenAI
from typing import TypedDict, Annotated
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv
import os

# Load environment variables from the correct path
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)

# Print to verify API key is loaded
print(f"API Key loaded: {'OPENAI_API_KEY' in os.environ}")

# Define the state schema
class State(TypedDict):
    messages: list[HumanMessage | AIMessage]
    trade: str | None

def trading_strategy(state: State) -> State:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
        
    llm = ChatOpenAI(model="gpt-4-turbo-preview", api_key=api_key)
    prompt = HumanMessage(content="""
    You are a forex trading assistant. Provide a specific trade recommendation in this exact format:

    PAIR: [currency pair]
    POSITION: [LONG/SHORT]
    ENTRY: [price range]
    STOP LOSS: [price]
    TAKE PROFIT: [price]
    REASON: [1-2 sentences only]

    No disclaimers or additional information needed.
    """)
    
    trade_idea = llm.invoke([prompt])
    state["messages"] = [prompt, trade_idea]
    state["trade"] = trade_idea.content
    return state

# Initialize with state schema
workflow = StateGraph(state_schema=State)
workflow.add_node("strategy", trading_strategy)
workflow.set_entry_point("strategy")
workflow.compile()

# Initialize state with proper type
initial_state: State = {
    "messages": [],
    "trade": None
}

app = workflow.compile()
result = app.invoke(initial_state)
print("Suggested Trade:", result["trade"])
