import csv
import urllib.request
import io

url = "https://raw.githubusercontent.com/xivapi/ffxiv-datamining/master/csv/en/Item.csv"
print("Downloading item data...")
response = urllib.request.urlopen(url)
data = response.read().decode("utf-8")

reader = csv.reader(io.StringIO(data))
header = next(reader)

# Find column indices
id_idx = header.index("#")
name_idx = header.index("Name")

with open("eorzea_analytics/seeds/item_names.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["item_id", "item_name"])
    count = 0
    for row in reader:
        item_id = row[id_idx]
        item_name = row[name_idx].strip()
        if item_id and item_name and item_id != "0":
            writer.writerow([item_id, item_name])
            count += 1

print(f"Wrote {count} items to eorzea_analytics/seeds/item_names.csv")
