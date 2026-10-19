from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import os
import json
import asyncio

try:
    import redis.asyncio as redis
except Exception:
    redis = None

router = APIRouter()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
PUB_CHANNEL = "telemetry:pub"


@router.websocket("/ws/telemetry")
async def websocket_telemetry(ws: WebSocket):
    """
    WebSocket endpoint that subscribes to the Redis Pub/Sub channel `telemetry:pub`
    and forwards incoming messages to the connected WebSocket client.

    This is a PoC implementation that creates a per-connection Redis pubsub subscription.
    For higher scale, consider using a single background subscriber and a WebSocket manager
    that fans out messages to all connected clients.
    """
    await ws.accept()

    if redis is None:
        await ws.send_json({"error": "redis.asyncio is required on the server to subscribe to telemetry:pub"})
        await ws.close()
        return

    client = redis.from_url(REDIS_URL)
    pubsub = client.pubsub()
    await pubsub.subscribe(PUB_CHANNEL)

    async def forward_pubsub_to_ws():
        try:
            async for message in pubsub.listen():
                # message example: {'type': 'message', 'pattern': None, 'channel': b'telemetry:pub', 'data': b'{...}'}
                if not message:
                    continue
                mtype = message.get("type")
                if mtype != "message":
                    continue
                data = message.get("data")
                if isinstance(data, bytes):
                    data = data.decode()
                # forward raw JSON text
                try:
                    await ws.send_text(data)
                except Exception:
                    # client probably disconnected
                    break
        finally:
            # ensure we try to unsubscribe when leaving
            try:
                await pubsub.unsubscribe(PUB_CHANNEL)
            except Exception:
                pass

    forward_task = asyncio.create_task(forward_pubsub_to_ws())

    try:
        # keep the websocket open and respond to client pings/messages
        while True:
            try:
                _ = await ws.receive_text()
                # We don't expect client messages in this PoC, but receiving keeps the connection alive
            except WebSocketDisconnect:
                break
            except Exception:
                # ignore and continue
                await asyncio.sleep(0.1)
                continue
    finally:
        forward_task.cancel()
        try:
            await pubsub.close()
        except Exception:
            pass
        try:
            await client.close()
        except Exception:
            pass
