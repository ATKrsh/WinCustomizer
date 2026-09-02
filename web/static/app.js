let selectedStep = 1;
let selectedEditionIndex = 1;
let presetsData = null;

document.addEventListener("DOMContentLoaded", () => {
    loadPresets();
    connectSSE();
});

function switchStep(stepNum) {
    selectedStep = stepNum;
    
    // Update Sidebar
    const stepItems = document.querySelectorAll(".step-item");
    stepItems.forEach((item, index) => {
        if (index + 1 === stepNum) {
            item.classList.add("active");
        } else {
            item.classList.remove("active");
        }
    });

    // Update Sections
    for (let i = 1; i <= 5; i++) {
        const sec = document.getElementById(`step-${i}`);
        if (sec) {
            sec.style.display = (i === stepNum) ? "flex" : "none";
        }
    }
}

async function loadPresets() {
    try {
        const res = await fetch("/api/presets");
        presetsData = await res.json();
        renderTweaks(presetsData.tweak_presets);
        renderAppxCatalog(presetsData.appx_catalog);
    } catch (e) {
        console.error("Failed to load presets:", e);
    }
}

function renderTweaks(tweakPresets) {
    const grid = document.getElementById("tweaksGrid");
    grid.innerHTML = "";

    for (const [key, tweak] of Object.entries(tweakPresets)) {
        const label = document.createElement("label");
        label.className = "toggle-card";
        label.innerHTML = `
            <input type="checkbox" id="tweak_${key}" ${tweak.default ? 'checked' : ''}>
            <div class="toggle-info">
                <h4>${tweak.name}</h4>
                <p>${tweak.description}</p>
            </div>
        `;
        grid.appendChild(label);
    }
}

function renderAppxCatalog(catalog) {
    const grid = document.getElementById("appxCategoriesGrid");
    grid.innerHTML = "";

    for (const [catKey, cat] of Object.entries(catalog)) {
        const label = document.createElement("label");
        label.className = "toggle-card";
        label.innerHTML = `
            <input type="checkbox" id="appx_cat_${catKey}" checked>
            <div class="toggle-info">
                <h4>${cat.name}</h4>
                <p>${cat.description} (${cat.packages.length} packages)</p>
            </div>
        `;
        grid.appendChild(label);
    }
}

function onDebloatProfileChange() {
    const profileKey = document.getElementById("debloatProfile").value;
    if (profileKey === "custom" || !presetsData) return;

    const profile = presetsData.debloat_profiles[profileKey];
    if (!profile) return;

    // Toggle categories based on profile
    for (const catKey of Object.keys(presetsData.appx_catalog)) {
        const chk = document.getElementById(`appx_cat_${catKey}`);
        if (chk) {
            chk.checked = profile.categories.includes(catKey);
        }
    }
}

async function inspectISO() {
    const isoPath = document.getElementById("isoPath").value.trim();
    if (!isoPath) {
        alert("Please enter a valid Windows ISO file path.");
        return;
    }

    appendLog(`Sending inspection request for: ${isoPath}`);
    try {
        const res = await fetch("/api/inspect-iso", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ iso_path: isoPath })
        });
        const data = await res.json();
        if (data.error) {
            appendLog(`[ERROR] ${data.error}`);
            alert(`Error inspecting ISO: ${data.error}`);
            return;
        }

        renderEditions(data.editions);
        appendLog(`[SUCCESS] Detected ${data.editions.length} Windows edition(s) in ISO.`);
    } catch (e) {
        appendLog(`[ERROR] ${e.message}`);
    }
}

function renderEditions(editions) {
    const container = document.getElementById("editionsContainer");
    const grid = document.getElementById("editionsGrid");
    grid.innerHTML = "";
    container.style.display = "block";

    editions.forEach((ed, idx) => {
        const card = document.createElement("div");
        card.className = `edition-card ${idx === 0 ? 'selected' : ''}`;
        card.onclick = () => selectEdition(ed.index, card);
        card.innerHTML = `
            <div class="edition-title">Index ${ed.index}: ${ed.name || 'Windows Edition'}</div>
            <div class="edition-meta">
                <span>Architecture: ${ed.architecture || 'x64'}</span>
                <span>Size: ${ed.size || 'N/A'}</span>
                <span>Version: ${ed.version || 'N/A'}</span>
            </div>
        `;
        grid.appendChild(card);
    });

    if (editions.length > 0) {
        selectedEditionIndex = editions[0].index;
    }
}

function selectEdition(index, element) {
    selectedEditionIndex = index;
    document.querySelectorAll(".edition-card").forEach(c => c.classList.remove("selected"));
    element.classList.add("selected");
}

async function startBuild() {
    const isoPath = document.getElementById("isoPath").value.trim();
    if (!isoPath) {
        alert("Please select a valid Windows ISO file first (Step 1).");
        switchStep(1);
        return;
    }

    const debloatProfile = document.getElementById("debloatProfile").value;

    // Gather Tweaks
    const tweaks = {};
    for (const key of Object.keys(presetsData.tweak_presets)) {
        const chk = document.getElementById(`tweak_${key}`);
        if (chk) {
            tweaks[key] = chk.checked;
        }
    }

    // Gather Unattended Config
    const unattended_config = {
        username: document.getElementById("unattendUser").value || "Admin",
        password: document.getElementById("unattendPass").value || "",
        computer_name: document.getElementById("unattendPCName").value || "WinCustom-PC",
        language: document.getElementById("unattendLang").value || "en-US",
        skip_oobe: document.getElementById("skipOOBE").checked,
        auto_logon: document.getElementById("autoLogon").checked
    };

    const payload = {
        iso_path: isoPath,
        edition_index: selectedEditionIndex,
        debloat_profile: debloatProfile,
        tweaks: tweaks,
        unattended_config: unattended_config
    };

    document.getElementById("btnBuild").disabled = true;
    appendLog("\nStarting WinCustomizer customization engine...");

    try {
        const res = await fetch("/api/start-build", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.error) {
            appendLog(`[ERROR] ${data.error}`);
            document.getElementById("btnBuild").disabled = false;
        }
    } catch (e) {
        appendLog(`[ERROR] Failed to start build: ${e.message}`);
        document.getElementById("btnBuild").disabled = false;
    }
}

function connectSSE() {
    const evtSource = new EventSource("/api/events");
    evtSource.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            if (data.message) {
                appendLog(data.message);
                if (data.message.startsWith("BUILD_SUCCESS:") || data.message.startsWith("BUILD_ERROR:")) {
                    document.getElementById("btnBuild").disabled = false;
                }
            }
        } catch (e) {
            console.error("Error parsing event data:", e);
        }
    };
    evtSource.onerror = (e) => {
        console.warn("SSE connection interrupted. Retrying...", e);
    };
}

function appendLog(msg) {
    const consoleBody = document.getElementById("consoleLog");
    const timestamp = new Date().toLocaleTimeString();
    consoleBody.innerText += `\n[${timestamp}] ${msg}`;
    consoleBody.scrollTop = consoleBody.scrollHeight;
}
