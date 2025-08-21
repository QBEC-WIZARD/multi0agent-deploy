import asyncio
from agents.auditor import create_auditor_agent  # <-- IMPORT the new function name

async def interactive_auditor_agent():
    """
    Continuously accepts user input and queries the Auditor agent.
    """
    # 1. CREATE the new agent
    agent = create_auditor_agent()
    
    # 2. UPDATE the user-facing prompts
    print("\n--- 🛡️ Auditor Agent Interactive Mode ---")
    print("Type 'exit' to quit.")
    
    while True:
        user_query = input("\nAsk Auditor: ") # <-- UPDATE the input prompt
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
    # 3. UPDATE the main function call
    asyncio.run(interactive_auditor_agent())