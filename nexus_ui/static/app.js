document.addEventListener("DOMContentLoaded", () => {
    console.log("NexusKV Control Center initialized.");
    
    // Simulate dynamic live metrics polling
    setInterval(() => {
        const opsVal = document.getElementById("opsVal");
        if (opsVal) {
            const currentOps = 42000 + Math.floor(Math.random() * 2000);
            opsVal.innerHTML = `${currentOps.toLocaleString()} <small>ops/sec</small>`;
        }
    }, 2000);
});
