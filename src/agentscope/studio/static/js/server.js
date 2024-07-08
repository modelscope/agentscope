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
    return '<svg t="1719488530356" class="icon" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="11441"><path d="M937.281581 799.254764 937.281581 799.254764 937.281581 799.254764 937.281581 799.254764zM1002.320395 510.91602c0-270.99506-220.409315-491.404375-491.404375-491.404375-270.99506 0-491.404375 220.409315-491.404375 491.404375 0 270.99506 220.409315 491.404375 491.404375 491.404375C781.91108 1002.320395 1002.320395 781.91108 1002.320395 510.91602M510.91602 931.500353c-231.971771 0-421.306987-188.612562-421.306987-421.306987 0-231.971771 188.612562-421.306987 421.306987-421.306987 231.971771 0 421.306987 188.612562 421.306987 421.306987C931.500353 742.887791 742.887791 931.500353 510.91602 931.500353M712.536344 664.841214l-151.757234-152.479887 151.757234-150.311927c13.730416-13.730416 13.730416-36.132675 0-49.863091-13.730416-13.730416-36.132675-13.730416-49.863091 0L510.91602 462.498236 360.604093 312.186309c-13.730416-13.730416-36.132675-13.730416-49.863091 0-13.730416 13.730416-13.730416 36.132675 0 49.863091l149.589273 150.311927L310.018349 661.227946c-13.730416 13.730416-13.730416 36.132675 0 49.863091 7.226535 7.226535 15.898377 10.117149 24.570219 10.117149 8.671842 0 18.066337-3.613267 24.570219-10.117149l151.03458-149.589273 152.479887 152.479887c6.503881 6.503881 15.898377 10.117149 24.570219 10.117149 8.671842 0 18.066337-3.613267 24.570219-10.117149C725.544107 700.973888 725.544107 678.57163 712.536344 664.841214" p-id="11442"></path></svg>';
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
