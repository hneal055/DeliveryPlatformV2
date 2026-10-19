# Telemetry PoC - README

This directory contains the PoC components added on branch `integration/telemetry-poc` to demonstrate a simple telemetry ingestion → Redis Streams → bridge → websocket → frontend flow.

How it works
- POST /telemetry (FastAPI): accepts a TelemetryEvent JSON payload and writes it to a Redis Stream (telemetry:stream).
- telemetry_bridge (worker): reads from the stream as part of a consumer group and republishes each event to Redis Pub/Sub channel telemetry:pub.
- Websocket layer (existing app): should subscribe to telemetry:pub and forward messages to connected websocket clients. For the PoC, the frontend component connects to /ws/telemetry by default; you may need to wire your websocket server to listen to telemetry:pub and broadcast messages.

Quick dev steps
1. Start Redis locally (docker):

   docker run -p 6379:6379 redis:7

2. Start the FastAPI backend (from repo root, adjust paths if needed):

   export REDIS_URL=redis://localhost:6379
   export POC_TELEMETRY_API_KEY=telemetry-poc-secret
   uvicorn src.backend.main:app --reload

3. Run the bridge worker (in a separate terminal):

   python src/backend/workers/telemetry_bridge.py

4. Start the frontend dev server and open the Telemetry viewer route where you register the component.

Test with curl

curl -X POST "http://localhost:8000/telemetry" -H "Content-Type: application/json" -H "x-api-key: telemetry-poc-secret" -d '{"vehicle_id":"veh-1","ts":"2026-10-19T12:00:00Z","lat":37.7749,"lon":-122.4194,"status":"enroute"}'

Notes
- The PoC uses a simple API key for auth. For production, integrate with your OIDC/service accounts.
- The FastAPI websocket layer is not modified by this PoC; you'll need to connect your websocket broadcaster to Redis Pub/Sub (telemetry:pub) so browser clients receive the messages. If your existing websocket handlers already read from Redis, the bridge will integrate with them.
