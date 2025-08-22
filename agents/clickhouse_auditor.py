# agents/clickhouse_audit_agent.py

import json
import os
from langchain_openai import AzureChatOpenAI
from mcp_use import MCPAgent
from connectors.mcp_client import create_client_to_running_server_clickhouse
from langchain_core.messages import HumanMessage

# --- STEP 1: LOAD THE AUDITOR'S DETAILED PROCEDURE ---
PROCEDURE_FILENAME = "prompts/clickhouse_audit.txt" 
try:
    # This reads the entire content of the SOP file.
    with open(PROCEDURE_FILENAME, 'r') as f:
        AUDITOR_SOP = f.read()
    print("Auditor's SOP loaded successfully.")
except Exception as e:
    print(f"FATAL ERROR loading auditor SOP: {e}")
    AUDITOR_SOP = "Error: Standard Operating Procedure file not found. I cannot function."

# --- STEP 2: CREATE THE FINAL SYSTEM PROMPT BY WRAPPING THE SOP ---
# This adds the high-level instructions and injects the detailed SOP.
prompt = f"""
You are the ClickHouse Auditor Agent. Your identity and instructions are defined by the Standard Operating Procedure (SOP) provided below.

Your primary role is to act as a secure and reliable interface to a set of predefined audit queries. You must follow the procedure outlined in the SOP with absolute precision. Do not deviate, infer tasks, or perform any action not explicitly described in the procedure.

Your entire operational knowledge base and mandatory workflow are contained in the following SOP.

---
{AUDITOR_SOP}
---
"""

# --- AGENT CREATION LOGIC ---

# --- AGENT CREATION LOGIC ---

# --- AGENT CREATION LOGIC ---

def create_audit_llm(): # <-- RENAMED for clarity
    """
    Initializes and returns the LLM for the ClickHouse Auditor agent.
    """
    # llm = AzureChatOpenAI(
    #     azure_deployment="gpt-4.1-mini",
    #     api_version="2023-06-01-preview",
    #     temperature=0.7, 
    #     max_tokens=4000
    # )
    from langchain_google_genai import ChatGoogleGenerativeAI

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
        # other params...
    )
    return llm

def create_clickhouse_audit_agent(): # <-- RENAMED to be more specific
    """
    Creates the complete ClickHouse Auditor specialist agent.
    """
    print("--- 🛡️ Building ClickHouse Auditor Agent ---")
    
    client = create_client_to_running_server_clickhouse()
    llm = create_audit_llm()

    agent = MCPAgent(
        llm=llm,
        client=client,
        system_prompt=prompt,
        max_steps=25,
        memory_enabled=False
    )
    
    print("--- ✅ ClickHouse Auditor Agent is built and ready. ---")
    return agent

# --- LANGGRAPH NODE ---

async def clickhouse_audit_node(state: dict): # <-- RENAMED to be more specific
    """
    Executes the ClickHouse Auditor agent on the user's query.
    """
    print("--- 🛡️ CLICKHOUSE AUDITOR NODE: Starting investigation... ---")
    
    agent = create_clickhouse_audit_agent()
    user_query = state['messages'][-1].content

    try:
        response = await agent.run(user_query)
    except Exception as e:
        response = f"An error occurred while running the ClickHouse Auditor agent: {e}"
    
    await agent.client.close_all_sessions()
    
    print(f"--- ✅ ClickHouse Auditor agent finished with response: {response} ---")
    
    return {"messages": [HumanMessage(content=response)]}