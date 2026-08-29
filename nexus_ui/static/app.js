document.addEventListener("DOMContentLoaded", () => {
    console.log("NexusKV Dashboard Controller Initialized.");

    const API_BASE = "http://127.0.0.1:9001/api/v1";

    const opsVal = document.getElementById("opsVal");
    const totalOps = document.getElementById("totalOps");
    const writeP99 = document.getElementById("writeP99");
    const nodeId = document.getElementById("nodeId");
    const raftTerm = document.getElementById("raftTerm");
    const walSeq = document.getElementById("walSeq");
    const memBytes = document.getElementById("memBytes");
    const l0Count = document.getElementById("l0Count");
    const cacheCount = document.getElementById("cacheCount");
    const memBarFill = document.getElementById("memBarFill");
    const consoleOutput = document.getElementById("consoleOutput");

    // Live Metrics Poller
    async function fetchClusterMetrics() {
        try {
            const statusResp = await fetch(`${API_BASE}/cluster/status`);
            if (statusResp.ok) {
                const statusData = await statusResp.json();
                if (nodeId) nodeId.textContent = statusData.node_id || "node-1";
                if (l0Count) l0Count.textContent = statusData.active_level_0_sstables || "0";
                if (memBytes) {
                    const mb = (statusData.memtable_bytes / 1024).toFixed(2);
                    memBytes.textContent = `${mb} KB`;
                    const pct = Math.min(100, Math.max(5, (statusData.memtable_bytes / 67108864) * 100));
                    if (memBarFill) memBarFill.style.width = `${pct}%`;
                }
            }

            const metricsResp = await fetch(`${API_BASE}/metrics`);
            if (metricsResp.ok) {
                const metricsData = await metricsResp.json();
                if (metricsData.stats) {
                    if (totalOps) totalOps.textContent = metricsData.stats.puts + metricsData.stats.gets + metricsData.stats.deletes;
                }
                if (metricsData.wal_sequence !== undefined && walSeq) {
                    walSeq.textContent = metricsData.wal_sequence;
                }
                if (metricsData.cache_items !== undefined && cacheCount) {
                    cacheCount.textContent = `${metricsData.cache_items} items`;
                }
            }

            // Simulate ops per second
            if (opsVal) {
                const ops = 42000 + Math.floor(Math.random() * 2500);
                opsVal.innerHTML = `${ops.toLocaleString()} <small>ops/sec</small>`;
            }

        } catch (err) {
            console.warn("Metrics fetch warning:", err);
        }
    }

    // Polling every 2 seconds
    setInterval(fetchClusterMetrics, 2000);
    fetchClusterMetrics();

    // Interactive KV Actions
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
                logConsole(`PUT Result: ${JSON.stringify(res)}`);
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
                logConsole(`GET Result: ${JSON.stringify(res)}`);
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
                logConsole(`DELETE Result: ${JSON.stringify(res)}`);
                fetchClusterMetrics();
            } catch (e) {
                logConsole(`DELETE Error: ${e.message}`);
            }
        });
    }
});
