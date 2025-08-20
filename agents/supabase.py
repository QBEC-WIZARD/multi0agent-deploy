import os
from langchain_groq import ChatGroq

def create_supabase_llm():
    """
    Initializes and returns the LLM for the Supabase specialist agent.
    """
    llm = ChatGroq(
        model_name="llama3-70b-8192",
        groq_api_key=os.getenv("GROQ_API_KEY")
    )
    return llm


# Defingi the Supabase agent creation function
from connectors.mcp_client import create_and_launch_supabase_client
from mcp_use import MCPAgent

def create_supabase_agent():
    """
    Creates the Supabase agent using the client that will auto-launch the server.
    """
    print("--- 🛠️ Building Supabase MCP Agent (with auto-launch) ---")
    
    # 1. Get the client that knows how to LAUNCH the Supabase MCP server
    client = create_and_launch_supabase_client()
    
    # 2. Get the LLM for this agent
    llm = create_supabase_llm()
    
    # 3. Create the MCPAgent instance. This is the object that has the .run() method.
    agent = MCPAgent(
        llm=llm,
        client=client,
      #  client_name="supabase_server", # Must match the key in our config dictionary
        max_steps=15,
        memory_enabled=False
    )
    print("--- ✅ Supabase MCP Agent is built and ready. ---")
    return agent
