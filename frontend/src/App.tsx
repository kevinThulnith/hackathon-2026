import React, { useState, useEffect } from "react";
import axios from "axios";
import { Shield, Activity, Zap, RefreshCcw } from "lucide-react";
import { UniverseCanvas, type PlanetNode } from "./components/UniverseCanvas";
import "./App.css";

const API_BASE = "/api"; // Or use docker internal host

function App() {
  const [nodes, setNodes] = useState<PlanetNode[]>([]);
  const [origin, setOrigin] = useState<string>("");
  const [destination, setDestination] = useState<string>("");
  const [payload, setPayload] = useState<string>("Hello World");
  const [pathTaken, setPathTaken] = useState<string[]>([]);
  const [hopLog, setHopLog] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [totalLatency, setTotalLatency] = useState<number | null>(null);

  // Fetch universe on load
  const fetchUniverse = async () => {
    try {
      const res = await axios.get(`${API_BASE}/universe/`);
      const nodesArray = Object.values(res.data.nodes);
      setNodes(nodesArray.map((n: any) => ({ ...n, status: "online" })));
      if (nodesArray.length >= 2) {
        setOrigin((nodesArray[0] as any).id);
        setDestination((nodesArray[1] as any).id);
      }
    } catch (err: any) {
      console.error(err);
      setError("Failed to connect to backend. Make sure Django is running.");
    }
  };

  useEffect(() => {
    fetchUniverse();
  }, []);

  const handleRoute = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setLoading(true);
    setError(null);
    setPathTaken([]);
    setHopLog([]);
    setTotalLatency(null);

    try {
      const res = await axios.post(`${API_BASE}/route/`, {
        origin,
        destination,
        payload,
      });
      setPathTaken(res.data.path_taken);
      setHopLog(res.data.hop_log);
      setTotalLatency(res.data.total_latency_seconds);
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.error || "Failed to route packet");
    } finally {
      setLoading(false);
    }
  };

  const handlePlanetClick = async (nodeId: string) => {
    // Toggle node status locally first for immediate feedback
    const node = nodes.find((n) => n.id === nodeId);
    if (!node) return;

    const newAction = node.status === "offline" ? "revive" : "kill";

    setNodes((prev) =>
      prev.map((n) =>
        n.id === nodeId
          ? { ...n, status: newAction === "kill" ? "offline" : "online" }
          : n,
      ),
    );

    try {
      await axios.post(`${API_BASE}/toggle/`, {
        node_id: nodeId,
        action: newAction,
      });

      // Auto re-route if we had a successful route before
      if (origin && destination && payload) {
        handleRoute();
      }
    } catch (err) {
      console.error("Failed to toggle node:", err);
      // Revert if failed
      setNodes((prev) =>
        prev.map((n) => (n.id === nodeId ? { ...n, status: node.status } : n)),
      );
    }
  };

  return (
    <div className="app-container">
      {/* Sidebar Controls */}
      <div className="sidebar glass-panel">
        <div className="header">
          <Shield size={32} color="var(--primary-color)" />
          <div>
            <h1>Relic Ring</h1>
            <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
              ZETA-26 PROTOCOL DASHBOARD
            </div>
          </div>
        </div>

        <div className="control-panel">
          <h2 className="text-gradient">Routing Dashboard</h2>
          <form
            onSubmit={handleRoute}
            className="form-group"
            style={{ gap: "16px", marginTop: "16px" }}
          >
            <div className="form-group">
              <label>Origin Node</label>
              <select
                className="form-control"
                value={origin}
                onChange={(e) => setOrigin(e.target.value)}
              >
                {nodes.map((n) => (
                  <option key={`orig-${n.id}`} value={n.id}>
                    {n.id}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>Destination Node</label>
              <select
                className="form-control"
                value={destination}
                onChange={(e) => setDestination(e.target.value)}
              >
                {nodes.map((n) => (
                  <option key={`dest-${n.id}`} value={n.id}>
                    {n.id}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>Payload (Transmission Data)</label>
              <input
                type="text"
                className="form-control"
                value={payload}
                onChange={(e) => setPayload(e.target.value)}
                placeholder="Enter transmission..."
              />
            </div>

            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? "Calculating Route..." : "Initialize Transmission"}
            </button>
            {error && (
              <div
                style={{ color: "var(--secondary-color)", fontSize: "0.9rem" }}
              >
                {error}
              </div>
            )}
          </form>
        </div>

        <div className="log-panel">
          <h3>
            <Activity size={20} /> Transmission Logs{" "}
            {totalLatency && `(${totalLatency.toFixed(4)}s)`}
          </h3>
          <div className="log-content">
            {hopLog.length === 0 && !loading && (
              <div
                style={{ textAlign: "center", opacity: 0.5, marginTop: "20px" }}
              >
                System ready. Awaiting routing command.
              </div>
            )}

            {hopLog.map((hop, idx) => (
              <div key={idx} className="hop-item">
                <div className="hop-header">
                  Hop {hop.hop_number}: {hop.from_planet} → {hop.to_planet}
                </div>
                <div className="hop-detail">
                  <span>Routing:</span>
                  <span>{hop.tower_routing}</span>
                </div>
                <div className="hop-detail">
                  <span>Distance:</span>
                  <span>{hop.void_distance_km.toLocaleString()} km</span>
                </div>
                <div className="hop-detail">
                  <span>
                    Translation ({hop.data_translation.next_hop_codex}):
                  </span>
                  <span style={{ color: "var(--primary-color)" }}>
                    {hop.data_translation.binary_transmission_stream}
                  </span>
                </div>
                <div
                  className="hop-detail"
                  style={{
                    borderTop: "1px solid rgba(255,255,255,0.1)",
                    paddingTop: "4px",
                    marginTop: "4px",
                  }}
                >
                  <span>Latency:</span>
                  <span>
                    {hop.latency_breakdown.total_hop_latency_sec.toFixed(4)}s
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Main Visualization Canvas */}
      <div className="main-view glass-panel">
        <div className="canvas-container">
          <div className="overlay-status">
            <div className="status-indicator"></div>
            <span>Zeta-26 Subspace Active</span>
            <button
              className="btn-primary"
              style={{
                padding: "4px 8px",
                fontSize: "0.7rem",
                marginLeft: "12px",
              }}
              onClick={fetchUniverse}
            >
              <RefreshCcw size={12} /> Sync
            </button>
          </div>

          <UniverseCanvas
            nodes={nodes}
            pathTaken={pathTaken}
            onPlanetClick={handlePlanetClick}
          />

          <div
            style={{
              position: "absolute",
              bottom: 20,
              left: 20,
              color: "var(--text-secondary)",
              fontSize: "0.8rem",
              background: "rgba(0,0,0,0.5)",
              padding: "8px",
              borderRadius: "4px",
            }}
          >
            <Zap
              size={14}
              style={{
                verticalAlign: "middle",
                marginRight: "4px",
                color: "var(--secondary-color)",
              }}
            />
            Chaos Mode: Click on any planet to simulate a catastrophic hardware
            failure.
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
