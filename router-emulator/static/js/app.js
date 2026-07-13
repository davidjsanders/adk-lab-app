/**
 * Router Emulator Client Logic
 * Handles real-time LED rendering, command dispatching, log streaming, and API execution.
 */

document.addEventListener("DOMContentLoaded", () => {
    // DOM Element References
    const inputAuthPass = document.getElementById("input-auth-pass");
    const labelPassPreview = document.getElementById("label-pass-preview");
    const labelJsonPayload = document.getElementById("label-json-payload");
    const terminalLogs = document.getElementById("terminal-logs");
    
    // Status LCD & Badges
    const lcdUptime = document.getElementById("lcd-uptime");
    const lcdState = document.getElementById("lcd-state");
    const badgeSysStatus = document.getElementById("badge-sys-status");
    
    // Quick Action Buttons
    const btnPowerUp = document.getElementById("cmd-power-up");
    const btnPowerDown = document.getElementById("cmd-power-down");
    const btnReboot = document.getElementById("cmd-reboot");
    const btnBgpReset = document.getElementById("cmd-bgp-reset");
    const btnTraffic = document.getElementById("cmd-traffic");
    
    // Bezel Physical Buttons
    const btnBezelPower = document.getElementById("btn-bezel-power");
    const btnBezelReset = document.getElementById("btn-bezel-reset");
    
    // Manual LED Controls
    const selectLedTarget = document.getElementById("select-led-target");
    const selectLedColor = document.getElementById("select-led-color");
    const btnApplyLed = document.getElementById("btn-apply-led");
    const btnClearLogs = document.getElementById("btn-clear-logs");

    let headerName = "X-Control-Password";

    /**
     * Updates pass preview label securely without logging secret
     */
    function updatePassPreview() {
        const val = inputAuthPass ? inputAuthPass.value : "";
        if (labelPassPreview) {
            labelPassPreview.textContent = val ? "••••••••" : "<EMPTY>";
        }
    }

    if (inputAuthPass) {
        inputAuthPass.addEventListener("input", updatePassPreview);
    }

    /**
     * Maps status LED state names to CSS glow classes
     * @param {HTMLElement} element LED indicator element
     * @param {string} state State value (green, amber, red, off, flash, flash_fast)
     */
    function applyLedState(element, state) {
        if (!element) return;
        element.className = "led-indicator"; // Reset base classes
        
        switch (state.toLowerCase()) {
            case "green":
                element.classList.add("led-green");
                break;
            case "amber":
                element.classList.add("led-amber");
                break;
            case "red":
                element.classList.add("led-red");
                break;
            case "flash":
                element.classList.add("led-green", "led-flash");
                break;
            case "flash_fast":
                element.classList.add("led-amber", "led-flash-fast");
                break;
            case "off":
            default:
                element.classList.add("led-off");
                break;
        }
    }

    /**
     * Safely appends log lines into the terminal window using secure DOM creation
     * @param {Array} logs Array of log objects {timestamp, level, message}
     */
    function renderTerminalLogs(logs) {
        if (!terminalLogs || !Array.isArray(logs)) return;
        
        // Clear terminal window safely
        terminalLogs.replaceChildren();

        logs.forEach(logItem => {
            const line = document.createElement("div");
            line.className = "terminal-line";

            const timeSpan = document.createElement("span");
            timeSpan.className = "term-time";
            timeSpan.textContent = `[${logItem.timestamp}]`;

            const levelSpan = document.createElement("span");
            const lvl = (logItem.level || "INFO").toUpperCase();
            if (lvl === "WARN") levelSpan.className = "term-level-warn";
            else if (lvl === "ERROR") levelSpan.className = "term-level-error";
            else levelSpan.className = "term-level-info";
            levelSpan.textContent = `[${lvl}]`;

            const msgSpan = document.createElement("span");
            msgSpan.className = "term-msg";
            msgSpan.textContent = logItem.message;

            line.appendChild(timeSpan);
            line.appendChild(levelSpan);
            line.appendChild(msgSpan);
            terminalLogs.appendChild(line);
        });

        // Auto scroll to bottom
        terminalLogs.scrollTop = terminalLogs.scrollHeight;
    }

    /**
     * Polls router status telemetry endpoint and updates UI components
     */
    async function fetchRouterStatus() {
        try {
            const res = await fetch("/api/status");
            if (!res.ok) return;
            const data = await res.json();

            // Update Metadata Header Name & SNMP Status
            if (data.metadata) {
                if (data.metadata.control_header) {
                    headerName = data.metadata.control_header;
                }
                const lcdSnmp = document.getElementById("lcd-snmp");
                if (lcdSnmp && data.metadata.snmp) {
                    const snmpInfo = data.metadata.snmp;
                    if (snmpInfo.enabled) {
                        lcdSnmp.textContent = `/snmp/walk (${snmpInfo.community})`;
                    } else {
                        lcdSnmp.textContent = "DISABLED";
                    }
                }
            }

            // Update LCD Display
            if (data.telemetry) {
                if (lcdUptime) lcdUptime.textContent = `${data.telemetry.uptime_seconds}s`;
                if (lcdState) lcdState.textContent = data.telemetry.status;
                if (badgeSysStatus) badgeSysStatus.textContent = data.telemetry.status;
            }

            // Update LED indicators
            if (data.leds) {
                Object.keys(data.leds).forEach(ledKey => {
                    const ledElem = document.getElementById(`led-${ledKey}`);
                    applyLedState(ledElem, data.leds[ledKey]);
                });
            }

            // Update Logs
            if (data.logs) {
                renderTerminalLogs(data.logs);
            }

        } catch (err) {
            // Quiet fail for polling
        }
    }

    /**
     * Sends control command request to router command API
     * @param {string} command Command key string
     * @param {object} parameters Optional command parameters
     */
    async function sendControlCommand(command, parameters = {}) {
        const pass = inputAuthPass ? inputAuthPass.value : "";
        const payload = { command, parameters };

        if (labelJsonPayload) {
            labelJsonPayload.textContent = JSON.stringify(payload, null, 2);
        }

        try {
            const response = await fetch("/api/command", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    [headerName]: pass
                },
                body: JSON.stringify(payload)
            });

            const result = await response.json();
            if (!response.ok) {
                alert(`Command Failed: ${result.message || result.error || "Unauthorized"}`);
            } else {
                // Immediately refresh status
                fetchRouterStatus();
            }
        } catch (err) {
            alert(`Error connecting to router command API: ${err.message}`);
        }
    }

    // Bind Event Listeners
    if (btnPowerUp) btnPowerUp.addEventListener("click", () => sendControlCommand("power_up"));
    if (btnPowerDown) btnPowerDown.addEventListener("click", () => sendControlCommand("power_down"));
    if (btnReboot) btnReboot.addEventListener("click", () => sendControlCommand("reset"));
    if (btnBgpReset) btnBgpReset.addEventListener("click", () => sendControlCommand("bgp_reset"));
    if (btnTraffic) btnTraffic.addEventListener("click", () => sendControlCommand("send_info"));

    if (btnBezelPower) btnBezelPower.addEventListener("click", () => sendControlCommand("power_up"));
    if (btnBezelReset) btnBezelReset.addEventListener("click", () => sendControlCommand("reset"));

    if (btnApplyLed) {
        btnApplyLed.addEventListener("click", () => {
            const led = selectLedTarget ? selectLedTarget.value : "power";
            const color = selectLedColor ? selectLedColor.value : "green";
            sendControlCommand("set_led", { led, color });
        });
    }

    if (btnClearLogs) {
        btnClearLogs.addEventListener("click", () => {
            if (terminalLogs) terminalLogs.replaceChildren();
        });
    }

    // Start status polling every 1.5 seconds
    fetchRouterStatus();
    setInterval(fetchRouterStatus, 1500);
});
