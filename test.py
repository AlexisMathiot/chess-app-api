import asyncio
import websockets

async def test():
    uri = "ws://localhost:8000/ws/analyze"
    async with websockets.connect(uri) as websocket:
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"
        await websocket.send(fen)
        while True:
            response = await websocket.recv()
            print(response)

asyncio.run(test())
