import duckdb

con = duckdb.connect()
con.execute("INSTALL httpfs")
con.execute("LOAD httpfs")
con.execute("SET s3_endpoint = 'localhost:9000'")
con.execute("SET s3_access_key_id = 'minioadmin'")
con.execute("SET s3_secret_access_key = 'minioadmin'")
con.execute("SET s3_use_ssl = false")
con.execute("SET s3_url_style = 'path'")

result = con.execute("""
    SELECT item, world, pricePerUnit, quantity, hq, retainerName 
    FROM parquet_scan('s3://eorzea-lake/raw/market_listings/*/*/*.parquet') 
    LIMIT 20
""")
print(result.fetchdf())

