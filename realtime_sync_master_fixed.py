import asyncio
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

# Initialize FastAPI app
app = FastAPI()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}

@app.websocket("/sync")
async def sync_clock(websocket: WebSocket):
    await websocket.accept()
    tick = 0
    try:
        while True:
            tick += 1
            message = {"tick": tick, "timestamp": time.time()}
            await websocket.send_json(message)
            await asyncio.sleep(0.033)  # 30 Hz
    except WebSocketDisconnect:
        # Client disconnected, end loop
        pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9201)

