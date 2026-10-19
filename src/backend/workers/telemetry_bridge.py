import os
import asyncio
import json

try:
    import redis.asyncio as redis
except Exception:
    redis = None

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
STREAM_KEY = "telemetry:stream"
GROUP = "telemetry-poc-group"
CONSUMER = os.getenv("TELEMETRY_BRIDGE_CONSUMER", "bridge-1")
PUB_CHANNEL = "telemetry:pub"

# Simple bridge: read from Redis Stream (consumer group) and publish JSON payloads to a Redis pub/sub
# channel that existing websocket handlers can subscribe to (or the frontend can connect to if your
# websocket infrastructure supports proxying Redis pubsub → websocket).

async def ensure_group(client: "redis.Redis"):
    try:
        # Create consumer group; if stream doesn't exist, mkstream=True will create it
        await client.xgroup_create(STREAM_KEY, GROUP, id="$", mkstream=True)
    except Exception:
        # group likely exists
        pass


async def run_forever():
    if redis is None:
        raise RuntimeError("redis.asyncio is required to run the telemetry bridge")

    client = redis.from_url(REDIS_URL)
    await ensure_group(client)

    while True:
        try:
            # XREADGROUP blocking read
            res = await client.xreadgroup(GROUP, CONSUMER, {STREAM_KEY: ">"}, count=10, block=5000)
            if not res:
                await asyncio.sleep(0.1)
                continue

            for stream_name, messages in res:
                for msg_id, msg in messages:
                    try:
                        raw = msg.get(b"data") if isinstance(msg, dict) else msg.get("data")
                        if raw is None:
                            await client.xack(STREAM_KEY, GROUP, msg_id)
                            continue
                        if isinstance(raw, bytes):
                            raw = raw.decode()
                        data = json.loads(raw)
                        # publish to pubsub channel for websocket bridge
                        await client.publish(PUB_CHANNEL, json.dumps(data))
                        # acknowledge
                        await client.xack(STREAM_KEY, GROUP, msg_id)
                    except Exception:
                        # on error, don't ack so message can be retried
                        raise
        except Exception:
            # On any connection/read error, wait and retry
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(run_forever())
