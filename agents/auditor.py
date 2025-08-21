import json
import os
from langchain_openai import AzureChatOpenAI
from mcp_use import MCPAgent
from connectors.mcp_client import create_client_to_running_server_clickhouse
from langchain_core.messages import HumanMessage # Assuming HumanMessage is used in your graph state

# --- STEP 1: DEFINE THE NEW, GENERIC SYSTEM PROMPT FOR THE AUDITOR AGENT ---

# I've renamed the variable to AUDITOR_PROCEDURE for clarity.
PROCEDURE_FILENAME = "prompts/auditor.txt" 
try:
    with open(PROCEDURE_FILENAME, 'r') as f:
        AUDITOR_PROCEDURE = f.read()
    print("Auditor's detailed procedure loaded successfully.")
except Exception as e:
    print(f"FATAL ERROR loading auditor procedure: {e}")
    AUDITOR_PROCEDURE = "Error: Detailed procedure file not found. I cannot perform my primary function."

# --- STEP 2: CREATE THE FINAL, UNIFIED SYSTEM PROMPT ---

# The generic persona is combined with the detailed, mandatory procedure loaded from the file.
prompt = f"""
You are the Auditor Agent, a specialized AI designed to inspect, verify, and report on data within a ClickHouse database. You are meticulous, precise, and objective.

Your general operational procedure is as follows:
1.  Carefully analyze the user's request to fully understand the audit objective.
2.  Use tools such as `list_tables` to understand the structure of the data you are auditing.
3.  Formulate precise and efficient SQL queries using `run_select_query` to gather evidence.
4.  Provide a clear, concise, and factual summary of your findings.

---
### MANDATORY PROCEDURE FOR 'GAP ANALYSIS' TASKS

When a user provides input in the structured format with a "Dataset," "Question," and "Provided Answer," you MUST cease your general procedure and STRICTLY follow the detailed procedure outlined below. This is your primary and most important function.

{AUDITOR_PROCEDURE}
"""

# --- STEP 2: RENAME AND REPURPOSE THE AGENT CREATION LOGIC ---

def create_llm_for_agent():
    """
    Initializes and returns the LLM for the agent.
    This function remains generic as it only configures the language model.
    """
    llm = AzureChatOpenAI(
        azure_deployment="gpt-4.1-mini",       # your deployed model name on Azure
        api_version="2023-06-01-preview",
        temperature=0.7, 
        max_tokens=4000
    )
    return llm

def create_auditor_agent():
    """
    Creates the complete Auditor specialist agent.
    
    This function will:
    1. Initialize the client to connect to the running ClickHouse server.
    2. Initialize the LLM for the agent.
    3. Create the MCPAgent instance with the new auditor prompt.
    
    Returns:
        An instance of MCPAgent configured as the Auditor.
    """
    print("--- 🛡️ Building Auditor Agent ---")
    
    # 1. Get the client that connects to your running server (server is still ClickHouse)
    client = create_client_to_running_server_clickhouse()
    
    # 2. Get the LLM for this agent
    llm = create_llm_for_agent()

    # 3. Create the agent instance with the new auditor identity
    agent = MCPAgent(
        llm=llm,
        client=client,
        system_prompt=prompt,  # Use the new, generic auditor prompt
        max_steps=25,          # Adjusted max_steps for auditing tasks
        memory_enabled=False
    )
    
    print("--- ✅ Auditor Agent is built and ready. ---")
    return agent

# --- STEP 3: RENAME AND REPURPOSE THE LANGGRAPH NODE ---

async def auditor_node(state: dict):
    """
    Executes the Auditor agent on the user's query.

    Args:
        state (dict): The current state of the graph.

    Returns:
        dict: A dictionary containing the agent's response to be added to the message history.
    """

    print("--- 🛡️ AUDITOR NODE: Starting investigation... ---")
    
    # 1. Create the specialist agent instance
    agent = create_auditor_agent()

    # 2. Get the user's query from the state
    user_query = state['messages'][-1].content

    try:
        response = await agent.run(user_query)
    except Exception as e:
        response = f"An error occurred while running the Auditor agent: {e}"
    
    # Always close the client sessions after the node is done
    await agent.client.close_all_sessions()
    
    print(f"--- ✅ Auditor agent finished with response: {response} ---")

    # 4. Return the response in the correct format to update the state
    return {"messages": [HumanMessage(content=response)]}