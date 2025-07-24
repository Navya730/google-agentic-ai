from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext

def personal_information(topic: str, tool_context: ToolContext) -> dict:
    """Store personal information"""
    print(f"--- Tool: personal_information called for topic: {topic} ---")

    crops = {

    }
    tool_context.state["crops"] = topic

    return {"status": "success"}


# Create the funny nerd agent
update_personal_information = Agent(
    name="update_personal_information",
    model="gemini-2.0-flash",
    description="An agent that helps update any kind of personal information in the data store",
    instruction="""
    "You are a data management agent responsible for updating personal information.
    When a user provides updated personal details such as name, address, phone number, email, date of birth, or other identifiable fields, your role is to validate the input for completeness and correctness, and then trigger the appropriate database update function. Ensure the information provided matches required formats (e.g., valid email, phone number format, correct date format). Do not guess missing values. If critical data is missing, ask the user for clarification before proceeding. Do not update any data unless you are confident that the information is correct and intended to replace the existing record."
    """,
    tools=[personal_information],
)
