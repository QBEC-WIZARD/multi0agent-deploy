import os
from langchain_groq import ChatGroq

from langchain_core.prompts import ChatPromptTemplate

def create_orchestrator_llm():
    """
    Initializes and returns the LLM for the main orchestrator agent.
    We use a powerful model and low temperature for reliable routing decisions.
    """
    llm = ChatGroq(
        # The most capable model for reasoning and routing logic
        model_name="llama3-70b-8192",
        groq_api_key=os.getenv("GROQ_API_KEY"),
        # Temperature 0 makes the output more deterministic and predictable
        temperature=0
    )
    return llm


# Define the orchestrator node creation function
def orchestrator_node(state: dict):
    """
    Analyzes the user's query and routes it to the correct specialist.

    Args:
        state (dict): The current state of the graph, containing the message history.

    Returns:
        dict: A dictionary with the key "next_node" indicating where to go next.
    """
    print("--- 🧠 ORCHESTRATOR: Analyzing query... ---")

    # 1. Get the LLM for the orchestrator using our existing function
    llm = create_orchestrator_llm()

    # 2. Define the routing prompt
    routing_prompt_template = """You are an expert routing agent. Your job is to analyze a user's query and decide which of the following specialist agents is best suited to handle it.
    You must respond with ONLY the name of the chosen agent and nothing else.

    Here are the available agents and their descriptions:

    1. supabase_analyst: This agent is an expert on the user database. Use this agent for any questions about users, user profiles, accounts, sign-ups, orders, or other transactional data.
    2. clickhouse_analyst: This agent is an expert on the analytics database. Use this agent for any questions about analytics, time-series data, event logs, performance metrics, or large-scale aggregations.

    User Query:
    {user_query}

    Chosen Agent:"""

    prompt = ChatPromptTemplate.from_template(routing_prompt_template)

    # 3. Create the chain and invoke it
    router_chain = prompt | llm

    # The user's query is the last message in the state
    user_query = state['messages'][-1].content

    # The LLM's response will be a string (e.g., "supabase_analyst")
    chosen_agent = router_chain.invoke({"user_query": user_query}).content

    # Clean up the response to ensure it's just the agent name
    chosen_agent = chosen_agent.strip().replace("`", "") # Also remove backticks if the LLM adds them

    print(f"--- ROUTING to: {chosen_agent} ---")

    # 4. Return the routing decision
    return {"next_node": chosen_agent}



