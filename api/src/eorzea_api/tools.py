import logging
import httpx
from bs4 import BeautifulSoup
from langchain_core.tools import tool
from eorzea_api.database import DuckDBConnect
from eorzea_api.models.tool_models import (
    ItemSearchInput,
    MarketSnapshotInput,
    DatacenterInput,
    LivePriceInput,
    ItemDetailsInput,
    MarketListing,
    RecentSale,
    LivePriceResult,
    ItemDetail,
    NewsItem,
    LodestoneNews,
)

logger = logging.getLogger(__name__)

# FFXIV DC to World Mappings
DATA_CENTERS = {
    "Aether": ["Adamantoise", "Cactuar", "Faerie", "Gilgamesh", "Jenova", "Midgardsormr", "Sargatanas", "Siren"],
    "Primal": ["Behemoth", "Excalibur", "Exodus", "Famfrit", "Hyperion", "Lamia", "Leviathan", "Ultros"],
    "Crystal": ["Balmung", "Brynhildr", "Coeurl", "Diabolos", "Goblin", "Malboro", "Mateus", "Zalera"],
    "Dynamis": ["Halicarnassus", "Maduin", "Marilith", "Seraph"],
    "Light": ["Alpha", "Lich", "Odin", "Phoenix", "Raiden", "Shiva", "Twintania", "Zodiark"],
    "Chaos": ["Cerberus", "Louisoix", "Moogle", "Omega", "Phantom", "Ragnarok", "Sagittarius", "Spriggan"],
    "Elemental": ["Aegis", "Atomos", "Carbuncle", "Garuda", "Gungnir", "Kujata", "Tonberry", "Typhon"],
    "Gaia": ["Alexander", "Bahamut", "Durandal", "Fenrir", "Ifrit", "Ridill", "Tiamat", "Ultima"],
    "Mana": ["Anima", "Asura", "Chocobo", "Hades", "Ixion", "Masamune", "Pandaemonium", "Titan"],
    "Meteor": ["Belias", "Mandragora", "Ramuh", "Shinryu", "Unicorn", "Valefor", "Yojimbo", "Zeromus"],
    "Materia": ["Bismarck", "Ravana", "Sephirot", "Sophia", "Zurvan"],
}

UNIVERSALIS_BASE = "https://universalis.app/api/v2"
XIVAPI_BASE = "https://xivapi.com/api/1"
LODESTONE_NEWS = "https://na.finalfantasyxiv.com/lodestone/news/"


def create_tools(db_path: str) -> list:
    ## Some of the tools require info from the DuckDB so we need to pass it through to hold a connection

    # ---- Local DB Tools ----

    @tool(args_schema=ItemSearchInput)
    def search_items(query: str) -> str:
        """Search for FFXIV item names matching a keyword. Use this when you need
        to find the exact item name before writing a SQL query. Returns up to 10 matches."""
        with DuckDBConnect(db_path) as db:
            df = db.execute(f"""
                SELECT item_id, item_name
                FROM item_names
                WHERE item_name ILIKE '%{query}%'
                LIMIT 10
            """).fetchdf()
        if df.empty:
            return f"No items found matching '{query}'."
        return df.to_string(index=False)

    @tool(args_schema=MarketSnapshotInput)
    def get_market_snapshot(item_name: str) -> str:
        """Get a quick price snapshot for an item across all worlds.

        Use this when you need current price context before answering
        a question about whether something is cheap or expensive."""
        with DuckDBConnect(db_path) as db:
            df = db.execute(f"""
                SELECT item_name, world_name, is_hq,
                       listing_count, ROUND(avg_price) as avg_price,
                       min_price, max_price
                FROM mart_price_summary
                WHERE item_name ILIKE '%{item_name}%'
                ORDER BY listing_count DESC
                LIMIT 10
            """).fetchdf()
        if df.empty:
            return f"No market data found for '{item_name}'."
        return df.to_string(index=False)

    # ---- Game Knowledge Tools ----

    @tool(args_schema=DatacenterInput)
    def get_worlds_in_datacenter(datacenter: str) -> str:
        """Look up which worlds (servers) belong to an FFXIV data center.

        Use this when a user asks about a data center like Aether, Primal, Crystal, etc.
        so you can filter queries to the right set of worlds."""
        for dc, worlds in DATA_CENTERS.items():
            if dc.lower() == datacenter.lower():
                return f"{dc}: {', '.join(worlds)}"
        available = ", ".join(DATA_CENTERS.keys())
        return f"Unknown data center '{datacenter}'. Available: {available}"

    # ---- External API Tools ----

    @tool(args_schema=LivePriceInput)
    def get_live_prices(item_name: str, world: str) -> str:
        """Fetch LIVE current prices from the Universalis API for an item on a specific world.

        Use this when the user wants real-time prices, not historical data from the local database.
        You must search_items first to get the item_id, then call this with the exact item name."""
        with DuckDBConnect(db_path) as db:
            df = db.execute(f"""
                SELECT item_id, item_name
                FROM item_names
                WHERE item_name ILIKE '%{item_name}%'
                LIMIT 1
            """).fetchdf()
        if df.empty:
            return f"Could not find item '{item_name}' to look up live prices."

        item_id = int(df.iloc[0]["item_id"])
        resolved_name = df.iloc[0]["item_name"]

        try:
            resp = httpx.get(
                f"{UNIVERSALIS_BASE}/{world}/{item_id}",
                params={"listings": 5, "entries": 5},
                timeout=10.0,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.error("Universalis API error: %s", e)
            return f"Failed to fetch live prices: {e}"

        listings = [
            MarketListing(
                quality="HQ" if listing.get("hq") else "NQ",
                quantity=listing.get("quantity", 0),
                price_per_unit=listing.get("pricePerUnit", 0),
                total=listing.get("total", 0),
            )
            for listing in data.get("listings", [])[:5]
        ]

        recent_sales = [
            RecentSale(
                quality="HQ" if s.get("hq") else "NQ",
                quantity=s.get("quantity", 0),
                price_per_unit=s.get("pricePerUnit", 0),
            )
            for s in data.get("recentHistory", [])[:3]
        ]

        result = LivePriceResult(
            item_name=resolved_name,
            world=world,
            listings=listings,
            recent_sales=recent_sales,
        )
        return str(result)

    @tool(args_schema=ItemDetailsInput)
    def get_item_details(item_name: str) -> str:
        """Look up detailed info about an FFXIV item from XIVAPI — its category,
        item level, whether it's craftable, what class uses it, etc.

        Use this when the user asks what an item is, what it's used for,
        or whether they should buy HQ vs NQ."""
        with DuckDBConnect(db_path) as db:
            df = db.execute(f"""
                SELECT item_id, item_name
                FROM item_names
                WHERE item_name ILIKE '%{item_name}%'
                LIMIT 1
            """).fetchdf()
        if df.empty:
            return f"Could not find item '{item_name}'."

        item_id = int(df.iloc[0]["item_id"])
        resolved_name = df.iloc[0]["item_name"]

        try:
            resp = httpx.get(
                f"{XIVAPI_BASE}/item/{item_id}",
                timeout=10.0,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.error("XIVAPI error: %s", e)
            return f"Failed to fetch item details: {e}"

        fields = data.get("fields", data)
        category = fields.get("ItemUICategory", {})
        category_name = category.get("Name", "Unknown") if isinstance(category, dict) else str(category)

        detail = ItemDetail(
            item_name=resolved_name,
            item_id=item_id,
            category=category_name,
            item_level=str(fields.get("LevelItem", "?")),
            equip_level=str(fields.get("LevelEquip", "?")),
            can_be_hq=bool(fields.get("CanBeHq", False)),
            description=fields.get("Description", "No description available."),
        )
        return str(detail)

    # ---- Web Scraping Tools ----

    @tool
    def get_lodestone_news() -> str:
        """Fetch the latest news headlines from the FFXIV Lodestone.

        Use this when the user asks about recent patches, maintenance,
        game updates, or events."""
        try:
            resp = httpx.get(
                LODESTONE_NEWS,
                timeout=10.0,
                headers={"User-Agent": "EorzeaMarketBot/1.0"},
            )
            resp.raise_for_status()
        except Exception as e:
            logger.error("Lodestone fetch error: %s", e)
            return f"Failed to fetch Lodestone news: {e}"

        soup = BeautifulSoup(resp.text, "html.parser")

        news_items = soup.select("li.news__list--link")
        if not news_items:
            news_items = soup.select(".news__list li")

        if not news_items:
            return "Could not parse Lodestone news page. The page structure may have changed."

        items = []
        for item in news_items[:8]:
            title_el = item.select_one(".news__list--title") or item.select_one("p")
            date_el = item.select_one("time") or item.select_one(".news__list--time")

            items.append(NewsItem(
                title=title_el.get_text(strip=True) if title_el else "Unknown",
                date=date_el.get_text(strip=True) if date_el else "",
            ))

        return str(LodestoneNews(items=items))

    return [
        search_items,
        get_worlds_in_datacenter,
        get_market_snapshot,
        get_live_prices,
        get_item_details,
        get_lodestone_news,
    ]
