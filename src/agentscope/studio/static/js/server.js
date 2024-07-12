var serversTable;
var agentsTable;
var curServerId;

function deleteServer(e, cell) {
    const serverId = cell.getData().id;
    if (confirm(`Are you sure you want to stop server ${serverId} ?`)) {
        fetch(`/api/servers/delete/${serverId}`)
            .then((response) => {
                if (!response.ok) {
                    throw new Error("Failed to delete server");
                }
                return response.json();
            })
            .then((data) => {
                cell.getRow().delete();
            });
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
                            `Are you sure you want to delete agent ${
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
}

function loadAgentDetails(serverData) {
    var serverDetail = document.getElementById("server-detail");
    var serverDetailTitle = serverDetail.querySelector(".server-section-title");
    serverDetail.classList.remove("collapsed");
    serverDetailTitle.textContent = `Agents on [${serverData.id}](${serverData.host}:${serverData.port})`;
    getAgentTableData(serverData.id, initAgentTable);
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

function flushAgentTable(serverId, data) {
    if (agentsTable) {
        agentsTable.setData(data);
        console.log("Flush Agent Table");
    } else {
        console.error("Agent Table is not initialized.");
    }
}

function deleteIcon(cell, formatterParams, onRendered) {
    return '<img src="/static/svg/circle-delete.svg" class="icon"/>';
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
            if (data.status == "running") {
                cell.getElement().innerHTML =
                    '<div class="status-tag running">running</div>';
                var row = cell.getRow();
                row.update({
                    status: data.status,
                    cpu: data.cpu,
                    mem: data.mem,
                });
            } else {
                cell.getElement().innerHTML =
                    '<div class="status-tag dead">dead</div>';
            }
        })
        .catch((error) => {
            console.error("Error fetching server status:", error);
            cell.getElement().innerHTML =
                '<div class="status-tag unknown">unknown</div>';
        });
}

function cpuUsage(cell, formatterParams, onRendered) {
    if (cell.getData().cpu) {
        return `<div class="status-tag running">${cell.getData().cpu} %</div>`;
    } else {
        return '<div class="status-tag unknown">unknown</div>';
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
                cellClick: deleteServer,
            },
        ],
        layout: "fitColumns",
    });
    serversTable.on("rowClick", function (e, row) {
        if (row.getData().status != "running") {
            return;
        }
        loadAgentDetails(row.getData());
    });
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
    let agentflushBtn = document.getElementById("flush-agent-btn");
    agentflushBtn.onclick = function () {
        let serverId = curServerId;
        getAgentTableData(serverId, flushAgentTable);
    };
}
