"""
REFERENCE FILE — FastAPI app with market analytics endpoints + LLM chat.
This is not used by the app. It's a reference for building main.py.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from eorzea_api.chat import MarketChatAgent
from eorzea_api.database import DuckDBConnect

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)

DB_PATH = "../dbt/eorzea_analytics/eorzea.duckdb"
agent: MarketChatAgent | None = None


# lifespan runs once on startup / shutdown
# creates the chat agent (loads schemas, initializes Claude)
@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent
    agent = MarketChatAgent(DB_PATH)
    yield


app = FastAPI(
    title="Eorzea Market Analytics API",
    description="FFXIV Market Board analytics powered by dbt, DuckDB, and Claude",
    lifespan=lifespan,
)


# --- Request / Response models ---

class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    question: str
    sql: str
    rows: int = 0
    answer: str
    error: str | None = None
    data: list[dict] = []


# --- Routes ---

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """Natural language question → SQL → answer."""
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    result = agent.ask(req.question)
    return ChatResponse(**result)


@app.get("/arbitrage")
def get_arbitrage(min_margin: float = 50, limit: int = 20):
    """Top cross-world arbitrage opportunities."""
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


@app.get("/prices/{item_name}")
def get_prices(item_name: str):
    """Price summary for an item across all worlds."""
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


@app.get("/velocity")
def get_velocity(limit: int = 20):
    """Fastest selling items by sale count."""
    with DuckDBConnect(DB_PATH) as db:
        df = db.execute(f"""
            SELECT item_name, world_name, sale_date, sale_count,
                   total_volume, ROUND(avg_price, 0) AS avg_price
            FROM mart_market_velocity
            ORDER BY sale_count DESC
            LIMIT {limit}
        """).fetchdf()
        return df.to_dict(orient="records")
