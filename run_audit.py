# run_audit.py

import os
import requests
from supabase import create_client, Client
from dotenv import load_dotenv
import json

# --- CONFIGURATION ---
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
AGENT_API_ENDPOINT = os.getenv("AGENT_API_ENDPOINT")

# --- DATABASE CLIENT INITIALIZATION ---
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Successfully connected to Supabase.")
except Exception as e:
    print(f"❌ ERROR: Could not connect to Supabase. Check your .env file. Error: {e}")
    exit()


def fetch_approved_questions():
    """Fetches all questions with 'Approved' status from the questionnaire table."""
    try:
        print("\nFetching approved questions from Supabase...")
        response = supabase.table("t_auditor_questionaire").select("id, question").eq("status", "Approved").execute()
        
        if response.data:
            print(f"  > Found {len(response.data)} approved questions.")
            return response.data
        else:
            print("  > No approved questions found.")
            return []
    except Exception as e:
        print(f"❌ ERROR: Failed to fetch questions from Supabase. Error: {e}")
        return []

def call_agent_api(question: str):
    """Sends a single question to the agent's API endpoint and returns the JSON response."""
    if not AGENT_API_ENDPOINT:
        print("❌ ERROR: AGENT_API_ENDPOINT is not set in the .env file.")
        return None
        
    print(f"  > Calling agent with question: '{question[:50]}...'")
    try:
        # The 'q' parameter must match what your FastAPI endpoint expects
        params = {"q": question}
        response = requests.get(AGENT_API_ENDPOINT, params=params, timeout=300) # 5-minute timeout for complex queries
        
        response.raise_for_status()  # This will raise an exception for 4xx or 5xx status codes
        
        print(f"  > Agent responded successfully.")
        return response.json() # Returns the response content as a Python dictionary
        
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: Failed to call the agent API. Error: {e}")
        return None

def store_answer(question_id: int, question_text: str, answer_json: dict):
    """Stores the agent's JSON response in the answers table."""
    try:
        print(f"  > Storing answer for question ID: {question_id}...")
        
        # We create a new record in the answers table
        data_to_insert = {
            "question_id": question_id,
            "question": question_text,
            "answer": answer_json, # The 'answer' column is of type JSONB
            "status": "Approved" # Or you could set a 'Completed' status
        }
        
        response = supabase.table("t_auditor_ques_answers").insert(data_to_insert).execute()
        
        if len(response.data) > 0:
            print("  > Successfully stored the answer in Supabase.")
        else:
            print("  > FAILED to store the answer. Response from Supabase was empty.")
            # You might want to inspect response.error here if it exists

    except Exception as e:
        print(f"❌ ERROR: Could not store answer in Supabase. Error: {e}")


def main():
    """Main orchestration function."""
    print("\n--- 🚀 Starting Automated Auditor Run ---")
    
    questions_to_process = fetch_approved_questions()
    
    if not questions_to_process:
        print("\n--- 🏁 No questions to process. Exiting. ---")
        return

    for item in questions_to_process:
        question_id = item.get("id")
        question_text = item.get("question")
        
        if not question_id or not question_text:
            print("  > Skipping malformed question item from database.")
            continue
            
        print(f"\nProcessing Question #{question_id}: '{question_text}'")
        
        # Call the agent API
        agent_response = call_agent_api(question_text)
        
        # Store the result if the API call was successful
        if agent_response:
            store_answer(question_id, question_text, agent_response)
            
    print("\n--- ✅ Automated Auditor Run Complete ---")


if __name__ == "__main__":
    # Ensure your FastAPI agent server is running before you execute this script.
    main()