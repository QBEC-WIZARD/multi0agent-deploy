from contextlib import asynccontextmanager
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
import uvicorn
# from agents.clickhouse import create_clickhouse_agent
from agents.clickhouse_auditor import create_clickhouse_audit_agent

from agents.auditor import create_auditor_agent

agent = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent
    # Startup
    agent = create_clickhouse_audit_agent()
    print("✅ ClickHouse Agent started")
    
    yield   # 👈 FastAPI will serve requests while paused here
    
    # Shutdown
    if hasattr(agent, "client"):
        await agent.client.close_all_sessions()
    print("❌ ClickHouse Agent stopped")

app = FastAPI(lifespan=lifespan)

@app.get("/ask")
async def ask_agent(q: str = Query(..., description="Your question for the ClickHouse agent")):
    try:
        result = await agent.run(q)
        # audit_agent = create_auditor_agent()
        # audit_result = await audit_agent.run(result)
        print(f"Audit Result: {result}")
        return JSONResponse(content={"answer":  result}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)




