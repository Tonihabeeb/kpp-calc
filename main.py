import asyncio
import requests
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

# Initialize FastAPI app
app = FastAPI()

@app.websocket("/state")
async def state_stream(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # fetch the latest state from the backend
            resp = requests.get("http://localhost:9100/status")
            state = resp.json()
            await websocket.send_json(state)
            await asyncio.sleep(0.033)  # ~30 FPS
    except Exception:
        # If the client disconnects or error occurs, break out of loop
        await websocket.close()

@app.get("/")
async def root():
    """Root endpoint"""
    return {"status": "running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9101)

