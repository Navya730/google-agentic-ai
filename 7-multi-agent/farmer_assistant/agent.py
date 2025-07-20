from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool

from .sub_agents.update_personal_information.agent import update_personal_information
from .sub_agents.news_analyst.agent import news_analyst
from .sub_agents.crop_recommendation.agent import crop_recommendation
from .tools.tools import get_current_time

from dotenv import load_dotenv
load_dotenv()

root_agent = Agent(
    name="farmer_assistant",
    model="gemini-2.0-flash-exp",
    description="Farmer Assistant",
    instruction="""
    You are a farmer assistant that is responsible helping farmer with their queries.

    There are multiple queries a farmer can ask. Use the tool/agent for the farmer query:

    For queries related to crop recommendation use the agent:
    crop_recommendation

    Every time you get some personal information use the agent:
    update_personal_information
    
    If the question are related to any kind of news use and current time:
    news_analyst or get_current_time
    """,
    sub_agents=[crop_recommendation, update_personal_information],
    tools=[
        AgentTool(news_analyst),
        get_current_time,
    ],
)
