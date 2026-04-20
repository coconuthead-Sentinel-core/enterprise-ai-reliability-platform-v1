import { useMemo, useState } from "react";
import {
  api,
  AssessmentOutput,
  ComplianceControl,
  DashboardEpic,
  DashboardMetric,
  ExecutiveSummary,
  PolicyHistoryRecord,
} from "./api";

type WorkspaceView = "release" | "security" | "executive";

const DATE_FORMAT = new Intl.DateTimeFormat(undefined, {
  month: "short",
  day: "numeric",
  hour: "numeric",
  minute: "2-digit",
});

const STATUS_LABELS: Record<string, string> = {
  good: "On target",
  attention: "Needs work",
  blocked: "Blocked",
  empty: "No data",
  implemented: "Implemented",
  partial: "Partial",
  planned: "Planned",
};

function formatTimestamp(value: string) {
  return DATE_FORMAT.format(new Date(value));
}

function formatPercent(value: number, total: number) {
  if (total === 0) return "0%";
  return `${Math.round((value / total) * 100)}%`;
}

function buildNarrative(summary: ExecutiveSummary) {
  const dashboard = summary.dashboard;
  const policy = dashboard.policy_history.stats;
  const assessments = dashboard.assessment_summary;
  return `Current branch ${summary.branch} is carrying Sprint ${summary.current_sprint} delivery with ${dashboard.epic_completion_percent.toFixed(
    1
  )}% epic completion, ${policy.allow_count} allow decisions in the policy window, and ${assessments.high_risk} high-risk assessments still requiring remediation.`;
}

function StatusPill({ status }: { status: string }) {
  return (
    <span className={`status-pill status-${status}`}>
      {STATUS_LABELS[status] ?? status}
    </span>
  );
}

function MetricCard({ metric }: { metric: DashboardMetric }) {
  return (
    <article className="metric-card">
      <div className="metric-head">
        <span className="metric-label">{metric.label}</span>
        <StatusPill status={metric.status} />
      </div>
      <div className="metric-value">{metric.value}</div>
      <div className="metric-target">{metric.target ?? "No target"}</div>
      <p className="metric-detail">{metric.detail}</p>
    </article>
  );
}

function ViewTabs({
  active,
  onChange,
}: {
  active: WorkspaceView;
  onChange: (view: WorkspaceView) => void;
}) {
  const views: Array<[WorkspaceView, string]> = [
    ["release", "Release"],
    ["security", "Security"],
    ["executive", "Executive"],
  ];
  return (
    <div className="view-tabs" role="tablist" aria-label="Workspace views">
      {views.map(([value, label]) => (
        <button
          key={value}
          className={`tab-button ${active === value ? "tab-active" : ""}`}
          onClick={() => onChange(value)}
          role="tab"
          aria-selected={active === value}
        >
          {label}
        </button>
      ))}
    </div>
  );
}

function EpicTable({ epics }: { epics: DashboardEpic[] }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Epic</th>
            <th>Title</th>
            <th>Status</th>
            <th>Sprint</th>
          </tr>
        </thead>
        <tbody>
          {epics.map((epic) => (
            <tr key={epic.id}>
              <td>{epic.id}</td>
              <td>{epic.title}</td>
              <td>
                <StatusPill status={epic.status === "done" ? "good" : epic.status === "in_progress" ? "attention" : "empty"} />
              </td>
              <td>{epic.sprint}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function DistributionBar({
  label,
  value,
  total,
  tone,
}: {
  label: string;
  value: number;
  total: number;
  tone: "green" | "amber" | "red" | "slate";
}) {
  const width = total === 0 ? 0 : Math.max((value / total) * 100, value > 0 ? 8 : 0);
  return (
    <div className="distribution-row">
      <div className="distribution-meta">
        <span>{label}</span>
        <strong>
          {value} <span className="muted-inline">{formatPercent(value, total)}</span>
        </strong>
      </div>
      <div className="distribution-track">
        <div className={`distribution-fill tone-${tone}`} style={{ width: `${width}%` }} />
      </div>
    </div>
  );
}

function AssessmentTable({ rows }: { rows: AssessmentOutput[] }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>System</th>
            <th>Owner</th>
            <th>Overall</th>
            <th>Risk</th>
            <th>Gate</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td colSpan={6}>No assessments yet.</td>
            </tr>
          ) : (
            rows.map((row) => (
              <tr key={row.id}>
                <td>{row.system_name}</td>
                <td>{row.owner}</td>
                <td>{row.overall_score.toFixed(1)}</td>
                <td>{row.risk_tier}</td>
                <td>{row.gate_decision ?? "-"}</td>
                <td>{formatTimestamp(row.created_at)}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

function PolicyTable({ rows }: { rows: PolicyHistoryRecord[] }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>System</th>
            <th>Decision</th>
            <th>Composite</th>
            <th>Tier</th>
            <th>Time</th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td colSpan={5}>No policy evaluations yet.</td>
            </tr>
          ) : (
            rows.map((row) => (
              <tr key={row.id}>
                <td>{row.system_name}</td>
                <td>{row.decision}</td>
                <td>{row.composite_score.toFixed(1)}</td>
                <td>{row.tier}</td>
                <td>{formatTimestamp(row.created_at)}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

function ControlList({ controls }: { controls: ComplianceControl[] }) {
  return (
    <div className="control-list">
      {controls.map((control) => (
        <article className="control-item" key={control.control_id}>
          <div className="control-head">
            <div>
              <div className="control-id">{control.control_id}</div>
              <h3>{control.title}</h3>
            </div>
            <StatusPill status={control.status} />
          </div>
          <p className="control-summary">{control.summary}</p>
          <div className="control-columns">
            <div>
              <h4>Evidence</h4>
              <ul>
                {control.evidence.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
            <div>
              <h4>Gaps</h4>
              <ul>
                {control.gaps.length === 0 ? <li>No open gap in this control.</li> : control.gaps.map((item) => <li key={item}>{item}</li>)}
              </ul>
            </div>
          </div>
        </article>
      ))}
    </div>
  );
}

export default function App() {
  const [token, setToken] = useState<string | null>(null);
  const [email, setEmail] = useState("shannon@example.com");
  const [password, setPassword] = useState("correcthorsebatterystaple");
  const [summary, setSummary] = useState<ExecutiveSummary | null>(null);
  const [activeView, setActiveView] = useState<WorkspaceView>("release");
  const [busy, setBusy] = useState(false);
  const [seeding, setSeeding] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const dashboard = summary?.dashboard ?? null;

  async function loadWorkspace(nextToken: string) {
    setErr(null);
    const nextSummary = await api.getExecutiveSummary(nextToken);
    setSummary(nextSummary);
  }

  async function openWorkspace() {
    setBusy(true);
    setErr(null);
    try {
      try {
        const session = await api.login(email, password);
        setToken(session.access_token);
        await loadWorkspace(session.access_token);
      } catch {
        await api.register(email, password);
        const session = await api.login(email, password);
        setToken(session.access_token);
        await loadWorkspace(session.access_token);
      }
    } catch (e) {
      setErr(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function seedSampleData() {
    if (!token) {
      setErr("Open the workspace first.");
      return;
    }
    setSeeding(true);
    setErr(null);
    try {
      const scenarios = [
        {
          score: {
            system_name: "Claims Triage Model",
            components: [
              { name: "groundedness", value: 0.94, weight: 0.35, nist_function: "measure" as const },
              { name: "governance", value: 0.88, weight: 0.2, nist_function: "govern" as const },
              { name: "task_success", value: 0.91, weight: 0.25, nist_function: "map" as const },
              { name: "safety_posture", value: 0.86, weight: 0.2, nist_function: "manage" as const },
            ],
          },
          assessment: {
            system_name: "Claims Triage Model",
            owner: "Release Engineering",
            govern_score: 88,
            map_score: 84,
            measure_score: 92,
            manage_score: 86,
            notes: "Primary release candidate.",
          },
        },
        {
          score: {
            system_name: "Support Copilot",
            components: [
              { name: "groundedness", value: 0.79, weight: 0.35, nist_function: "measure" as const },
              { name: "governance", value: 0.74, weight: 0.2, nist_function: "govern" as const },
              { name: "task_success", value: 0.81, weight: 0.25, nist_function: "map" as const },
              { name: "safety_posture", value: 0.67, weight: 0.2, nist_function: "manage" as const },
            ],
          },
          assessment: {
            system_name: "Support Copilot",
            owner: "Product Quality",
            govern_score: 72,
            map_score: 78,
            measure_score: 81,
            manage_score: 66,
            notes: "Needs guardrail tuning before promotion.",
          },
        },
        {
          score: {
            system_name: "Policy Intake Agent",
            components: [
              { name: "groundedness", value: 0.52, weight: 0.35, nist_function: "measure" as const },
              { name: "governance", value: 0.38, weight: 0.2, nist_function: "govern" as const },
              { name: "task_success", value: 0.61, weight: 0.25, nist_function: "map" as const },
              { name: "safety_posture", value: 0.42, weight: 0.2, nist_function: "manage" as const },
            ],
          },
          assessment: {
            system_name: "Policy Intake Agent",
            owner: "Safety and Compliance",
            govern_score: 38,
            map_score: 61,
            measure_score: 52,
            manage_score: 42,
            notes: "Held in remediation due to governance gap.",
          },
        },
      ];

      for (const scenario of scenarios) {
        await api.createReliabilityScore(scenario.score);
        await api.evaluatePolicy({ score_input: scenario.score });
        await api.createAssessment(token, scenario.assessment);
      }

      await loadWorkspace(token);
    } catch (e) {
      setErr(String(e));
    } finally {
      setSeeding(false);
    }
  }

  async function exportPdf() {
    if (!token) {
      setErr("Open the workspace first.");
      return;
    }
    setExporting(true);
    setErr(null);
    try {
      const blob = await api.executiveSummaryPdf(token);
      const href = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = href;
      anchor.download = "earp-executive-summary.pdf";
      anchor.click();
      URL.revokeObjectURL(href);
    } catch (e) {
      setErr(String(e));
    } finally {
      setExporting(false);
    }
  }

  const narrative = useMemo(() => (summary ? buildNarrative(summary) : null), [summary]);

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <div className="eyebrow">Enterprise AI Reliability Platform</div>
          <h1>Dashboard and Reporting Workspace</h1>
          <p className="topline">
            Release posture, assessment risk, policy audit history, and security evidence in one local view.
          </p>
        </div>
        <div className="session-panel">
          <div className="session-fields">
            <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" />
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password"
            />
          </div>
          <div className="session-actions">
            <button onClick={openWorkspace} disabled={busy}>
              {busy ? "Opening..." : token ? "Refresh workspace" : "Open workspace"}
            </button>
            <button onClick={seedSampleData} disabled={!token || seeding} className="secondary-button">
              {seeding ? "Seeding..." : "Seed sample data"}
            </button>
            <button onClick={exportPdf} disabled={!token || exporting} className="secondary-button">
              {exporting ? "Exporting..." : "Export PDF"}
            </button>
          </div>
          <div className="session-meta">
            {summary ? (
              <>
                <span>Viewer role: {summary.viewer_role}</span>
                <span>Release: {summary.release}</span>
                <span>Branch: {summary.branch}</span>
                <span>Updated: {formatTimestamp(summary.generated_at)}</span>
              </>
            ) : (
              <span>Sign in to load the dashboard and exports.</span>
            )}
          </div>
        </div>
      </header>

      {err && <div className="err-banner">{err}</div>}

      {!summary ? (
        <main className="empty-state">
          <h2>Workspace not loaded</h2>
          <p>
            Open the workspace to pull the dashboard summary, the compliance evidence bundle, and the PDF export.
          </p>
        </main>
      ) : (
        <main className="workspace">
          <section className="section-block">
            <div className="section-header">
              <div>
                <h2>Executive snapshot</h2>
                <p>{narrative}</p>
              </div>
              <ViewTabs active={activeView} onChange={setActiveView} />
            </div>

            <div className="metrics-grid">
              {dashboard?.metrics.map((metric) => (
                <MetricCard key={metric.key} metric={metric} />
              ))}
            </div>
          </section>

          {activeView === "release" && dashboard && (
            <>
              <section className="section-block split-layout">
                <div>
                  <div className="section-header compact">
                    <div>
                      <h2>Epic progress</h2>
                      <p>{dashboard.epic_completion_percent.toFixed(1)}% of epics currently marked done.</p>
                    </div>
                  </div>
                  <EpicTable epics={dashboard.epics} />
                </div>
                <div>
                  <div className="section-header compact">
                    <div>
                      <h2>Assessment posture</h2>
                      <p>Risk and gate distributions across the current local dataset.</p>
                    </div>
                  </div>
                  <div className="distribution-panel">
                    <DistributionBar
                      label="Low risk"
                      value={dashboard.assessment_summary.low_risk}
                      total={dashboard.assessment_summary.total}
                      tone="green"
                    />
                    <DistributionBar
                      label="Medium risk"
                      value={dashboard.assessment_summary.medium_risk}
                      total={dashboard.assessment_summary.total}
                      tone="amber"
                    />
                    <DistributionBar
                      label="High risk"
                      value={dashboard.assessment_summary.high_risk}
                      total={dashboard.assessment_summary.total}
                      tone="red"
                    />
                    <DistributionBar
                      label="Allow decisions"
                      value={dashboard.assessment_summary.allow_count}
                      total={dashboard.assessment_summary.total}
                      tone="green"
                    />
                    <DistributionBar
                      label="Warn decisions"
                      value={dashboard.assessment_summary.warn_count}
                      total={dashboard.assessment_summary.total}
                      tone="amber"
                    />
                    <DistributionBar
                      label="Block decisions"
                      value={dashboard.assessment_summary.block_count}
                      total={dashboard.assessment_summary.total}
                      tone="red"
                    />
                  </div>
                </div>
              </section>

              <section className="section-block">
                <div className="section-header compact">
                  <div>
                    <h2>Recent assessments</h2>
                    <p>Newest-first assessment rows with embedded gate outcomes.</p>
                  </div>
                </div>
                <AssessmentTable rows={dashboard.recent_assessments} />
              </section>

              <section className="section-block">
                <div className="section-header compact">
                  <div>
                    <h2>Policy history window</h2>
                    <p>
                      {dashboard.policy_history.stats.count} policy evaluations in the current window. Trend:{" "}
                      {dashboard.policy_history.stats.trend_direction}.
                    </p>
                  </div>
                </div>
                <PolicyTable rows={dashboard.policy_history.records} />
              </section>
            </>
          )}

          {activeView === "security" && summary && (
            <>
              <section className="section-block">
                <div className="section-header compact">
                  <div>
                    <h2>Security and compliance controls</h2>
                    <p>Repo-backed control status with evidence paths and open gaps.</p>
                  </div>
                  <StatusPill status={summary.compliance.overall_status} />
                </div>
                <ControlList controls={summary.compliance.controls} />
              </section>

              <section className="section-block split-layout">
                <div>
                  <div className="section-header compact">
                    <div>
                      <h2>Outstanding gaps</h2>
                      <p>These items still separate the local build from a full live release.</p>
                    </div>
                  </div>
                  <ul className="bullet-list">
                    {summary.compliance.outstanding_gaps.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <div className="section-header compact">
                    <div>
                      <h2>Recommended next steps</h2>
                      <p>Execution order for the next security/compliance slice.</p>
                    </div>
                  </div>
                  <ul className="bullet-list">
                    {summary.compliance.recommended_next_steps.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
              </section>
            </>
          )}

          {activeView === "executive" && summary && (
            <>
              <section className="section-block split-layout">
                <div>
                  <div className="section-header compact">
                    <div>
                      <h2>Executive summary</h2>
                      <p>The same data used for the PDF export, kept readable in-app.</p>
                    </div>
                  </div>
                  <p className="narrative">{buildNarrative(summary)}</p>
                  <div className="snapshot-list">
                    <div>
                      <span className="snapshot-label">Policy trend</span>
                      <strong>{summary.dashboard.policy_history.stats.trend_direction}</strong>
                    </div>
                    <div>
                      <span className="snapshot-label">Average composite</span>
                      <strong>
                        {summary.dashboard.score_history.stats.rolling_average?.toFixed(1) ?? "No data"}
                      </strong>
                    </div>
                    <div>
                      <span className="snapshot-label">High-risk assessments</span>
                      <strong>{summary.dashboard.assessment_summary.high_risk}</strong>
                    </div>
                  </div>
                </div>
                <div>
                  <div className="section-header compact">
                    <div>
                      <h2>Export readiness</h2>
                      <p>The PDF export uses the same executive summary and control bundle shown here.</p>
                    </div>
                  </div>
                  <ul className="bullet-list">
                    <li>Release metrics and epic status are bundled into the export.</li>
                    <li>Recent assessments and gate outcomes are included.</li>
                    <li>Compliance controls and remaining blockers are carried into the same artifact.</li>
                    <li>Azure deploy remains outside the export until live URLs exist.</li>
                  </ul>
                </div>
              </section>
            </>
          )}
        </main>
      )}
    </div>
  );
}
