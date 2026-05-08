client_test.py


import asyncio
import websockets

async def test():
    async with websockets.connect("ws://localhost:8765") as ws:
        while True:
            data = await ws.recv()
            print("Received from server:", data[:50])

asyncio.run(test())