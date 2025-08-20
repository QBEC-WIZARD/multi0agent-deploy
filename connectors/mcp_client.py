from mcp_use import MCPClient
import os

def create_client_to_running_server_clickhouse():
    running_server_url = "http://127.0.0.1:8000/sse/"

    # Build the config dict: use "url" for HTTP-based (SSE) servers
    config = {
        "mcpServers": {
            "clickhouse_server": {
                "url": running_server_url
            }
        }
    }

    # Create the MCPClient from the config dict
    client = MCPClient.from_dict(config)
    return client


# def create_and_launch_supabase_client():
#     """
#     Creates a client that will AUTOMATICALLY LAUNCH the Supabase MCP server.
#     The server configuration is defined directly in this function.
#     """
#     print("--- ⚙️ Defining configuration to LAUNCH Supabase MCP server... ---")
    
#     # 1. Get the PAT from the environment
#     token = os.getenv("SUPABASE_ACCESS_TOKEN")
#     if not token:
#         raise ValueError("SUPABASE_ACCESS_TOKEN not found in .env file.")

#     # 2. Define the server configuration as a Python dictionary
#     config = {
#         "mcpServers": {
#             "supabase_server": { # Logical name for the Supabase server
#                 "command": "npx",
#                 "args": [
#                     "-y", "@supabase/mcp-server-supabase@latest",
#                     "--read-only",
#                     "--port=8001", # Use a different port to avoid conflict with ClickHouse!
#                     "--project-ref=jvgufroqfhtgnfgjijop"
#                 ],
#                 "env": {
#                     "SUPABASE_ACCESS_TOKEN": token
#                 }
#             }
#         }
#     }

#     # 3. Create the client from the dictionary
#     client = MCPClient.from_dict(config)
#     print("--- ✅ Supabase client is configured and ready to launch the server on demand. ---")
#     return client


def create_and_launch_supabase_client():
    """Connects to the running Supabase MCP server on the default port 8000."""
    running_server_url = "http://127.0.0.1:8000/"
    print("--- 🔌 Connecting to existing Supabase MCP server at 127.0.0.1:8000 ---")
    
    config = { "mcpServers": { "supabase_server": { "url": running_server_url } } }
    client = MCPClient.from_dict(config)
    return client


from langchain_community.utilities.sql_database import SQLDatabase

def create_supabase_connection():
    """Creates the direct database connection object."""
    db_uri = os.getenv("SUPABASE_CONNECTION_STRING")
    if not db_uri:
        raise ValueError("SUPABASE_CONNECTION_STRING not found in .env file.")
    
    # This will now use the correct, URL-encoded connection string
    db = SQLDatabase.from_uri(db_uri)
    print("--- ✅ Direct connection to Supabase DB configured. ---")
    return db