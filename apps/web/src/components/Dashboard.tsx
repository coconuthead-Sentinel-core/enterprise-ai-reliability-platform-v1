export default function Dashboard() {
  const resultColors: Record<string, string> = {
    pass: "#22c55e",
    conditional: "#f59e0b",
    fail: "#ef4444",
  };

  return (
    <main style={{ fontFamily: "system-ui, sans-serif", maxWidth: 900, margin: "0 auto", padding: 32 }}>
      <h1 style={{ fontSize: 24, fontWeight: 700 }}>EARP — LLM Reliability Platform</h1>
      <p style={{ color: "#6b7280" }}>Sprint 1 dashboard scaffold. Gate decisions and audit reports will appear here.</p>

      <section style={{ marginTop: 32 }}>
        <h2 style={{ fontSize: 18, fontWeight: 600 }}>Result Legend</h2>
        <div style={{ display: "flex", gap: 16, marginTop: 8 }}>
          {Object.entries(resultColors).map(([label, color]) => (
            <span
              key={label}
              style={{
                padding: "4px 12px",
                borderRadius: 4,
                background: color,
                color: "#fff",
                fontWeight: 600,
                textTransform: "capitalize",
              }}
            >
              {label}
            </span>
          ))}
        </div>
      </section>
    </main>
  );
}
