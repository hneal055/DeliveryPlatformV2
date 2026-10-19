import React, { useEffect, useState } from "react";

interface TelemetryPoint {
  vehicle_id: string;
  ts: string;
  lat: number;
  lon: number;
  heading?: number;
  speed?: number;
  accuracy?: number;
  status?: string;
}

// Simple PoC UI: connect to a websocket endpoint (configurable) and list incoming telemetry points.
// This component intentionally avoids adding map dependencies so it can be integrated quickly.

const DEFAULT_WS = (window.location.protocol === "https:" ? "wss://" : "ws://") + (window.location.host || "localhost:8000") + "/ws/telemetry";
const WS_URL = (process.env.REACT_APP_TELEMETRY_WS_URL || DEFAULT_WS) as string;

export const TelemetryViewer: React.FC = () => {
  const [points, setPoints] = useState<TelemetryPoint[]>([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const ws = new WebSocket(WS_URL);
    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);

    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data) as TelemetryPoint;
        setPoints((p) => [data, ...p].slice(0, 200));
      } catch (err) {
        // ignore parse errors
      }
    };

    return () => ws.close();
  }, []);

  return (
    <div style={{ padding: 12 }}>
      <h3>Telemetry PoC Viewer</h3>
      <div>Status: {connected ? "connected" : "disconnected"}</div>
      <div style={{ marginTop: 8 }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th style={{ textAlign: "left" }}>vehicle_id</th>
              <th>ts</th>
              <th>lat</th>
              <th>lon</th>
              <th>status</th>
            </tr>
          </thead>
          <tbody>
            {points.map((pt, i) => (
              <tr key={i}>
                <td>{pt.vehicle_id}</td>
                <td>{new Date(pt.ts).toLocaleString()}</td>
                <td>{pt.lat.toFixed(5)}</td>
                <td>{pt.lon.toFixed(5)}</td>
                <td>{pt.status ?? ""}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default TelemetryViewer;
