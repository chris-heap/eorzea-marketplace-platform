import csv
import json
import urllib.request

print("Loading world data from worlds.json...")
with open("worlds.json", "r", encoding="utf-8") as f:
    worlds = json.load(f)

with open("eorzea_analytics/seeds/world_names.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["world_id", "world_name"])
    count = 0
    for w in worlds:
        if w["id"] < 3000:  # skip test servers
            writer.writerow([w["id"], w["name"]])
            count += 1

print(f"Wrote {count} worlds to eorzea_analytics/seeds/world_names.csv")
