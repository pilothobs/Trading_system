from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

# Load environment variables
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
env_path = os.path.join(parent_dir, '.env')
load_dotenv(env_path)

# Initialize the LLM
llm = ChatOpenAI(model="gpt-4-turbo-preview")

# Create Specialized Agents
technical_analyst = Agent(
    role='Technical Analyst',
    goal='Analyze technical indicators and chart patterns',
    backstory="""You are an expert in technical analysis, specializing in:
    - Chart patterns
    - Technical indicators (RSI, MACD, etc.)
    - Support/resistance levels
    - Price action analysis""",
    tools=[],
    llm=llm
)

fundamental_analyst = Agent(
    role='Fundamental Analyst',
    goal='Analyze economic data and market sentiment',
    backstory="""You are an expert in fundamental analysis, focusing on:
    - Economic indicators
    - Central bank policies
    - Market news and sentiment
    - Global economic trends""",
    tools=[],
    llm=llm
)

risk_manager = Agent(
    role='Risk Manager',
    goal='Determine optimal position sizing and risk levels',
    backstory="""You are a conservative risk manager who:
    - Sets appropriate stop loss levels
    - Calculates optimal position sizes
    - Ensures risk-reward ratios are favorable
    - Manages overall portfolio risk""",
    tools=[],
    llm=llm
)

# Create Tasks
technical_analysis_task = Task(
    description="""Analyze current technical indicators and chart patterns for XAUUSD (Gold). Provide:
    - Key support/resistance levels
    - Relevant technical indicators (RSI, MACD, Moving Averages)
    - Chart pattern analysis
    Focus specifically on XAUUSD (Gold) price action.""",
    expected_output="A technical analysis summary for XAUUSD with specific levels and patterns identified.",
    agent=technical_analyst
)

fundamental_analysis_task = Task(
    description="""Review current economic conditions and news affecting Gold (XAUUSD). Identify:
    - Key economic events affecting gold prices
    - US Dollar strength/weakness
    - Market risk sentiment
    - Inflation expectations
    - Geopolitical factors affecting gold
    Focus on factors that directly impact gold prices.""",
    expected_output="A fundamental analysis summary with key gold market drivers identified.",
    agent=fundamental_analyst
)

risk_assessment_task = Task(
    description="""Based on the technical and fundamental analysis, provide a trade recommendation for XAUUSD:
    PAIR: XAUUSD.PRO
    POSITION: [LONG/SHORT]
    ENTRY: [specific price range in USD]
    STOP LOSS: [specific price in USD]
    TAKE PROFIT: [specific price in USD]
    POSITION SIZE: [recommended size]
    REASON: [1-2 sentences only]""",
    expected_output="A complete trade recommendation for XAUUSD with risk management parameters.",
    agent=risk_manager
)

# Create Crew
trading_crew = Crew(
    agents=[technical_analyst, fundamental_analyst, risk_manager],
    tasks=[technical_analysis_task, fundamental_analysis_task, risk_assessment_task],
    verbose=True
)

# Add this if block to execute the code when run directly
if __name__ == "__main__":
    # Run the crew
    result = trading_crew.kickoff()
    print("\nFinal Trade Recommendation:")
    print(result)