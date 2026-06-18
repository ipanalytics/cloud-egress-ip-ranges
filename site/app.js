async function loadJson(path) {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) throw new Error(`failed to load ${path}`);
  return response.json();
}

function setText(id, value) {
  document.getElementById(id).textContent = String(value);
}

function renderProviders(latest, catalog) {
  const counts = latest.providers || {};
  const providers = Object.entries(counts).sort((left, right) => right[1] - left[1]);
  const catalogCount = catalog.providers ? catalog.providers.length : 0;
  setText("records", latest.total_records || 0);
  setText("providers", providers.length);
  setText("sources", Object.keys(latest.sources || {}).length);
  setText("catalog", catalogCount);

  const grid = document.getElementById("provider-grid");
  grid.innerHTML = providers.map(([provider, count]) => (
    `<div class="provider"><strong>${provider}</strong><small>${count.toLocaleString()} CIDR records</small></div>`
  )).join("");
}

Promise.all([
  loadJson("./data/latest.json"),
  loadJson("./data/provider-catalog.json"),
]).then(([latest, catalog]) => renderProviders(latest, catalog)).catch((error) => {
  document.querySelector("main").insertAdjacentHTML(
    "beforeend",
    `<section class="panel"><p class="muted">${error.message}</p></section>`,
  );
});
