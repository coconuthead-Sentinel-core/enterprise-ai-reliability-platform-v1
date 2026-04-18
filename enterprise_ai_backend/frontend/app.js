// Minimal vanilla-JS front end. No framework, no build step.
// Same-origin when served via /ui, otherwise points to localhost:8000.
const API = (location.origin && location.origin.startsWith("http"))
  ? location.origin
  : "http://127.0.0.1:8000";

const $ = (id) => document.getElementById(id);
const show = (id, data) => { $(id).textContent = JSON.stringify(data, null, 2); };

async function api(path, opts = {}) {
  const r = await fetch(API + path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  const body = await r.json().catch(() => ({}));
  return { status: r.status, body };
}

async function refreshHealth() {
  const { status, body } = await api("/health");
  $("status").textContent = status === 200
    ? `Backend online - ${body.app_name} v${body.app_version} (${body.app_env})`
    : `Backend error: ${status}`;
  show("out-health", body);
}

async function compute() {
  const payload = {
    mtbf_hours: Number($("mtbf").value),
    mttr_hours: Number($("mttr").value),
    mission_time_hours: Number($("mission").value),
  };
  const { body } = await api("/reliability/compute", {
    method: "POST", body: JSON.stringify(payload),
  });
  show("out-rel", body);
}

async function createAssessment() {
  const payload = {
    system_name: $("system_name").value,
    owner: $("owner").value,
    govern_score: Number($("govern_score").value),
    map_score: Number($("map_score").value),
    measure_score: Number($("measure_score").value),
    manage_score: Number($("manage_score").value),
  };
  const { body } = await api("/assessments", {
    method: "POST", body: JSON.stringify(payload),
  });
  show("out-asm", body);
  listAssessments();
}

async function listAssessments() {
  const { body } = await api("/assessments");
  show("out-list", body);
}

async function hashText() {
  const { body } = await api("/hash/sha256", {
    method: "POST",
    body: JSON.stringify({ text: $("hash-text").value }),
  });
  show("out-hash", body);
}

$("btn-health").addEventListener("click", refreshHealth);
$("btn-rel").addEventListener("click", compute);
$("btn-asm").addEventListener("click", createAssessment);
$("btn-list").addEventListener("click", listAssessments);
$("btn-hash").addEventListener("click", hashText);

refreshHealth();
listAssessments();
