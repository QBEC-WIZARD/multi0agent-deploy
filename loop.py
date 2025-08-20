import asyncio
from agents.clickhouse import create_clickhouse_agent

async def interactive_clickhouse_agent():
    """
    Continuously accepts user input and queries the ClickHouse agent.
    """
    agent = create_clickhouse_agent()
    print("--- 🟢 ClickHouse Agent Interactive Mode ---")
    print("Type 'exit' to quit.")
    while True:
        user_query = input("\nAsk ClickHouse: ")
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
    asyncio.run(interactive_clickhouse_agent())


#----------------------------------------------------------------------------------------------------------------------------------------

