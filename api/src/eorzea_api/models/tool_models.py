from pydantic import BaseModel, Field


# ---- Tool Input Schemas ----

class ItemSearchInput(BaseModel):
    query: str = Field(description="Keyword to search for in item names, e.g. 'Iron Ore' or 'Bow'")


class MarketSnapshotInput(BaseModel):
    item_name: str = Field(description="The FFXIV item name to look up prices for")


class DatacenterInput(BaseModel):
    datacenter: str = Field(description="FFXIV data center name, e.g. Aether, Primal, Crystal")


class LivePriceInput(BaseModel):
    item_name: str = Field(description="The FFXIV item name to look up")
    world: str = Field(description="The world/server name, e.g. Jenova, Gilgamesh, Cactuar")


class ItemDetailsInput(BaseModel):
    item_name: str = Field(description="The FFXIV item name to get details for")


# ---- Data Models (for structuring API responses) ----

class MarketListing(BaseModel):
    quality: str
    quantity: int
    price_per_unit: int
    total: int

    def __str__(self):
        return f"{self.quality} x{self.quantity} @ {self.price_per_unit:,} gil (total: {self.total:,} gil)"


class RecentSale(BaseModel):
    quality: str
    quantity: int
    price_per_unit: int

    def __str__(self):
        return f"{self.quality} x{self.quantity} sold @ {self.price_per_unit:,} gil"


class LivePriceResult(BaseModel):
    item_name: str
    world: str
    listings: list[MarketListing] = []
    recent_sales: list[RecentSale] = []

    def __str__(self):
        if not self.listings:
            return f"No current listings for {self.item_name} on {self.world}."
        lines = [f"Live listings for {self.item_name} on {self.world}:"]
        for listing in self.listings:
            lines.append(f"  {listing}")
        if self.recent_sales:
            lines.append("Recent sales:")
            for sale in self.recent_sales:
                lines.append(f"  {sale}")
        return "\n".join(lines)


class ItemDetail(BaseModel):
    item_name: str
    item_id: int
    category: str = "Unknown"
    item_level: str = "?"
    equip_level: str = "?"
    can_be_hq: bool = False
    description: str = "No description available."

    def __str__(self):
        desc = self.description[:300] + "..." if len(self.description) > 300 else self.description
        return "\n".join([
            f"{self.item_name} (ID: {self.item_id})",
            f"  Category: {self.category}",
            f"  Item Level: {self.item_level}",
            f"  Equip Level: {self.equip_level}",
            f"  Can be HQ: {'Yes' if self.can_be_hq else 'No'}",
            f"  Description: {desc}",
        ])


class NewsItem(BaseModel):
    title: str
    date: str = ""

    def __str__(self):
        line = f"- {self.title}"
        if self.date:
            line += f" ({self.date})"
        return line


class LodestoneNews(BaseModel):
    items: list[NewsItem] = []

    def __str__(self):
        if not self.items:
            return "No news found."
        lines = ["Latest FFXIV Lodestone News:"]
        for item in self.items:
            lines.append(f"  {item}")
        return "\n".join(lines)
