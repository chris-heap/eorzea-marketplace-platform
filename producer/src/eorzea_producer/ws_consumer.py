import asyncio
import bson
from websockets.asyncio.client import connect

"""
Connect to wss://universalis.app/api/ws
Subscribe to listings/add and sales/add
Print each incoming message
""" 

channel = "wss://universalis.app/api/ws"

async def initialize():
    async with connect(channel) as websocket:
        print(f"Connected to {channel}")
        await subscribe(websocket)
        print("Subscription request sent. Waiting for events...")

        async for message in websocket:
            data = bson.decode(message)
            print(f"Received: {data}")


async def subscribe(ws):
    await ws.send(bson.encode({"event": "subscribe", "channel": "listings/add"}))
    await ws.send(bson.encode({"event": "subscribe", "channel": "sales/add"}))

if __name__ == "__main__":
    asyncio.run(initialize())