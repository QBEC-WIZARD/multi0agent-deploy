# clickhouse_audit_loop.py

import asyncio
# Import the renamed function from your agent file
from agents.clickhouse_auditor import create_clickhouse_audit_agent

async def interactive_clickhouse_audit_agent():
    """
    Continuously accepts user input and queries the ClickHouse Auditor agent.
    """
    # 1. Create the new agent using the renamed function
    agent = create_clickhouse_audit_agent()
    
    # 2. Update the user-facing prompts
    print("\n--- 🛡️ ClickHouse Auditor Agent Interactive Mode ---")
    print("Type 'exit' to quit.")
    
    while True:
        user_query = input("\nAsk ClickHouse Auditor: ") # <-- Updated input prompt
        if user_query.strip().lower() in ["exit", "quit"]:
            print("Exiting interactive mode.")
            break
        try:
            result = await agent.run(user_query)
            print(f"\nAgent Response: {result}")
        except Exception as e:
            print(f"Error: {e}")
            
    # Always close client sessions after loop
    await agent.client.close_all_sessions()

if __name__ == "__main__":
    # 3. Update the main function call
    asyncio.run(interactive_clickhouse_audit_agent())