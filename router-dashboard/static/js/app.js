/**
 * Router Operations Dashboard Client Logic (Material Design 3 Edition)
 * Controls navigation drawer, right side-sheet command console, multi-router visualizers, and telemetry polling.
 */

document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const routerGrid = document.getElementById("router-grid");
    const badgeTotalNodes = document.getElementById("badge-total-nodes");
    
    // Left Navigation Drawer Elements
    const navDrawer = document.getElementById("nav-drawer");
    const sidebarBackdrop = document.getElementById("sidebar-backdrop");
    const btnToggleSidebar = document.getElementById("btn-toggle-sidebar");
    const btnCloseSidebar = document.getElementById("btn-close-sidebar");

    // Right Command Console Side-Sheet Elements
    const consoleDrawer = document.getElementById("console-drawer");
    const consoleBackdrop = document.getElementById("console-backdrop");
    const btnOpenConsoleDrawer = document.getElementById("btn-open-console-drawer");
    const btnCloseConsoleDrawer = document.getElementById("btn-close-console-drawer");

    // Console Controls
    const labelSelectedName = document.getElementById("label-selected-name");
    const labelSelectedMeta = document.getElementById("label-selected-meta");
    const btnRunSnmp = document.getElementById("btn-run-snmp");
    
    const btnPowerUp = document.getElementById("cmd-power-up");
    const btnPowerDown = document.getElementById("cmd-power-down");
    const btnReboot = document.getElementById("cmd-reboot");
    const btnBgpReset = document.getElementById("cmd-bgp-reset");
    const btnTraffic = document.getElementById("cmd-traffic");
    const btnRedeploy = document.getElementById("cmd-redeploy");
    const btnFailMode = document.getElementById("cmd-fail-mode");
    const labelFailModeText = document.getElementById("label-fail-mode-text");
    
    const selectLedTarget = document.getElementById("select-led-target");
    const selectLedColor = document.getElementById("select-led-color");
    const btnApplyLed = document.getElementById("btn-apply-led");
    const terminalOutput = document.getElementById("terminal-output");
    const btnClearTerminal = document.getElementById("btn-clear-terminal");

    // Modal Elements
    const btnOpenAddModal = document.getElementById("btn-open-add-modal");
    const btnCloseModal = document.getElementById("btn-close-modal");
    const btnCancelModal = document.getElementById("btn-cancel-modal");
    const modalAddRouter = document.getElementById("modal-add-router");
    const formAddRouter = document.getElementById("form-add-router");

    let routerList = [];
    let selectedRouter = null;

    /**
     * Navigation Drawer Controls (Left)
     */
    function openNavDrawer() {
        if (navDrawer) navDrawer.classList.add("open");
        if (sidebarBackdrop) sidebarBackdrop.classList.add("active");
    }

    function closeNavDrawer() {
        if (navDrawer) navDrawer.classList.remove("open");
        if (sidebarBackdrop) sidebarBackdrop.classList.remove("active");
    }

    if (btnToggleSidebar) btnToggleSidebar.addEventListener("click", openNavDrawer);
    if (btnCloseSidebar) btnCloseSidebar.addEventListener("click", closeNavDrawer);
    if (sidebarBackdrop) sidebarBackdrop.addEventListener("click", closeNavDrawer);

    const toggleConsoleIcon = document.getElementById("toggle-console-icon");
    const btnToggleConsoleDrawer = document.getElementById("btn-toggle-console-drawer");
    const railCollapsedView = document.querySelector(".rail-collapsed-view");

    /**
     * Right Docked Command Console Sidebar Controls
     */
    function openConsoleDrawer() {
        if (consoleDrawer) consoleDrawer.classList.add("open");
        if (consoleBackdrop) consoleBackdrop.classList.add("active");
        if (toggleConsoleIcon) toggleConsoleIcon.textContent = "chevron_right";
    }

    function closeConsoleDrawer() {
        if (consoleDrawer) consoleDrawer.classList.remove("open");
        if (consoleBackdrop) consoleBackdrop.classList.remove("active");
        if (toggleConsoleIcon) toggleConsoleIcon.textContent = "chevron_left";
    }

    function toggleConsoleDrawer() {
        if (consoleDrawer && consoleDrawer.classList.contains("open")) {
            closeConsoleDrawer();
        } else {
            openConsoleDrawer();
        }
    }

    if (btnToggleConsoleDrawer) btnToggleConsoleDrawer.addEventListener("click", (e) => { e.stopPropagation(); toggleConsoleDrawer(); });
    if (railCollapsedView) railCollapsedView.addEventListener("click", openConsoleDrawer);
    if (btnCloseConsoleDrawer) btnCloseConsoleDrawer.addEventListener("click", closeConsoleDrawer);
    if (consoleBackdrop) consoleBackdrop.addEventListener("click", closeConsoleDrawer);

    let isMultiSelectMode = false;
    const selectedRouterIds = new Set();
    const btnToggleSelectMode = document.getElementById("btn-toggle-select-mode");
    const iconSelectMode = document.getElementById("icon-select-mode");
    const labelSelectModeText = document.getElementById("label-select-mode-text");

    // Escape Key listener for drawers and modals
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            closeConsoleDrawer();
            closeNavDrawer();
            if (modalAddRouter) modalAddRouter.classList.add("hidden");
        }
    });

    /**
     * Updates control console button state based on router selection or multi-select collection
     */
    function updateConsoleControlsState() {
        const isMulti = isMultiSelectMode && selectedRouterIds.size > 0;
        const hasSelection = isMulti || selectedRouter !== null;
        
        [btnPowerUp, btnPowerDown, btnReboot, btnBgpReset, btnTraffic, btnFailMode, selectLedTarget, selectLedColor, btnApplyLed].forEach(el => {
            if (el) el.disabled = !hasSelection;
        });

        if (btnRunSnmp) btnRunSnmp.disabled = isMulti || !selectedRouter;
        if (btnRedeploy) btnRedeploy.disabled = !hasSelection;

        if (selectedRouter && btnFailMode) {
            if (selectedRouter.fail_mode) {
                btnFailMode.classList.add("active");
                btnFailMode.setAttribute("data-action-label", "Disable Fail Mode");
                btnFailMode.setAttribute("data-action-desc", "Turns off automated 5-minute BGP fault injection");
                btnFailMode.title = "Disable Fail Mode: Stop automated BGP fault injection";
            } else {
                btnFailMode.classList.remove("active");
                btnFailMode.setAttribute("data-action-label", "Enable Fail Mode");
                btnFailMode.setAttribute("data-action-desc", "Injects automated BGP fault every 5 minutes");
                btnFailMode.title = "Enable Fail Mode: Inject automated BGP fault every 5 minutes";
            }
        }

        if (isMulti) {
            const idList = Array.from(selectedRouterIds);
            if (labelSelectedName) labelSelectedName.textContent = `MULTI-ROUTER CONTROL (${idList.length} Selected)`;
            if (labelSelectedMeta) labelSelectedMeta.textContent = `Targeting: ${idList.join(", ")}`;
        } else if (selectedRouter) {
            if (labelSelectedName) labelSelectedName.textContent = selectedRouter.name;
            if (labelSelectedMeta) labelSelectedMeta.textContent = `ID: ${selectedRouter.id} | ${selectedRouter.location}`;
        } else {
            if (labelSelectedName) labelSelectedName.textContent = "No Router Selected";
            if (labelSelectedMeta) labelSelectedMeta.textContent = "Select a router card or enable Multi-Select mode";
        }
    }

    // In-memory per-router isolated log buffer map
    const routerLogsMap = new Map();
    const SYSTEM_LOG_KEY = "__system__";

    /**
     * Appends a log line to a router's isolated log buffer and updates live terminal output if active
     * @param {string} message Message line text
     * @param {string} prefix Log severity label (INFO, COMMAND, SUCCESS, ERROR)
     * @param {string|null} routerId Target router ID string, or null to target currently selected router
     */
    function appendTerminalLog(message, prefix = "INFO", routerId = null) {
        const targetId = routerId || (selectedRouter ? selectedRouter.id : SYSTEM_LOG_KEY);

        if (!routerLogsMap.has(targetId)) {
            routerLogsMap.set(targetId, []);
        }

        const logItem = {
            time: new Date().toLocaleTimeString(),
            prefix: prefix,
            message: message
        };

        const logList = routerLogsMap.get(targetId);
        logList.push(logItem);
        if (logList.length > 200) logList.shift();

        // Render line immediately if target matches current selection
        const activeId = selectedRouter ? selectedRouter.id : SYSTEM_LOG_KEY;
        if (targetId === activeId) {
            renderSingleTerminalLine(logItem);
        }
    }

    /**
     * Renders full terminal log buffer for currently selected router or system default
     */
    function renderTerminalForActiveSelection() {
        if (!terminalOutput) return;
        terminalOutput.replaceChildren();

        const activeId = selectedRouter ? selectedRouter.id : SYSTEM_LOG_KEY;
        const logs = routerLogsMap.get(activeId) || [];

        if (logs.length === 0) {
            const emptyLine = document.createElement("div");
            emptyLine.className = "terminal-line";
            const displayName = selectedRouter ? selectedRouter.name : "System";
            emptyLine.innerHTML = `<span class="term-time">[System]</span> Execution log buffer ready for ${displayName}. Dispatch operational commands to view log activity.`;
            terminalOutput.appendChild(emptyLine);
            return;
        }

        logs.forEach(logItem => renderSingleTerminalLine(logItem));
    }

    /**
     * Appends a single formatted log line element to terminal box
     */
    function renderSingleTerminalLine(logItem) {
        if (!terminalOutput) return;

        const line = document.createElement("div");
        line.className = "terminal-line";

        const timeSpan = document.createElement("span");
        timeSpan.className = "term-time";
        timeSpan.textContent = `[${logItem.time}] [${logItem.prefix}]`;

        const textSpan = document.createElement("span");
        textSpan.textContent = " " + logItem.message;

        line.appendChild(timeSpan);
        line.appendChild(textSpan);
        terminalOutput.appendChild(line);

        terminalOutput.scrollTop = terminalOutput.scrollHeight;
    }

    /**
     * Maps LED state name to CSS glow class safely, applying variable animation timing per router node
     */
    function setLedElementState(elem, state, routerId = "") {
        if (!elem) return;
        elem.className = "led-indicator";
        const st = (state || "off").toLowerCase();
        
        elem.style.animationDuration = "";
        elem.style.animationDelay = "";

        if (st === "green") elem.classList.add("led-green");
        else if (st === "amber") elem.classList.add("led-amber");
        else if (st === "red") elem.classList.add("led-red");
        else if (st === "flash" || st === "flash_fast") {
            const isFast = st === "flash_fast";
            elem.classList.add(isFast ? "led-amber" : "led-green", isFast ? "led-flash-fast" : "led-flash");

            if (routerId) {
                // Compute deterministic unique hash from router ID + element ID for distinct blink rates
                let hash = 0;
                const seedStr = `${routerId}-${elem.id}`;
                for (let i = 0; i < seedStr.length; i++) {
                    hash = (hash << 5) - hash + seedStr.charCodeAt(i);
                    hash |= 0;
                }
                const base = isFast ? 0.22 : 0.75;
                const duration = base + (((Math.abs(hash) % 40) - 20) / 100);
                const delay = ((Math.abs(hash) % 60) / 100);

                elem.style.animationDuration = `${duration.toFixed(2)}s`;
                elem.style.animationDelay = `${delay.toFixed(2)}s`;
            }
        } else {
            elem.classList.add("led-off");
        }
    }

    const badgeNodesCount = document.getElementById("badge-nodes-count");

    /**
     * Formats an ISO 8601 deployment timestamp into a clean localized date and time string
     */
    function formatDeployedTime(isoStr) {
        if (!isoStr) return "N/A (Local)";
        try {
            const d = new Date(isoStr);
            if (isNaN(d.getTime())) return isoStr;
            return d.toLocaleString(undefined, {
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        } catch {
            return isoStr;
        }
    }

    /**
     * Formats a Cloud Run revision string into a compact identifier (e.g. 00010-fpg)
     */
    function formatRevision(rev) {
        if (!rev) return "N/A";
        const parts = rev.split("-");
        if (parts.length >= 2) {
            return parts.slice(-2).join("-");
        }
        return rev;
    }

    /**
     * Constructs a single LED indicator group component safely
     */
    function createLedGroup(id, labelText) {
        const grp = document.createElement("div");
        grp.className = "card-led-group";

        const ind = document.createElement("div");
        ind.className = "led-indicator";
        ind.id = id;
        ind.setAttribute("aria-label", `${labelText} LED indicator`);

        const lbl = document.createElement("span");
        lbl.className = "led-label";
        lbl.textContent = labelText;

        grp.appendChild(ind);
        grp.appendChild(lbl);
        return grp;
    }

    /**
     * Renders multi-router fleet grid cards with native embedded hardware visualizers
     */
    function renderRouterGrid(routers) {
        if (!routerGrid) return;
        routerGrid.replaceChildren();

        if (badgeNodesCount) {
            badgeNodesCount.textContent = `${routers.length}`;
        } else if (badgeTotalNodes) {
            badgeTotalNodes.textContent = `${routers.length}`;
        }

        if (routers.length === 0) {
            const emptyMsg = document.createElement("div");
            emptyMsg.className = "sub-text";
            emptyMsg.textContent = "No router nodes registered. Click '+ Register Router' above to add a router node.";
            routerGrid.appendChild(emptyMsg);
            return;
        }

        routers.forEach(router => {
            const card = document.createElement("div");
            card.className = "router-card";
            card.id = `router-card-${router.id}`;
            card.setAttribute("role", "article");
            card.setAttribute("tabindex", "0");
            card.setAttribute("aria-label", `Router card for ${router.name} (${router.id}) in ${router.location}`);

            if (isMultiSelectMode) {
                if (selectedRouterIds.has(router.id)) {
                    card.classList.add("selected");
                    card.setAttribute("aria-selected", "true");
                }
            } else if (selectedRouter && selectedRouter.id === router.id) {
                card.classList.add("selected");
                card.setAttribute("aria-selected", "true");
            } else {
                card.setAttribute("aria-selected", "false");
            }

            // Top Header Bar
            const topBar = document.createElement("div");
            topBar.className = "card-top";

            if (isMultiSelectMode) {
                const chkWrap = document.createElement("div");
                chkWrap.className = "card-select-checkbox-wrapper";

                const chk = document.createElement("input");
                chk.type = "checkbox";
                chk.className = "card-select-checkbox";
                chk.checked = selectedRouterIds.has(router.id);
                chk.title = `Select ${router.name}`;
                chk.setAttribute("aria-label", `Select router ${router.name}`);

                chk.addEventListener("change", (e) => {
                    e.stopPropagation();
                    if (chk.checked) {
                        selectedRouterIds.add(router.id);
                        card.classList.add("selected");
                        card.setAttribute("aria-selected", "true");
                        openConsoleDrawer();
                    } else {
                        selectedRouterIds.delete(router.id);
                        card.classList.remove("selected");
                        card.setAttribute("aria-selected", "false");
                    }
                    updateConsoleControlsState();
                });

                chkWrap.appendChild(chk);
                topBar.appendChild(chkWrap);
            }

            const titleGroup = document.createElement("div");
            titleGroup.className = "card-title-group";

            const rName = document.createElement("div");
            rName.className = "router-name";
            rName.textContent = router.name;

            const rMeta = document.createElement("div");
            rMeta.className = "router-meta";
            rMeta.textContent = `${router.id} • ${router.location}`;

            titleGroup.appendChild(rName);
            titleGroup.appendChild(rMeta);

            const cardActions = document.createElement("div");
            cardActions.className = "card-actions";

            const launchBtn = document.createElement("button");
            launchBtn.className = "btn-card-launch";
            launchBtn.title = `Launch Command Console for ${router.name}`;
            launchBtn.setAttribute("aria-label", `Launch Command Console for ${router.name}`);
            launchBtn.innerHTML = `<span class="material-symbols-outlined" style="font-size: 14px;" aria-hidden="true">terminal</span> Console`;
            launchBtn.addEventListener("click", (e) => {
                e.stopPropagation();
                toggleRouterNodeSelection(router);
            });

            const redeployBtn = document.createElement("button");
            redeployBtn.className = "btn-card-launch";
            redeployBtn.style.background = "#0284c7";
            redeployBtn.title = `Redeploy ${router.name} instance to Cloud Run`;
            redeployBtn.setAttribute("aria-label", `Redeploy ${router.name} instance to Cloud Run`);
            redeployBtn.innerHTML = `<span class="material-symbols-outlined" style="font-size: 14px;" aria-hidden="true">cloud_sync</span>`;
            redeployBtn.addEventListener("click", (e) => {
                e.stopPropagation();
                redeployRouterNode(router);
            });
            const editBtn = document.createElement("button");
            editBtn.className = "icon-button";
            editBtn.style.cssText = "width: 28px; height: 28px; color: var(--md-sys-color-primary);";
            editBtn.title = `Edit Router Settings for ${router.name}`;
            editBtn.setAttribute("aria-label", `Edit Router Settings for ${router.name}`);
            editBtn.innerHTML = `<span class="material-symbols-outlined" style="font-size: 16px;" aria-hidden="true">edit</span>`;
            editBtn.addEventListener("click", (e) => {
                e.stopPropagation();
                openEditModal(router);
            });

            const delBtn = document.createElement("button");
            delBtn.className = "icon-button";
            delBtn.style.cssText = "width: 28px; height: 28px; color: #ef4444;";
            delBtn.title = `Delete Router ${router.id} Registration`;
            delBtn.setAttribute("aria-label", `Delete Router ${router.id} Registration`);
            delBtn.innerHTML = `<span class="material-symbols-outlined" style="font-size: 16px;" aria-hidden="true">delete</span>`;
            delBtn.addEventListener("click", (e) => {
                e.stopPropagation();
                deleteRouter(router.id);
            });

            cardActions.appendChild(launchBtn);
            cardActions.appendChild(redeployBtn);
            cardActions.appendChild(editBtn);
            cardActions.appendChild(delBtn);
            topBar.appendChild(titleGroup);
            topBar.appendChild(cardActions);

            // Native Embedded Chassis Bezel Box Component
            const bezel = document.createElement("div");
            bezel.className = "card-chassis-bezel";

            // LCD Display Component
            const lcd = document.createElement("div");
            lcd.className = "card-lcd-display";

            const r1 = document.createElement("div");
            r1.className = "lcd-row";
            const l1 = document.createElement("span");
            l1.className = "lcd-label";
            l1.textContent = "DEVICE:";
            const v1 = document.createElement("span");
            v1.className = "lcd-val";
            v1.textContent = router.id;
            r1.appendChild(l1);
            r1.appendChild(v1);

            const r2 = document.createElement("div");
            r2.className = "lcd-row";
            const l2 = document.createElement("span");
            l2.className = "lcd-label";
            l2.textContent = "UPTIME:";
            const v2 = document.createElement("span");
            v2.className = "lcd-val";
            v2.id = `lcd-uptime-${router.id}`;
            v2.textContent = "...";

            const l3 = document.createElement("span");
            l3.className = "lcd-label";
            l3.textContent = "STATE:";
            const v3 = document.createElement("span");
            v3.className = "lcd-val highlights";
            v3.id = `lcd-state-${router.id}`;
            v3.textContent = "CONNECTING";

            r2.appendChild(l2);
            r2.appendChild(v2);
            r2.appendChild(l3);
            r2.appendChild(v3);

            const r3 = document.createElement("div");
            r3.className = "lcd-row";
            const l4 = document.createElement("span");
            l4.className = "lcd-label";
            l4.textContent = "MFG/MODEL:";
            const v4 = document.createElement("span");
            v4.className = "lcd-val";
            v4.textContent = `${router.manufacturer || 'Cisco'} ${router.model || 'Nexus 9300'}`;

            const l5 = document.createElement("span");
            l5.className = "lcd-label";
            l5.textContent = "UPDATED:";
            const v5 = document.createElement("span");
            v5.className = "lcd-val";
            v5.id = `lcd-updated-${router.id}`;
            v5.textContent = router.last_updated || new Date().toLocaleTimeString();

            r3.appendChild(l4);
            r3.appendChild(v4);
            r3.appendChild(l5);
            r3.appendChild(v5);

            const r4 = document.createElement("div");
            r4.className = "lcd-row";
            const l6 = document.createElement("span");
            l6.className = "lcd-label";
            l6.textContent = "DEPLOYED:";
            const v6 = document.createElement("span");
            v6.className = "lcd-val highlights";
            v6.id = `lcd-deployed-${router.id}`;
            v6.textContent = formatDeployedTime(router.last_deployed);

            const l7 = document.createElement("span");
            l7.className = "lcd-label";
            l7.textContent = "REV:";
            const v7 = document.createElement("span");
            v7.className = "lcd-val highlights";
            v7.id = `lcd-revision-${router.id}`;
            v7.textContent = formatRevision(router.revision);
            v7.title = router.revision || "No active Cloud Run revision tag";

            r4.appendChild(l6);
            r4.appendChild(v6);
            r4.appendChild(l7);
            r4.appendChild(v7);

            lcd.appendChild(r1);
            lcd.appendChild(r2);
            lcd.appendChild(r3);
            lcd.appendChild(r4);

            // LED Panel Component
            const ledPanel = document.createElement("div");
            ledPanel.className = "card-led-panel";

            ledPanel.appendChild(createLedGroup(`led-power-${router.id}`, "PWR"));
            ledPanel.appendChild(createLedGroup(`led-online-${router.id}`, "ONLINE"));
            ledPanel.appendChild(createLedGroup(`led-upstream-${router.id}`, "UPSTREAM"));

            const div1 = document.createElement("div");
            div1.className = "led-divider";
            ledPanel.appendChild(div1);

            ledPanel.appendChild(createLedGroup(`led-lan1-${router.id}`, "LAN1"));
            ledPanel.appendChild(createLedGroup(`led-lan2-${router.id}`, "LAN2"));
            ledPanel.appendChild(createLedGroup(`led-lan3-${router.id}`, "LAN3"));
            ledPanel.appendChild(createLedGroup(`led-lan4-${router.id}`, "LAN4"));

            const div2 = document.createElement("div");
            div2.className = "led-divider";
            ledPanel.appendChild(div2);

            ledPanel.appendChild(createLedGroup(`led-send-${router.id}`, "SEND"));
            ledPanel.appendChild(createLedGroup(`led-receive-${router.id}`, "RECV"));

            // Bezel Controls
            const bezelControls = document.createElement("div");
            bezelControls.className = "card-bezel-controls";

            const pwrBtn = document.createElement("button");
            pwrBtn.className = "card-bezel-btn";
            pwrBtn.title = "Power On/Off Router";
            pwrBtn.textContent = "PWR";
            pwrBtn.addEventListener("click", (e) => {
                e.stopPropagation();
                selectRouterNode(router);
                dispatchDirectCommand(router, "power_up");
            });

            const rstBtn = document.createElement("button");
            rstBtn.className = "card-bezel-btn";
            rstBtn.title = "Reboot Router";
            rstBtn.textContent = "RST";
            rstBtn.addEventListener("click", (e) => {
                e.stopPropagation();
                selectRouterNode(router);
                dispatchDirectCommand(router, "reset");
            });

            bezelControls.appendChild(pwrBtn);
            bezelControls.appendChild(rstBtn);

            bezel.appendChild(lcd);
            bezel.appendChild(ledPanel);
            bezel.appendChild(bezelControls);

            card.appendChild(topBar);
            card.appendChild(bezel);

            // Card click selection event
            card.addEventListener("click", () => {
                toggleRouterNodeSelection(router);
            });

            routerGrid.appendChild(card);
        });

        // Trigger immediate telemetry poll
        pollAllRouterTelemetry();
    }

    /**
     * Toggles selected router node state (selects if unselected, deselects if clicked again)
     */
    function toggleRouterNodeSelection(router) {
        if (selectedRouter && selectedRouter.id === router.id) {
            selectedRouter = null;
            document.querySelectorAll(".router-card").forEach(c => c.classList.remove("selected"));
            updateConsoleControlsState();
            renderTerminalForActiveSelection();
            closeConsoleDrawer();
        } else {
            selectRouterNode(router);
            openConsoleDrawer();
        }
    }

    /**
     * Sets selected router node and updates UI elements
     */
    function selectRouterNode(router) {
        selectedRouter = router;
        document.querySelectorAll(".router-card").forEach(c => c.classList.remove("selected"));
        const activeCard = document.getElementById(`router-card-${router.id}`);
        if (activeCard) activeCard.classList.add("selected");
        updateConsoleControlsState();
        renderTerminalForActiveSelection();
        appendTerminalLog(`Selected router node '${router.name}' (${router.id})`, "SELECTION");
    }

    /**
     * Polls status telemetry for all registered router cards dynamically
     */
    async function pollAllRouterTelemetry() {
        if (!Array.isArray(routerList) || routerList.length === 0) return;

        routerList.forEach(async (router) => {
            const turnOffLeds = () => {
                ["power", "online", "upstream", "lan1", "lan2", "lan3", "lan4", "send", "receive"].forEach(ledKey => {
                    const ledElem = document.getElementById(`led-${ledKey}-${router.id}`);
                    setLedElementState(ledElem, "off", router.id);
                });
            };

            try {
                const res = await fetch(`/api/proxy/status?router_id=${encodeURIComponent(router.id)}`);
                if (!res.ok) {
                    const stateElem = document.getElementById(`lcd-state-${router.id}`);
                    if (stateElem) {
                        stateElem.textContent = "OFFLINE";
                        stateElem.className = "lcd-val status-offline";
                    }
                    turnOffLeds();
                    return;
                }
                const data = await res.json();

                const uptimeElem = document.getElementById(`lcd-uptime-${router.id}`);
                const stateElem = document.getElementById(`lcd-state-${router.id}`);
                const updatedElem = document.getElementById(`lcd-updated-${router.id}`);

                if (updatedElem) {
                    updatedElem.textContent = new Date().toLocaleTimeString();
                }

                if (data.telemetry) {
                    if (uptimeElem) uptimeElem.textContent = `${data.telemetry.uptime_seconds || 0}s`;
                    if (stateElem) {
                        stateElem.textContent = data.telemetry.status || "UNKNOWN";
                        if (data.telemetry.status === "OFFLINE" || data.telemetry.status === "BGP_FAULT") {
                            stateElem.className = "lcd-val status-offline";
                        } else {
                            stateElem.className = "lcd-val highlights";
                        }
                    }
                    if (selectedRouter && router.id === selectedRouter.id) {
                        selectedRouter.fail_mode = !!data.telemetry.fail_mode;
                        updateConsoleControlsState();
                    }
                }

                if (data.leds) {
                    Object.keys(data.leds).forEach(ledKey => {
                        const ledElem = document.getElementById(`led-${ledKey}-${router.id}`);
                        setLedElementState(ledElem, data.leds[ledKey], router.id);
                    });
                }
            } catch (err) {
                const stateElem = document.getElementById(`lcd-state-${router.id}`);
                if (stateElem) {
                    stateElem.textContent = "OFFLINE";
                    stateElem.className = "lcd-val status-offline";
                }
                turnOffLeds();
            }
        });
    }

    /**
     * Fetches registered router nodes list from backend
     */
    async function fetchRouters() {
        try {
            const res = await fetch("/api/routers");
            if (!res.ok) return;
            const data = await res.json();
            routerList = data.routers || [];
            
            // Retain selection if valid
            if (selectedRouter) {
                selectedRouter = routerList.find(r => r.id === selectedRouter.id) || null;
            }

            renderRouterGrid(routerList);
            updateConsoleControlsState();
        } catch (err) {
            appendTerminalLog(`Error loading router registry: ${err.message}`, "ERROR");
        }
    }

    /**
     * Surgically updates ONLY the target router card's LCD deployment metadata without re-rendering the grid
     */
    async function refreshSingleRouterMetadata(routerId) {
        if (!routerId) return;
        try {
            const res = await fetch("/api/routers");
            if (!res.ok) return;
            const data = await res.json();
            const routers = data.routers || [];
            const target = routers.find(r => r.id === routerId);
            if (!target) return;

            const idx = routerList.findIndex(r => r.id === routerId);
            const prevRev = idx !== -1 ? routerList[idx].revision : "";

            // Sync target in global routerList without re-rendering DOM grid
            if (idx !== -1) {
                routerList[idx] = target;
            }

            const depElem = document.getElementById(`lcd-deployed-${routerId}`);
            if (depElem) {
                depElem.textContent = formatDeployedTime(target.last_deployed);
            }

            const revElem = document.getElementById(`lcd-revision-${routerId}`);
            if (revElem) {
                revElem.textContent = formatRevision(target.revision);
                revElem.title = target.revision || "No active Cloud Run revision tag";
            }

            if (prevRev && target.revision && prevRev !== target.revision) {
                appendTerminalLog(`Cloud Run deployment ready for '${routerId}'. New active revision: ${target.revision}`, "SUCCESS", routerId);
            }
        } catch (err) {
            console.warn(`Error refreshing metadata for router ${routerId}:`, err);
        }
    }

    /**
     * Dispatches command directly to specified router
     */
    async function dispatchDirectCommand(targetRouter, command, parameters = {}) {
        appendTerminalLog(`Sending '${command}' command to router '${targetRouter.name}'...`, "COMMAND");

        try {
            const res = await fetch("/api/proxy/command", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    router_id: targetRouter.id,
                    command,
                    parameters
                })
            });

            const data = await res.json();
            if (!res.ok) {
                appendTerminalLog(`Command Failed [${res.status}]: ${data.message || data.error}`, "ERROR");
            } else {
                const msg = data.message || data.status || "Command executed successfully";
                const isInitiated = msg.toLowerCase().includes("initiated") || msg.toLowerCase().includes("in progress");
                appendTerminalLog(`Result: ${msg}`, isInitiated ? "INFO" : "SUCCESS");
                pollAllRouterTelemetry();
            }
        } catch (err) {
            appendTerminalLog(`Network Error sending command: ${err.message}`, "ERROR");
        }
    }

    /**
     * Sends proxy command to targeted router or collection of routers via backend proxy
     */
    async function dispatchProxyCommand(command, parameters = {}) {
        if (isMultiSelectMode && selectedRouterIds.size > 0) {
            const targetIds = Array.from(selectedRouterIds);
            appendTerminalLog(`Dispatching batch '${command}' command to ${targetIds.length} routers (${targetIds.join(", ")})...`, "BATCH");

            try {
                const res = await fetch("/api/proxy/command", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        router_ids: targetIds,
                        command,
                        parameters
                    })
                });

                const data = await res.json();
                if (!res.ok) {
                    appendTerminalLog(`Batch Command Failed: ${data.message || data.error}`, "ERROR");
                } else {
                    appendTerminalLog(`Batch '${command}' executed across ${targetIds.length} nodes.`, "SUCCESS");
                    if (data.results) {
                        Object.keys(data.results).forEach(rId => {
                            const item = data.results[rId];
                            const msg = item.message || item.status || JSON.stringify(item);
                            appendTerminalLog(`[${rId}] ${msg}`, item.error ? "ERROR" : "SUCCESS", rId);
                        });
                    }
                    pollAllRouterTelemetry();
                }
            } catch (err) {
                appendTerminalLog(`Network Error during batch command execution: ${err.message}`, "ERROR");
            }
            return;
        }

        if (!selectedRouter) {
            alert("Please select a router node first or enable Multi-Select mode.");
            return;
        }
        dispatchDirectCommand(selectedRouter, command, parameters);
    }

    /**
     * Executes HTTP SNMP Walk query against selected router
     */
    async function dispatchSnmpWalk() {
        if (!selectedRouter) return;

        appendTerminalLog(`Executing SNMP Walk against '${selectedRouter.name}'...`, "SNMP");

        try {
            const res = await fetch(`/api/proxy/snmp?router_id=${encodeURIComponent(selectedRouter.id)}&format=text`);
            const text = await res.text();
            
            if (!res.ok) {
                appendTerminalLog(`SNMP Query Failed: ${text}`, "ERROR");
            } else {
                appendTerminalLog(`SNMP Walk Response:\n${text}`, "SNMP-DATA");
            }
        } catch (err) {
            appendTerminalLog(`SNMP Network Error: ${err.message}`, "ERROR");
        }
    }

    /**
     * Deletes a router registration from registry
     */
    async function deleteRouter(routerId) {
        if (!confirm(`Are you sure you want to remove router '${routerId}' from the dashboard?`)) return;

        try {
            const res = await fetch(`/api/routers/${encodeURIComponent(routerId)}`, { method: "DELETE" });
            if (res.ok) {
                if (selectedRouter && selectedRouter.id === routerId) {
                    selectedRouter = null;
                }
                fetchRouters();
            }
        } catch (err) {
            alert(`Failed deleting router: ${err.message}`);
        }
    }

    // Navigation Items
    const navOpenConsole = document.getElementById("nav-open-console");
    const navRefreshFleet = document.getElementById("nav-refresh-fleet");
    const navTriggerRegister = document.getElementById("nav-trigger-register");

    if (navOpenConsole) navOpenConsole.addEventListener("click", () => { closeNavDrawer(); openConsoleDrawer(); });
    if (navRefreshFleet) navRefreshFleet.addEventListener("click", () => { closeNavDrawer(); fetchRouters(); });
    if (navTriggerRegister) navTriggerRegister.addEventListener("click", () => { closeNavDrawer(); modalAddRouter.classList.remove("hidden"); });

    // Modal Form Logic
    if (btnOpenAddModal) btnOpenAddModal.addEventListener("click", () => modalAddRouter.classList.remove("hidden"));
    if (btnCloseModal) btnCloseModal.addEventListener("click", () => modalAddRouter.classList.add("hidden"));
    if (btnCancelModal) btnCancelModal.addEventListener("click", () => modalAddRouter.classList.add("hidden"));

    if (formAddRouter) {
        formAddRouter.addEventListener("submit", async (e) => {
            e.preventDefault();

            const checkDeploy = document.getElementById("check-deploy-cloudrun");
            const btnSubmit = document.getElementById("btn-submit-router");
            const isDeploying = checkDeploy && checkDeploy.checked;

            const payload = {
                id: document.getElementById("input-router-id").value.trim(),
                name: document.getElementById("input-router-name").value.trim(),
                url: document.getElementById("input-router-url").value.trim(),
                purpose: document.getElementById("input-router-purpose") ? document.getElementById("input-router-purpose").value.trim() : "Edge Core Router",
                location: document.getElementById("input-router-loc").value.trim(),
                control_password: document.getElementById("input-router-pass").value.trim(),
                control_header: "X-Control-Password",
                deploy_cloud_run: isDeploying,
                deploy_cloudrun: isDeploying
            };

            const origText = btnSubmit ? btnSubmit.textContent : "Register / Deploy Router";
            if (btnSubmit) {
                btnSubmit.disabled = true;
                btnSubmit.textContent = isDeploying ? "Deploying to Cloud Run..." : "Saving Router...";
            }

            try {
                appendTerminalLog(`Submitting router '${payload.id}' registration (Deploy Cloud Run: ${isDeploying})...`, "DEPLOY");

                const res = await fetch("/api/routers", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });

                const data = await res.json();
                if (res.ok) {
                    appendTerminalLog(`Successfully registered/deployed router '${payload.id}'. Endpoint: ${data.url || payload.url}`, "SUCCESS");
                    modalAddRouter.classList.add("hidden");
                    formAddRouter.reset();
                    fetchRouters();
                } else {
                    appendTerminalLog(`Registration/Deployment Failed: ${data.message || data.error}`, "ERROR");
                    alert(`Failed registering/deploying router: ${data.message || data.error}`);
                }
            } catch (err) {
                appendTerminalLog(`Network Error during registration: ${err.message}`, "ERROR");
                alert(`Error saving router: ${err.message}`);
            } finally {
                if (btnSubmit) {
                    btnSubmit.disabled = false;
                    btnSubmit.textContent = origText;
                }
            }
        });
    }

    /**
     * Triggers Cloud Run redeployment for a router node
     */
    /**
     * Triggers Cloud Run redeployment for a single router node or batch multi-selected collection
     */
    async function redeployRouterNode(targetRouter) {
        let targetIds = [];
        if (isMultiSelectMode && selectedRouterIds.size > 0) {
            targetIds = Array.from(selectedRouterIds);
        } else if (targetRouter) {
            targetIds = [targetRouter.id];
        } else {
            alert("Please select a router node to redeploy.");
            return;
        }

        if (!confirm(`Are you sure you want to redeploy ${targetIds.length} router node(s) (${targetIds.join(", ")}) to Cloud Run?`)) return;

        appendTerminalLog(`Triggering Cloud Run redeployment for ${targetIds.length} router node(s) (${targetIds.join(", ")})...`, "REDEPLOY");

        try {
            const res = await fetch("/api/proxy/redeploy", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ router_ids: targetIds })
            });

            const data = await res.json();
            if (res.ok) {
                appendTerminalLog(`Successfully completed Cloud Run redeployment for ${targetIds.length} node(s).`, "SUCCESS");
                if (data.results) {
                    Object.keys(data.results).forEach(rId => {
                        const item = data.results[rId];
                        if (item.status === "SUCCESS") {
                            appendTerminalLog(`[${rId}] Service URL: ${item.url}`, "SUCCESS", rId);
                        } else {
                            appendTerminalLog(`[${rId}] Redeployment Failed: ${item.message || item.error}`, "ERROR", rId);
                        }
                    });
                }
                alert(`Cloud Run redeployment succeeded for ${targetIds.length} node(s)!`);
                fetchRouters();
            } else {
                appendTerminalLog(`Redeployment Failed: ${data.message || data.error}`, "ERROR");
                alert(`Redeployment failed: ${data.message || data.error}`);
            }
        } catch (err) {
            appendTerminalLog(`Network Error during redeployment: ${err.message}`, "ERROR");
            alert(`Error triggering redeployment: ${err.message}`);
        }
    }

    // Modal Edit Router Controls
    const modalEditRouter = document.getElementById("modal-edit-router");
    const btnCloseEditModal = document.getElementById("btn-close-edit-modal");
    const btnCancelEditModal = document.getElementById("btn-cancel-edit-modal");
    const formEditRouter = document.getElementById("form-edit-router");

    if (btnCloseEditModal) btnCloseEditModal.addEventListener("click", () => modalEditRouter.classList.add("hidden"));
    if (btnCancelEditModal) btnCancelEditModal.addEventListener("click", () => modalEditRouter.classList.add("hidden"));

    function openEditModal(router) {
        if (!router || !modalEditRouter) return;
        document.getElementById("edit-router-id").value = router.id;
        document.getElementById("edit-router-name").value = router.name || "";
        document.getElementById("edit-router-loc").value = router.location || "";
        document.getElementById("edit-router-purpose").value = router.purpose || "";
        document.getElementById("edit-router-mfg").value = router.manufacturer || "Cisco Systems";
        document.getElementById("edit-router-model").value = router.model || "Nexus 9300-EX";
        document.getElementById("edit-router-pass").value = "";
        document.getElementById("check-edit-redeploy").checked = true;
        modalEditRouter.classList.remove("hidden");
    }

    if (formEditRouter) {
        formEditRouter.addEventListener("submit", async (e) => {
            e.preventDefault();

            const rId = document.getElementById("edit-router-id").value;
            const btnSubmit = document.getElementById("btn-submit-edit-router");
            const isRedeploying = document.getElementById("check-edit-redeploy").checked;

            const payload = {
                name: document.getElementById("edit-router-name").value.trim(),
                location: document.getElementById("edit-router-loc").value.trim(),
                purpose: document.getElementById("edit-router-purpose").value.trim(),
                manufacturer: document.getElementById("edit-router-mfg").value.trim(),
                model: document.getElementById("edit-router-model").value.trim(),
                control_password: document.getElementById("edit-router-pass").value.trim(),
                redeploy_cloud_run: isRedeploying
            };

            const origText = btnSubmit.textContent;
            btnSubmit.disabled = true;
            btnSubmit.textContent = isRedeploying ? "Saving & Redeploying..." : "Saving...";

            try {
                const res = await fetch(`/api/routers/${encodeURIComponent(rId)}`, {
                    method: "PUT",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });

                const data = await res.json();
                if (res.ok) {
                    modalEditRouter.classList.add("hidden");
                    if (isRedeploying) {
                        appendTerminalLog(`Router '${rId}' configuration updated. Cloud Run deployment in progress...`, "INFO", rId);
                        [4000, 8000, 12000, 16000, 20000, 25000].forEach(delay => {
                            setTimeout(() => refreshSingleRouterMetadata(rId), delay);
                        });
                    } else {
                        appendTerminalLog(`Successfully updated router '${rId}' settings.`, "SUCCESS", rId);
                        fetchRouters();
                    }
                } else {
                    appendTerminalLog(`Failed updating settings for '${rId}': ${data.message || data.error}`, "ERROR", rId);
                    alert(`Failed updating settings: ${data.message || data.error}`);
                }
            } catch (err) {
                appendTerminalLog(`Error updating router settings: ${err.message}`, "ERROR", rId);
                alert(`Error updating settings: ${err.message}`);
            } finally {
                btnSubmit.disabled = false;
                btnSubmit.textContent = origText;
            }
        });
    }

    if (btnToggleSelectMode) {
        btnToggleSelectMode.addEventListener("click", () => {
            isMultiSelectMode = !isMultiSelectMode;
            if (isMultiSelectMode) {
                btnToggleSelectMode.className = "md-button-tonal active";
                if (iconSelectMode) iconSelectMode.textContent = "close";
                if (labelSelectModeText) labelSelectModeText.textContent = "Done";
            } else {
                btnToggleSelectMode.className = "md-button-outlined";
                if (iconSelectMode) iconSelectMode.textContent = "checklist";
                if (labelSelectModeText) labelSelectModeText.textContent = "Select Routers";
                selectedRouterIds.clear();
            }
            renderRouterGrid(routerList);
            updateConsoleControlsState();
        });
    }

    // Control Event Listeners
    if (btnPowerUp) btnPowerUp.addEventListener("click", () => dispatchProxyCommand("power_up"));
    if (btnPowerDown) btnPowerDown.addEventListener("click", () => dispatchProxyCommand("power_down"));
    if (btnReboot) btnReboot.addEventListener("click", () => dispatchProxyCommand("reset"));
    if (btnBgpReset) btnBgpReset.addEventListener("click", () => dispatchProxyCommand("bgp_reset"));
    if (btnTraffic) btnTraffic.addEventListener("click", () => dispatchProxyCommand("send_info"));
    if (btnFailMode) {
        btnFailMode.addEventListener("click", () => {
            const currentMode = selectedRouter ? !!selectedRouter.fail_mode : false;
            const newMode = !currentMode;
            dispatchProxyCommand("set_fail_mode", { enabled: newMode });
            if (selectedRouter) {
                selectedRouter.fail_mode = newMode;
                updateConsoleControlsState();
            }
        });
    }
    if (btnRedeploy) btnRedeploy.addEventListener("click", () => redeployRouterNode(selectedRouter));

    if (btnApplyLed) {
        btnApplyLed.addEventListener("click", () => {
            const led = selectLedTarget ? selectLedTarget.value : "power";
            const color = selectLedColor ? selectLedColor.value : "green";
            dispatchProxyCommand("set_led", { led, color });
        });
    }

    if (btnRunSnmp) btnRunSnmp.addEventListener("click", dispatchSnmpWalk);

    if (btnClearTerminal) {
        btnClearTerminal.addEventListener("click", () => {
            const activeId = selectedRouter ? selectedRouter.id : SYSTEM_LOG_KEY;
            routerLogsMap.set(activeId, []);
            renderTerminalForActiveSelection();
        });
    }

    // Material 3 Icon Button Hover & Focus Action Preview Badge Logic
    const actionPreviewIcon = document.getElementById("action-preview-icon");
    const actionPreviewText = document.getElementById("action-preview-text");

    document.querySelectorAll(".m3-icon-btn").forEach(btn => {
        const updatePreview = () => {
            const label = btn.getAttribute("data-action-label") || "Action";
            const desc = btn.getAttribute("data-action-desc") || "";
            const iconElem = btn.querySelector("span.material-symbols-outlined");
            const iconName = iconElem ? iconElem.textContent : "touch_app";

            if (actionPreviewIcon) actionPreviewIcon.textContent = iconName;
            if (actionPreviewText) actionPreviewText.innerHTML = `<strong>${label}</strong> — ${desc}`;
        };

        const resetPreview = () => {
            if (actionPreviewIcon) actionPreviewIcon.textContent = "touch_app";
            if (actionPreviewText) actionPreviewText.textContent = "Hover or focus an icon to inspect action";
        };

        btn.addEventListener("mouseenter", updatePreview);
        btn.addEventListener("focus", updatePreview);
        btn.addEventListener("mouseleave", resetPreview);
        btn.addEventListener("blur", resetPreview);
    });

    // Initial load and periodic telemetry refresh
    fetchRouters();
    const intervalMs = window.POLLING_INTERVAL_MS || 1500;
    setInterval(pollAllRouterTelemetry, intervalMs);
});
