document.addEventListener("DOMContentLoaded", () => {
    console.log("Project NexusKV Dashboard Controller active.");

    const API_BASE = "http://127.0.0.1:9001/api/v1";

    const valTotalNodes = document.getElementById("valTotalNodes");
    const valAlerts = document.getElementById("valAlerts");
    const valRaftLeader = document.getElementById("valRaftLeader");
    const valTotalOps = document.getElementById("valTotalOps");
    const consoleOutput = document.getElementById("consoleOutput");

    // Live Metrics Poller
    async function fetchClusterMetrics() {
        try {
            const statusResp = await fetch(`${API_BASE}/cluster/status`);
            if (statusResp.ok) {
                const statusData = await statusResp.json();
                if (valRaftLeader) valRaftLeader.textContent = (statusData.node_id || "NODE-1").toUpperCase();
            }

            const metricsResp = await fetch(`${API_BASE}/metrics`);
            if (metricsResp.ok) {
                const metricsData = await metricsResp.json();
                if (metricsData.stats && valTotalOps) {
                    const sum = metricsData.stats.puts + metricsData.stats.gets + metricsData.stats.deletes;
                    valTotalOps.textContent = sum.toLocaleString();
                }
            }
        } catch (err) {
            console.warn("Metrics polling notice:", err);
        }
    }

    setInterval(fetchClusterMetrics, 2000);
    fetchClusterMetrics();

    // Interactive KV Explorer Buttons
    const btnPut = document.getElementById("btnPut");
    const btnGet = document.getElementById("btnGet");
    const btnDelete = document.getElementById("btnDelete");
    const kvKey = document.getElementById("kvKey");
    const kvVal = document.getElementById("kvVal");

    function logConsole(msg) {
        const time = new Date().toLocaleTimeString();
        consoleOutput.textContent = `[${time}] ${msg}\n` + consoleOutput.textContent;
    }

    if (btnPut) {
        btnPut.addEventListener("click", async () => {
            const key = kvKey.value.trim();
            const val = kvVal.value.trim();
            if (!key) return alert("Please enter a Key");

            logConsole(`Executing PUT '${key}' => '${val}'...`);
            try {
                const resp = await fetch(`${API_BASE}/kv/${encodeURIComponent(key)}`, {
                    method: "PUT",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ value: val })
                });
                const res = await resp.json();
                logConsole(`PUT Response: ${JSON.stringify(res)}`);
                fetchClusterMetrics();
            } catch (e) {
                logConsole(`PUT Error: ${e.message}`);
            }
        });
    }

    if (btnGet) {
        btnGet.addEventListener("click", async () => {
            const key = kvKey.value.trim();
            if (!key) return alert("Please enter a Key");

            logConsole(`Executing GET '${key}'...`);
            try {
                const resp = await fetch(`${API_BASE}/kv/${encodeURIComponent(key)}`);
                const res = await resp.json();
                logConsole(`GET Response: ${JSON.stringify(res)}`);
            } catch (e) {
                logConsole(`GET Error: ${e.message}`);
            }
        });
    }

    if (btnDelete) {
        btnDelete.addEventListener("click", async () => {
            const key = kvKey.value.trim();
            if (!key) return alert("Please enter a Key");

            logConsole(`Executing DELETE '${key}'...`);
            try {
                const resp = await fetch(`${API_BASE}/kv/${encodeURIComponent(key)}`, {
                    method: "DELETE"
                });
                const res = await resp.json();
                logConsole(`DELETE Response: ${JSON.stringify(res)}`);
                fetchClusterMetrics();
            } catch (e) {
                logConsole(`DELETE Error: ${e.message}`);
            }
        });
    }
});
