import httpx
import time
from typing import List


def get_dc(region: str = 'North-America') -> List[List[int]]:
    r = httpx.get('https://universalis.app/api/v2/data-centers')
    r.raise_for_status()
    payload = r.json()
    world_list = [dc['worlds'] for dc in payload if dc['region'] == region]
    return world_list


def get_worlds(world_ids: List[int]) -> List[str]:
    r = httpx.get('https://universalis.app/api/v2/worlds')
    r.raise_for_status()
    payload = r.json()
    world_list = [w['name'] for w in payload if w['id'] in world_ids]
    return world_list


def get_market_data(world: str, item_ids: List[int]) -> dict | None:
    r = httpx.get(f'https://universalis.app/api/v2/{world}/{','.join(str(i) for i in item_ids)}')
    r.raise_for_status()
    data = r.json()
    return data


if __name__ == "__main__":
    dc_worlds = get_dc()
    all_world_ids = [world_id for dc in dc_worlds for world_id in dc]
    world_names = get_worlds(all_world_ids)
    print(f"Tracking {len(world_names)} worlds: {world_names}")
    TRACKED_ITEMS = [
        5057, 5058, 4551, 12609, 36113, 19872, 27757, 33919, 39728, 10155,
        7058, 8149, 15649, 21800, 29991, 44180, 37284, 13703, 25199, 16543,
        9354, 31521, 42006, 11401, 22547, 48722, 3017, 46812, 28450, 7893
    ]

    for world in world_names:
        data = get_market_data(world, TRACKED_ITEMS)
        if data:
            for item_id, item_data in data['items'].items():
                if item_data.get('hasData'):
                    print(f"{data['worldName']} - Item {item_id}")
                    print(f"  Listings: {item_data['listingsCount']}")
                    print(f"  Avg price: {item_data['averagePrice']}")
                    print(f"  Sale velocity: {item_data['regularSaleVelocity']}")
            time.sleep(1)