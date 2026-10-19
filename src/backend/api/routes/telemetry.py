import os
import json
from fastapi import APIRouter, Header, HTTPException
from ..schemas.telemetry import TelemetryEvent

try:
    import redis.asyncio as redis
except Exception:
    # If redis.asyncio is not available, the route will still be installable but will raise at runtime.
    redis = None

router = APIRouter()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
POC_API_KEY = os.getenv("POC_TELEMETRY_API_KEY", "telemetry-poc-secret")
STREAM_KEY = "telemetry:stream"

# Initialize redis client lazily to avoid import-time side effects in tests
_redis_client = None

def get_redis():
    global _redis_client
    if _redis_client is None:
        if redis is None:
            raise RuntimeError("redis.asyncio is required to use the telemetry endpoint")
        _redis_client = redis.from_url(REDIS_URL)
    return _redis_client


@router.post("/telemetry")
async def ingest_telemetry(event: TelemetryEvent, x_api_key: str = Header(None)):
    """
    Ingest a telemetry event and push it to the Redis Stream for downstream consumers.

    For the PoC this endpoint uses a simple API key header (x-api-key) to allow service-to-service calls.
    """
    if x_api_key != POC_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    payload = event.dict()
    # ensure timestamp is serializable
    payload["ts"] = payload["ts"].isoformat()

    client = get_redis()
    try:
        # xadd expects a dict of strings/bytes
        await client.xadd(STREAM_KEY, {"data": json.dumps(payload)}, id="*")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"failed to push to stream: {e}")

    return {"status": "ok", "stream": STREAM_KEY}
