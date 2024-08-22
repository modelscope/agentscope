var serversTable;
var agentsTable;
var agentMemoryTable;
var curServerId;
var curAgentId;
var messageEditor;

// Sever table functions

function deleteServer(row) {
    fetch("/api/servers/delete", {
        method: "POST",
        headers: {
            "Content-Type": "application/json; charset=utf-8",
        },
        body: JSON.stringify({
            server_id: row.getData().id,
            stop: row.getData().status == "running",
        }),
    })
        .then((response) => {
            if (!response.ok) {
                throw new Error("Failed to delete server");
            }
            return response.json();
        })
        .then((data) => {
            row.delete();
        });
}

function deleteServerBtn(e, cell) {
    const serverId = cell.getData().id;
    if (confirm(`Are you sure to stop server ${serverId} ?`)) {
        deleteServer(cell.getRow());
    }
}

function newServer() {
    console.log("new Server");
}

function flushServerTable(data) {
    if (serversTable) {
        serversTable.setData(data);
        console.log("Flush Server Table");
    } else {
        console.error("Server Table is not initialized.");
    }
}

function deleteDeadServer() {
    let deadServerIds = [];
    if (serversTable) {
        let rows = serversTable.getRows();
        for (let i = 0; i < rows.length; i++) {
            let row = rows[i];
            if (row.getData().status == "dead") {
                deadServerIds.push(row.getData().id);
                deleteServer(row);
            }
        }
    } else {
        console.error("Server Table is not initialized.");
    }
    console.log("Delete dead servers: ", deadServerIds);
    return deadServerIds;
}

function deleteIcon(cell, formatterParams, onRendered) {
    return '<img src="/static/svg/trash-bin.svg" class="icon cell-btn"/>';
}

function getServerStatus(cell, formatterParams, onRendered) {
    cell.getElement().innerHTML =
        '<div class="status-tag loading">loading</div>';

    const serverId = cell.getRow().getData().id;

    fetch(`/api/servers/status/${serverId}`)
        .then((response) => {
            if (!response.ok) {
                throw new Error("Failed to get server status");
            }
            return response.json();
        })
        .then((data) => {
            let row = cell.getRow();
            if (data.status == "running") {
                cell.getElement().innerHTML =
                    '<div class="status-tag running">running</div>';
                row.update({
                    status: data.status,
                    cpu: data.cpu,
                    mem: data.mem,
                    size: data.size,
                });
            } else {
                cell.getElement().innerHTML =
                    '<div class="status-tag dead">dead</div>';
                row.update({
                    status: "dead",
                });
            }
        })
        .catch((error) => {
            console.error("Error fetching server status:", error);
            cell.getElement().innerHTML =
                '<div class="status-tag unknown">unknown</div>';
        });
}

function cpuUsage(cell, formatterParams, onRendered) {
    const cpu = cell.getData().cpu;
    if (!cpu && cpu !== 0) {
        return '<div class="status-tag unknown">unknown</div>';
    } else {
        return `<div class="status-tag running">${cell.getData().cpu} %</div>`;
    }
}

function memoryUsage(cell, formatterParams, onRendered) {
    if (cell.getData().mem) {
        return `<div class="status-tag running">${cell
            .getData()
            .mem.toFixed(2)} MB</div>`;
    } else {
        return '<div class="status-tag unknown">unknown</div>';
    }
}

function getServerTableData(callback) {
    fetch("/api/servers/all")
        .then((response) => {
            if (!response.ok) {
                throw new Error("Failed to fetch servers data");
            }
            return response.json();
        })
        .then((data) => {
            callback(data);
        });
}

function initServerTable(data) {
    serversTable = new Tabulator("#server-table", {
        data: data,
        columns: [
            {
                title: "",
                field: "status",
                vertAlign: "middle",
                visible: false,
            },
            {
                title: "ID",
                field: "id",
                vertAlign: "middle",
            },
            {
                title: "Host",
                field: "host",
                vertAlign: "middle",
            },
            {
                title: "Port",
                field: "port",
                vertAlign: "middle",
            },
            {
                title: "Created Time",
                field: "create_time",
                vertAlign: "middle",
            },
            {
                title: "Status",
                vertAlign: "middle",
                formatter: getServerStatus,
            },
            {
                title: "Agent Number",
                field: "size",
                vertAlign: "middle",
            },
            {
                title: "CPU Usage",
                field: "cpu",
                vertAlign: "middle",
                formatter: cpuUsage,
            },
            {
                title: "Memory Usage",
                field: "mem",
                vertAlign: "middle",
                formatter: memoryUsage,
            },
            {
                title: "Delete",
                formatter: deleteIcon,
                width: 75,
                vertAlign: "middle",
                cellClick: deleteServerBtn,
            },
        ],
        layout: "fitColumns",
    });
    serversTable.on("rowClick", function (e, row) {
        if (row.getData().status != "running") {
            return;
        }
        if (e.target.classList.contains("cell-btn")) {
            return;
        }
        loadAgentDetails(row.getData());
    });
}

// Agent table functions

function getAgentTableData(serverId, callback) {
    fetch(`/api/servers/agent_info/${serverId}`)
        .then((response) => {
            if (!response.ok) {
                throw new Error("Failed to fetch agents data");
            }
            return response.json();
        })
        .then((data) => {
            callback(serverId, data);
        });
}

function flushAgentTable(serverId, data) {
    if (agentsTable) {
        agentsTable.setData(data);
        console.log("Flush Agent Table");
    } else {
        console.error("Agent Table is not initialized.");
    }
}

function deleteAllAgent() {
    let serverId = curServerId;
    if (agentsTable) {
        if (confirm(`Are you sure to delete all agent on ${serverId} ?`)) {
            fetch(`/api/servers/agents/delete`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json; charset=utf-8",
                },
                body: JSON.stringify({
                    server_id: serverId,
                }),
            })
                .then((response) => {
                    return response.json();
                })
                .then((data) => {
                    agentsTable.clearData();
                })
                .catch((error) => {
                    console.error("Error when deleting all agent:", error);
                });
        }
    } else {
        console.error("Agent Table is not initialized.");
    }
}

function initAgentTable(serverId, data) {
    curServerId = serverId;
    agentsTable = new Tabulator("#agent-table", {
        data: data,
        columns: [
            {
                title: "ID",
                field: "agent_id",
                vertAlign: "middle",
            },
            {
                title: "Name",
                field: "name",
                vertAlign: "middle",
            },
            {
                title: "Class",
                field: "type",
                vertAlign: "middle",
            },
            {
                title: "System prompt",
                field: "sys_prompt",
                vertAlign: "middle",
            },
            {
                title: "Model",
                field: "model",
                vertAlign: "middle",
                formatter: function (cell, formatterParams, onRendered) {
                    if (cell.getData().model == null) {
                        return `<div class="status-tag unknown">None</div>`;
                    }
                    return `<div class="status-tag running">[${
                        cell.getData().model.model_type
                    }]: ${cell.getData().model.config_name}</div>`;
                },
            },
            {
                title: "Delete",
                formatter: deleteIcon,
                width: 75,
                hozAlign: "center",
                vertAlign: "middle",
                cellClick: function (e, cell) {
                    if (
                        confirm(
                            `Are you sure to delete agent ${
                                cell.getData().id
                            } ?`
                        )
                    ) {
                        fetch(`/api/servers/agents/delete`, {
                            method: "POST",
                            headers: {
                                "Content-Type":
                                    "application/json; charset=utf-8",
                            },
                            body: JSON.stringify({
                                agent_id: cell.getData().agent_id,
                                server_id: serverId,
                            }),
                        })
                            .then((response) => {
                                return response.json();
                            })
                            .then((data) => {
                                cell.getRow().delete();
                            })
                            .catch((error) => {
                                console.error(
                                    "Error when deleting agent:",
                                    error
                                );
                            });
                    }
                },
            },
        ],
        layout: "fitColumns",
    });
    agentsTable.on("rowClick", function (e, row) {
        if (e.target.classList.contains("cell-btn")) {
            return;
        }
        loadAgentMemory(serverId, row.getData().agent_id, row.getData().name);
    });
}

function loadAgentDetails(serverData) {
    var serverDetail = document.getElementById("server-detail");
    var serverDetailTitle = serverDetail.querySelector(".server-section-title");
    serverDetailTitle.textContent = `Agents on (${serverData.host}:${serverData.port})[${serverData.id}]`;
    serverDetail.classList.remove("collapsed");
    var agentMemory = document.getElementById("agent-memory");
    if (!agentMemory.classList.contains("collapsed")) {
        agentMemory.classList.add("collapsed");
    }
    getAgentTableData(serverData.id, initAgentTable);
}

// agent memory functions

function showMessage(message) {
    if (messageEditor) {
        messageEditor.setValue(JSON.stringify(message, null, 2));
    } else {
        console.error("Message Editor is not initialized.");
    }
}

function loadAgentMemory(serverId, agentId, agentName) {
    var agentMemory = document.getElementById("agent-memory");
    var agentMemoryTitle = agentMemory.querySelector(".server-section-title");
    agentMemoryTitle.textContent = `Memory of (${agentName})[${agentId}]`;
    agentMemory.classList.remove("collapsed");
    getAgentMemoryData(serverId, agentId, initAgentMemoryTable);
}

function getAgentMemoryData(serverId, agentId, callback) {
    fetch(`/api/servers/agents/memory`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json; charset=utf-8",
        },
        body: JSON.stringify({
            server_id: serverId,
            agent_id: agentId,
        }),
    })
        .then((response) => {
            if (!response.ok) {
                throw new Error("Failed to fetch agent memory data");
            }
            return response.json();
        })
        .then((data) => {
            // Update the agent memory table with the fetched data
            callback(agentId, data);
        });
}

function initAgentMemoryTable(agentId, memoryData) {
    agentMemoryTable = new Tabulator("#agent-memory-table", {
        data: memoryData,
        columns: [
            {
                title: "Name",
                field: "name",
                vertAlign: "middle",
            },
            {
                title: "Role",
                field: "role",
                vertAlign: "middle",
            },
        ],
        layout: "fitColumns",
    });
    agentMemoryTable.on("rowClick", function (e, row) {
        showMessage(row.getData());
    });
    require.config({
        paths: {
            vs: "https://cdn.jsdelivr.net/npm/monaco-editor@latest/min/vs",
        },
    });
    require(["vs/editor/editor.main"], function () {
        if (messageEditor) {
            messageEditor.dispose();
            messageEditor = null;
        }
        messageEditor = monaco.editor.create(
            document.getElementById("agent-memory-raw"),
            {
                language: "json",
                theme: "vs-light",
                minimap: {
                    enabled: false,
                },
                wordWrap: "on",
                scrollBeyondLastLine: false,
                readOnly: true,
            }
        );
    });
}

function flushAgentMemoryTable(agentId, data) {
    if (agentMemoryTable) {
        agentMemoryTable.setData(data);
        console.log("Flush Agent Memory Table");
    } else {
        console.error("Agent Memory Table is not initialized.");
    }
}

// Initialize the server page with a table of servers
function initializeServerPage() {
    // init servers
    console.log("init server manager script");
    getServerTableData(initServerTable);
    let serverflushBtn = document.getElementById("flush-server-btn");
    serverflushBtn.onclick = function () {
        getServerTableData(flushServerTable);
    };
    let deleteDeadServerBtn = document.getElementById("delete-dead-server-btn");
    deleteDeadServerBtn.onclick = deleteDeadServer;
    let agentflushBtn = document.getElementById("flush-agent-btn");
    agentflushBtn.onclick = function () {
        let serverId = curServerId;
        getAgentTableData(serverId, flushAgentTable);
    };
    let deleteAllAgentBtn = document.getElementById("delete-all-agent-btn");
    deleteAllAgentBtn.onclick = deleteAllAgent;
    let memoryflushBtn = document.getElementById("flush-memory-btn");
    memoryflushBtn.onclick = flushAgentMemoryTable;
    window.addEventListener("resize", () => {
        if (messageEditor) {
            messageEditor.layout();
        }
    });
}
