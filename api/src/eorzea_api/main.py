import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from eorzea_api.models.chat_models import ChatRequest, ChatResponse

from eorzea_api.chat import EorzeaMarketChatAgent
from eorzea_api.database import DuckDBConnect

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)

DB_PATH = "../dbt/eorzea_analytics/eorzea.duckdb"
agent: EorzeaMarketChatAgent | None = None


# lifespan runs once on startup / shutdown
# creates the chat agent (loads schemas, initializes Claude)
@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent
    agent = EorzeaMarketChatAgent(DB_PATH)
    yield


app = FastAPI(
    title="Eorzea Market Analytics API",
    description="FFXIV Market Board analytics powered by dbt, DuckDB, and Claude",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}

"""Chatbot to convert human language to SQL to query the data model"""
@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    result = agent.ask(req.question)
    return ChatResponse(**result)

"""Lists the top cross-world arbitrage opportunities"""
@app.get("/arbitrage")
def get_arbitrage(min_margin: float = 50, limit: int = 20):
    with DuckDBConnect(DB_PATH) as db:
        df = db.execute(f"""
            SELECT item_name, world_name, is_hq, min_price,
                   cheapest_price, priciest_price, profit_margin_pct
            FROM mart_cross_world_arbitrage
            WHERE profit_margin_pct >= {min_margin}
            ORDER BY profit_margin_pct DESC
            LIMIT {limit}
        """).fetchdf()
        return df.to_dict(orient="records")

"""Get price summary of an item across all worlds"""
@app.get("/prices/{item_name}")
def get_prices(item_name: str):
    with DuckDBConnect(DB_PATH) as db:
        df = db.execute(f"""
            SELECT item_name, world_name, is_hq, listing_count,
                   ROUND(avg_price, 0) AS avg_price, min_price, max_price
            FROM mart_price_summary
            WHERE item_name ILIKE '%{item_name}%'
            ORDER BY listing_count DESC
            LIMIT 20
        """).fetchdf()
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No listings found for '{item_name}'")
        return df.to_dict(orient="records")

"""Get the highest sales velocity items across all worlds"""
@app.get("/velocity")
def get_velocity(limit: int = 20):
    with DuckDBConnect(DB_PATH) as db:
        df = db.execute(f"""
            SELECT item_name, world_name, sale_date, sale_count,
                   total_volume, ROUND(avg_price, 0) AS avg_price
            FROM mart_market_velocity
            ORDER BY sale_count DESC
            LIMIT {limit}
        """).fetchdf()
        return df.to_dict(orient="records")
