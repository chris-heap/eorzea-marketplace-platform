const API_BASE = "http://localhost:8000";

export async function chatQuery(question) {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!res.ok) throw new Error(`Chat failed: ${res.status}`);
  return res.json();
}

export async function getArbitrage(minMargin = 50, limit = 20) {
  const res = await fetch(
    `${API_BASE}/arbitrage?min_margin=${minMargin}&limit=${limit}`
  );
  if (!res.ok) throw new Error(`Arbitrage failed: ${res.status}`);
  return res.json();
}

export async function getPrices(itemName) {
  const res = await fetch(
    `${API_BASE}/prices/${encodeURIComponent(itemName)}`
  );
  if (!res.ok) throw new Error(`Prices failed: ${res.status}`);
  return res.json();
}

export async function getVelocity(limit = 20) {
  const res = await fetch(`${API_BASE}/velocity?limit=${limit}`);
  if (!res.ok) throw new Error(`Velocity failed: ${res.status}`);
  return res.json();
}
