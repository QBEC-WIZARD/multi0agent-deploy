import asyncio
from dotenv import load_dotenv
import os

# Import the LLM creation functions
from agents.orchestrator import create_orchestrator_llm
from agents.clickhouse import create_clickhouse_llm , create_clickhouse_agent
from agents.supabase import create_supabase_llm
from mcp_use import MCPAgent

# Import our new MCP client connector function
from connectors.mcp_client import create_client_to_running_server_clickhouse

def run_llm_tests():
    """
    Tests the three agent LLMs synchronously.
    """
    print("--- 🧠 Testing Orchestratfor LLM ---")
    orchestrator_llm = create_orchestrator_llm()
    response1 = orchestrator_llm.invoke("Identify the database type for a query about 'user profiles': 'supabase' or 'clickhouse'?")
    print(f"Response: {response1.content}")
    print("✅ Orchestrator LLM test PASSED.\n")

    print("--- 📊 Testing ClickHouse LLM ---")
    clickhouse_llm = create_clickhouse_llm()
    response2 = clickhouse_llm.invoke("Write a sample ClickHouse SQL query to count events.")
    print(f"Response: {response2.content}")
    print("✅ ClickHouse LLM test PASSED.\n")
    
    print("--- 👤 Testing Supabase LLM ---")
    supabase_llm = create_supabase_llm()
    response3 = supabase_llm.invoke("Write a sample PostgreSQL query to select a user by id.")
    print(f"Response: {response3.content}")
    print("✅ Supabase LLM test PASSED.\n")

async def run_mcp_client_test():
    """
    Asynchronously tests the connection to the running MCP server in WSL.
    """
    print("--- 🔌 Testing MCP Client Connection to WSL Server ---")
    
    client = None
    try:
        # 1. Create the client instance using our connector function
        # client = create_client_to_running_server()
        # print("Client created successfully. Now testing connection...\n")
        # llm  = create_clickhouse_llm()
        # # 3. Create the agent instance
        # agent = MCPAgent(
        # llm=llm,
        # client=client,
        # max_steps=15,
        # memory_enabled=False # We will manage memory in the main graph state
        # )
        agent = create_clickhouse_agent()
        result = await agent.run("I need to run the case complexity analysis on the default.mortgage_events table. Please follow the standard procedure by retrieving the documentation first to ensure you are using the correct SQL template.")
        print(result)
        print("ClickHouse agent created successfully. Now testing server connection...\n")


        # 2. Perform a test action: Get the list of tools from the server
        # This proves we can communicate with it.
        # 'clickhouse_server' is the logical name we gave the connection.
        # print("Calling 'list_databases' tool on server...")
        # result = await client.run(
        #     server="clickhouse_server",
        #     tool="list_databases",
        #     input={}  # Empty input if the tool doesn't require arguments
        # )
        # print("--- ✅ SUCCESS! Tool responded with: ---")
        # print(result)

        print("--- ✅ MCP CLIENT TEST PASSED ---")


        
    except Exception as e:
        print(f"\n--- ❌ MCP CLIENT TEST FAILED ---")
        print(f"An error occurred: {e}")
        print("\nPlease check the following:")
        print("1. Is your `fastmcp` server running in your WSL terminal?")
        print("2. Is it running on http://127.0.0.1:8000/sse/ ?")
        
    finally:
        # 3. Always clean up the client sessions
        if client:
            print("\nClosing client sessions...")
            await client.close_all_sessions()
            print("Client sessions closed.")


from connectors.mcp_client import create_supabase_connection

async def main_test_runner():
    """
    Main function to run all our tests in sequence.
    """
    print("--- Loading Environment Variables ---")
    load_dotenv()
    print("✅ .env file loaded.\n")
    db = create_supabase_connection()
    print("Supabase database connection created successfully.\n")
    # Run the synchronous LLM tests first
   # run_llm_tests()
    
    # Run the asynchronous MCP client test
    await run_mcp_client_test()



# Import BOTH client connector functions
from connectors.mcp_client import create_client_to_running_server_clickhouse
from connectors.mcp_client import create_and_launch_supabase_client

from agents.supabase import create_supabase_agent

async def run_supabase_launch_test():
    """
    Tests the ability to AUTOMATICALLY LAUNCH the Supabase MCP server.
    """
    print("--- 🚀 [Test 2] Testing AUTO-LAUNCH of Supabase Server ---")
    print("--> PRE-REQUISITE: Make sure no other server is running on port 8001.")
    client = None
    try:
        # 1. Create the client instance that knows how to launch the server
       # client = create_and_launch_supabase_client()
        agent = create_supabase_agent()
        print("--- ✅ Supabase MCP Agent created successfully. Now testing server launch...\n")
        result = await agent.run("What are the tools in our supabase?")
        print(result)
        
        # 2. Perform a test action. The client will LAUNCH the npx server
        #    the first time it needs to communicate with it.
        # print("Asking client for Supabase server tools (this will trigger launch)...")
        # tools = await client.get_tools('supabase_server')
        
        # print(f"--- ✅ SUCCESS! Supabase server launched and responded with tools: ---")
        # print(f"{tools}\n")
        
    except Exception as e:
        print(f"\n--- ❌ SUPABASE TEST FAILED --- \n{e}\n")
    finally:
        # 3. Important: The launched server is a subprocess.
        #    Closing all sessions will also terminate it.
        if client:
            print("Closing all client sessions (this will shut down the launched Supabase server)...")
            await client.close_all_sessions()
            print("Supabase server shut down.")

async def main_test_runner():
    """
    Main function to run all our tests in sequence.
    """
    print("--- Loading Environment Variables ---")
    load_dotenv()
    print("✅ .env file loaded.\n")
    
   # run_llm_tests()
   # await run_clickhouse_connection_test()
    await run_supabase_launch_test()

if __name__ == "__main__":
    asyncio.run(run_mcp_client_test())
    #asyncio.run(main_test_runner())
    # create_supabase_connection()
    #run_llm_tests()
