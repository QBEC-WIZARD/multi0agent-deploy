# main.py

import os
import requests
from supabase import create_client, Client
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query, BackgroundTasks
from fastapi.responses import JSONResponse
import uvicorn
from agents.clickhouse_audit_agent import create_clickhouse_audit_agent

# --- CONFIGURATION (can be shared across the app) ---
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# This global agent will be used by the interactive '/ask' endpoint
interactive_agent = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup and shutdown of the interactive agent."""
    global interactive_agent
    interactive_agent = create_clickhouse_audit_agent()
    print("✅ Interactive ClickHouse Auditor Agent pre-loaded for /ask endpoint.")
    
    yield
    
    if hasattr(interactive_agent, "client"):
        await interactive_agent.client.close_all_sessions()
    print("❌ Interactive ClickHouse Auditor Agent shut down.")

app = FastAPI(lifespan=lifespan)

# --- ENDPOINT 1: INTERACTIVE QUESTION ASKING ---
@app.get("/ask")
async def ask_agent(q: str = Query(..., description="Your question for the ClickHouse auditor agent")):
    """Handles a single, interactive question to the agent."""
    global interactive_agent
    try:
        result = await interactive_agent.run(q)
        print(f"Audit Result for '{q}': {result}")
        return JSONResponse(content={"answer": result})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


# --- LOGIC FOR THE NEW BATCH AUDIT ENDPOINT (from your run_audit.py script) ---

def run_full_audit_process():
    """
    This function contains the complete logic from your run_audit.py script.
    It will be run in the background to avoid tying up the API response.
    """
    try:
        print("\n--- 🚀 Starting Automated Batch Auditor Run ---")
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Batch Audit: Successfully connected to Supabase.")
        
        # 1. Fetch Questions
        print("  > Batch Audit: Fetching approved questions...")
        fetch_response = supabase.table("t_auditor_questionaire").select("id, question").eq("status", "Approved").execute()
        
        if not fetch_response.data:
            print("--- 🏁 Batch Audit: No questions to process. Exiting. ---")
            return

        questions_to_process = fetch_response.data
        print(f"  > Batch Audit: Found {len(questions_to_process)} questions.")
        
        # Create a single agent instance to reuse for all API calls in this batch
        batch_agent = create_clickhouse_audit_agent()
        
        for item in questions_to_process:
            question_id = item.get("id")
            question_text = item.get("question")
            print(f"\n  > Batch Audit: Processing Question #{question_id}: '{question_text}'")

            try:
                # 2. Call the agent
                agent_response = asyncio.run(batch_agent.run(question_text))
                
                # 3. Store the answer
                if agent_response:
                    print(f"  > Batch Audit: Storing answer for question ID {question_id}...")
                    supabase.table("t_auditor_ques_answers").insert({
                        "question_id": question_id,
                        "question": question_text,
                        "answer": {"answer": agent_response}, # Store the agent's string response in a JSON object
                        "status": "Approved"
                    }).execute()
                    print(f"  > Batch Audit: Successfully stored answer for question ID {question_id}.")

            except Exception as e:
                print(f"❌ ERROR: Failed to process question ID {question_id}. Error: {e}")
                # Optional: You could update the status in Supabase to 'Failed' here
                continue # Move to the next question
        
        # Clean up the batch agent's session
        asyncio.run(batch_agent.client.close_all_sessions())
        print("\n--- ✅ Automated Batch Auditor Run Complete ---")

    except Exception as e:
        print(f"❌ FATAL ERROR during batch audit process: {e}")


# --- ENDPOINT 2: BATCH AUDIT TRIGGER ---
@app.post("/run_batch_audit")
def trigger_batch_audit(background_tasks: BackgroundTasks):
    """
    Triggers the full, automated audit process in the background.
    Fetches all approved questions from Supabase, runs them through the agent,
    and stores the answers back in Supabase.
    """
    print("✅ Received request to run batch audit. Starting process in the background...")
    background_tasks.add_task(run_full_audit_process)
    return JSONResponse(
        content={"message": "Accepted. The automated audit process has been started in the background. Check server logs for progress."},
        status_code=202
    )