import { useEffect, useState } from "react";
import { api, ReliabilityOutput, AnomalyOutput } from "./api";

export default function App() {
  const [token, setToken] = useState<string | null>(null);
  const [email, setEmail] = useState("shannon@example.com");
  const [password, setPassword] = useState("correcthorsebatterystaple");
  const [mtbf, setMtbf] = useState(1000);
  const [mttr, setMttr] = useState(4);
  const [mission, setMission] = useState(720);
  const [latest, setLatest] = useState<ReliabilityOutput | null>(null);
  const [history, setHistory] = useState<ReliabilityOutput[]>([]);
  const [anomaly, setAnomaly] = useState<AnomalyOutput | null>(null);
  const [err, setErr] = useState<string | null>(null);

  async function doLogin() {
    setErr(null);
    try {
      const t = await api.login(email, password);
      setToken(t.access_token);
    } catch (e) {
      // Fall back to register then login on first run
      try {
        await api.register(email, password);
        const t = await api.login(email, password);
        setToken(t.access_token);
      } catch (e2) {
        setErr(String(e2));
      }
    }
  }

  async function doCompute() {
    setErr(null);
    try {
      const out = await api.compute({
        mtbf_hours: mtbf,
        mttr_hours: mttr,
        mission_time_hours: mission,
      });
      setLatest(out);
      const h = await api.history();
      setHistory(h);
    } catch (e) {
      setErr(String(e));
    }
  }

  async function doAnomaly() {
    if (!token) return setErr("Login first");
    try {
      const out = await api.anomalyFromHistory(token, 0.2);
      setAnomaly(out);
    } catch (e) {
      setErr(String(e));
    }
  }

  useEffect(() => {
    api.history().then(setHistory).catch(() => {});
  }, []);

  return (
    <div className="wrap">
      <h1>Enterprise AI Reliability Platform</h1>
      <p className="muted">v0.3.0 - FastAPI + scikit-learn + React TS</p>

      {err && <div className="err">{err}</div>}

      <section>
        <h2>1. Auth</h2>
        <div className="row">
          <input value={email} onChange={(e) => setEmail(e.target.value)} />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <button onClick={doLogin}>
            {token ? "Re-login" : "Login / register"}
          </button>
        </div>
        <p className="muted">
          {token ? `Token acquired (${token.slice(0, 20)}...)` : "Not logged in"}
        </p>
      </section>

      <section>
        <h2>2. Reliability (MTBF / MTTR to Availability & Reliability)</h2>
        <div className="row">
          <label>
            MTBF (h)
            <input
              type="number"
              value={mtbf}
              onChange={(e) => setMtbf(Number(e.target.value))}
            />
          </label>
          <label>
            MTTR (h)
            <input
              type="number"
              value={mttr}
              onChange={(e) => setMttr(Number(e.target.value))}
            />
          </label>
          <label>
            Mission time (h)
            <input
              type="number"
              value={mission}
              onChange={(e) => setMission(Number(e.target.value))}
            />
          </label>
          <button onClick={doCompute}>Compute</button>
        </div>
        {latest && (
          <pre>
            {JSON.stringify(latest, null, 2)}
          </pre>
        )}
      </section>

      <section>
        <h2>3. History ({history.length})</h2>
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>MTBF</th>
              <th>MTTR</th>
              <th>Mission</th>
              <th>Avail.</th>
              <th>Reliab.</th>
            </tr>
          </thead>
          <tbody>
            {history.map((h) => (
              <tr key={h.id}>
                <td>{h.id}</td>
                <td>{h.mtbf_hours}</td>
                <td>{h.mttr_hours}</td>
                <td>{h.mission_time_hours}</td>
                <td>{h.availability.toFixed(4)}</td>
                <td>{h.reliability.toFixed(4)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section>
        <h2>4. Anomaly detection (real IsolationForest)</h2>
        <button onClick={doAnomaly} disabled={!token}>
          Run on history
        </button>
        {anomaly && (
          <pre>
            {JSON.stringify(anomaly, null, 2)}
          </pre>
        )}
      </section>
    </div>
  );
}
