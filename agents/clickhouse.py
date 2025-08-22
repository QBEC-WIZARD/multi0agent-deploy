import os
from langchain_groq import ChatGroq
from mcp_use import MCPAgent

from langchain_openai import AzureChatOpenAI

import json
import os

# # --- Command to Load and CORRECTLY ESCAPE the Manifest ---

# MANIFEST_FILENAME = "analysis_manifest.json"

# try:
#     print(f"Attempting to load the agent's brain from '{MANIFEST_FILENAME}'...")
    
#     with open(MANIFEST_FILENAME, 'r') as f:
#         manifest_data = json.load(f)
    
#     # Convert the Python object back into a JSON string
#     raw_json_string = json.dumps(manifest_data, indent=4)
    
#     # --- THIS IS THE FIX ---
#     # Escape all curly braces for the LangChain template engine
#     ANALYSIS_MANIFEST_JSON = raw_json_string.replace("{", "{{").replace("}", "}}")
#     # --------------------
    
#     print(f"Successfully loaded and formatted the manifest.")

# except FileNotFoundError:
#     print(f"FATAL ERROR: The manifest file '{MANIFEST_FILENAME}' was not found.")
#     ANALYSIS_MANIFEST_JSON = "[]"
# except json.JSONDecodeError:
#     print(f"FATAL ERROR: The manifest file '{MANIFEST_FILENAME}' contains invalid JSON.")
#     ANALYSIS_MANIFEST_JSON = "[]"

# # --- End of Command ---
# # Use this variable in your test_groq.py or loop.py script
# prompt = f"""
# You are a data analysis robot. You follow a strict program. Your only purpose is to read a query from a file using your tools and then execute it.

# --- CORE MANDATE ---
# When a user asks to run a named analysis, your entire thought process MUST follow the procedure below. You are forbidden from deviating or using shortcuts.

# --- TOOL MANIFEST ---
# You have the following tools. You MUST choose the correct one based on the procedure.
# 1.  `read_sql_query_file(file_name: str)`: **Information Tool.** Use this to read the content of a specific .sql file. The filename comes from the manifest.
# 2.  `run_select_query(query: str)`: **Execution Tool.** Use this ONLY to run the final SQL query you read from a file.
# 3.  `list_user_defined_functions()`: **Validation Tool.** Use this ONLY to verify if a required UDF is active.
# *Other tools like `list_databases` & `list_tables` are for simple exploration only.*

# --- ANALYSIS MANIFEST ---
# This is your internal knowledge base.

# {ANALYSIS_MANIFEST_JSON}

# --- REQUIRED PROCEDURE FOR ANY NAMED ANALYSIS ---

# 1.  **IDENTIFY AND MATCH:**
#     - My first thought is: "The user wants to run '[analysis name]'. I must find this in my ANALYSIS MANIFEST."
#     - I will find the JSON object where the `analysis_type` matches the user's request. From this object, I will identify the `udf_required` value and the `sql_template_path` value.

# 2.  **VALIDATE (if necessary):**
#     - My second thought is: "Does the manifest say a UDF is required for this analysis?"
#     - **IF `udf_required` is NOT `null`:** My next action MUST be to call `list_user_defined_functions()` to verify the UDF exists. If it does not exist, I will STOP and report the error.
#     - **IF `udf_required` is `null`:** I will proceed to the next step.

# 3.  **RETRIEVE THE COMMAND:**
#     - My third thought is: "Validation is complete. Now I must retrieve the SQL command from the file."
#     - My next action MUST be to call the `read_sql_query_file()` tool. I will use the `sql_template_path` value I found in the manifest as the `file_name` argument.

# 4.  **EXECUTE THE COMMAND:**
#     - My final thought is: "I have the final SQL query from the previous step."
#     - My final action MUST be to call the `run_select_query()` tool and pass it the `sql_query` that was returned by the `read_sql_query_file` tool.
# """

# agents/clickhouse.py

import json
import os
from langchain_openai import AzureChatOpenAI
from mcp_use import MCPAgent
from connectors.mcp_client import create_client_to_running_server_clickhouse
from langchain_core.messages import HumanMessage

# --- STEP 1: LOAD ALL EXTERNAL KNOWLEDGE (Remains the same) ---

MANIFEST_FILENAME = "analysis_manifest.json"
try:
    with open(MANIFEST_FILENAME, 'r') as f:
        manifest_data = json.load(f)
    raw_json_string = json.dumps(manifest_data, indent=4)
    # Double curly braces are needed here because this JSON is part of a larger f-string prompt template.
    ANALYSIS_MANIFEST_JSON = raw_json_string.replace("{", "{{").replace("}", "}}")
    print("Analyst manifest loaded successfully.")
except Exception as e:
    print(f"FATAL ERROR loading manifest: {e}")
    ANALYSIS_MANIFEST_JSON = "[]"

PROCEDURE_FILENAME = "dynamic_doc_prompt.txt" # Assuming this is the architect's procedure
try:
    with open(PROCEDURE_FILENAME, 'r') as f:
        ARCHITECT_PROCEDURE = f.read()
    print("Architect procedure loaded successfully.")
except Exception as e:
    print(f"FATAL ERROR loading architect procedure: {e}")
    ARCHITECT_PROCEDURE = "Error: Procedure file not found."

# --- STEP 2: UPDATE THE ANALYST'S PROCEDURE WITHIN THE SYSTEM PROMPT ---

prompt = f"""
You are a multi-talented ClickHouse data robot. You can act as either an Analyst to run queries for a user, or as an Architect to perform system maintenance. You MUST determine the user's intent and follow the correct procedure.

--- PROCEDURE 1: ACTING AS AN ANALYST ---
If the user asks you to RUN a named analysis (e.g., "run case complexity"), you MUST follow the procedure described in the "ANALYST SOP" section below.

--- PROCEDURE 2: ACTING AS AN ARCHITECT ---
If the user asks you to GENERATE, CREATE, POPULATE, or UPDATE the view documentation or catalog, you MUST follow the procedure described in the "ARCHITECT SOP" section below.

======================================================================
--- ANALYST SOP ---

--- TOOL MANIFEST ---
You have the following tools. You MUST choose the correct one based on the procedure.
1.  `read_sql_query_file(file_name: str)`: **Information Tool.** Use this to read the content of a specific .sql file. The filename comes from the manifest.
2.  `run_select_query(query: str)`: **Execution Tool.** Use this ONLY to run the final SQL query you read from a file.
3.  `list_user_defined_functions()`: **Validation Tool.** Use this ONLY to verify if a required UDF is active.

--- ANALYSIS MANIFEST ---
This is your internal knowledge base for analyses.

{ANALYSIS_MANIFEST_JSON}

--- REQUIRED PROCEDURE ---
1.  **IDENTIFY AND MATCH:** Find the JSON object in the manifest where the `analysis_type` matches the user's request. Identify the `sql_template_path` and a best-guess for the primary table being queried.
2.  **VALIDATE (if necessary):** If `udf_required` is NOT `null`, call `list_user_defined_functions()` to verify the UDF exists. If not, STOP and report the error.
3.  **RETRIEVE THE COMMAND:** Call `read_sql_query_file()` using the `sql_template_path` from the manifest.
4.  **EXECUTE THE COMMAND:** Call `run_select_query()` with the `sql_query` returned by the previous tool.
5.  **FORMAT THE OUTPUT:** After executing the query, summarize the results and present your entire response using the MANDATORY OUTPUT FORMAT below.

--- MANDATORY OUTPUT FORMAT (FOR ANALYST ROLE ONLY) ---
Your final response MUST strictly follow the markdown structure below. Do not add any conversational text or pleasantries before or after this structure.

```markdown
---
**Dataset:** `[The name of the primary table you queried]`
**Question:** `[The user's original input query]`
**Provided Answer:** `[A concise, natural language summary of the key findings from the query results.]`
--- """

# --- STEP 3: INITIALIZE THE AGENT ---


def create_clickhouse_llm():
    """
    Initializes and returns the LLM for the ClickHouse specialist agent.
    """
    # llm = ChatGroq(
    #     model_name="llama3-8b-8192",
    #     groq_api_key=os.getenv("GROQ_API_KEY") , 
    #     # Temperature 0 makes the output more deterministic and predictable
    #     temperature=0
    # )
    llm = AzureChatOpenAI(
        azure_deployment="gpt-4.1-mini",       # your deployed model name on Azure
        api_version="2023-06-01-preview",
        temperature=0.7, max_tokens=4000
    )
    # Note: If you need to bind tools, you can implement a bind_tools() method in the LLM class.
    # llm.bind_tools(tools)  # Uncomment if you have tools to bind.
    
    return llm

# We will add the full agent creation logic here later.


# Import our new connector function
from connectors.mcp_client import create_client_to_running_server_clickhouse

def create_clickhouse_agent():
    """
    Creates the complete ClickHouse specialist agent.
    
    This function will:
    1. Initialize the client to connect to the RUNNING server.
    2. Initialize the LLM for the agent.
    3. Create the MCPAgent instance that connects them.
    
    Returns:
        An instance of MCPAgent.
    """
    print("--- 🛠️ Building ClickHouse Agent ---")
    
    # 1. Get the client that connects to your running server
    client = create_client_to_running_server_clickhouse()
    
    # 2. Get the LLM for this agent
    llm = create_clickhouse_llm()
    # from oai import create_azure_llm

    # llm = create_azure_llm()
    # llm = AzureChatOpenAI(
    #     azure_deployment="gpt-4.1-mini",       # your deployed model name on Azure
    #     api_version="2023-06-01-preview",
    #     temperature=0.7, max_tokens=4000
    # )
    agent = MCPAgent(
        llm=llm,
        client=client,
        system_prompt=prompt,  # Use the SOP prompt we defined
        max_steps=40,
        memory_enabled=False
    )
    # 3. Create the agent instance
    # agent = MCPAgent(
    #     llm=llm,
    #     client=client,
    #     max_steps=15,
    #     memory_enabled=False # We will manage memory in the main graph state
    # )
    
    print("--- ✅ ClickHouse Agent is built and ready. ---")
    return agent


# This function can be used in your main graph or tests to create the agent.


# now implementing the clcikhouse node forthe langchain graph

async def clickhouse_node(state: dict):
    """
    Executes the ClickHouse agent on the user's query.

    Args:
        state (dict): The current state of the graph.

    Returns:
        dict: A dictionary containing the agent's response to be added to the message history.
    """

    print("--- 📊 CLICKHOUSE NODE: Executing query... ---")

    print("--- 📊 CLICKHOUSE ANALYST: Taking over... ---")
    
    # 1. Create the specialist agent instance
    agent = create_clickhouse_agent()

    # 2. Get the user's query from the state
    user_query = state['messages'][-1].content

    try:
        response = await agent.run(user_query)
    except Exception as e:
        response = f"An error occurred while running the ClickHouse agent: {e}"
    
    # Always close the client sessions after the node is done.
    # This is crucial for connecting to an existing server.
    await agent.client.close_all_sessions()
    
    print(f"--- ✅ ClickHouse agent finished with response: {response} ---")

    # 4. Return the response in the correct format to update the state
    return {"messages": [HumanMessage(content=response)]}