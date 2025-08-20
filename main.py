from contextlib import asynccontextmanager
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
import uvicorn
from agents.clickhouse import create_clickhouse_agent

agent = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent
    # Startup
    agent = create_clickhouse_agent()
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
        return JSONResponse(content={"answer": result})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)




