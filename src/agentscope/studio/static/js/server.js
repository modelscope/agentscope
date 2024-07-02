function loadServerDetail(serverData) {
    var serverDetail = document.getElementById("server-detail");
    var serverDetailTitle = serverDetail.querySelector(".server-section-title");

    serverDetail.classList.remove("collapsed");
    serverDetailTitle.textContent = `Agents on [${serverData.id}](${serverData.host}:${serverData.port})`;
    fetch("/api/servers/agent_info/" + serverData.id)
        .then((response) => {
            if (!response.ok) {
                throw new Error("Failed to fetch agents data");
            }
            return response.json();
        })
        .then((data) => {
            let agentsTable = new Tabulator("#agent-table", {
                data: data,
                columns: [
                    {
                        title: "Name",
                        field: "name",
                        vertAlign: "middle",
                    },
                    {
                        title: "Type",
                        field: "type",
                        vertAlign: "middle",
                    },
                    {
                        title: "ID",
                        field: "agent_id",
                        vertAlign: "middle",
                    },
                    {
                        title: "model",
                        field: "config_name",
                        vertAlign: "middle",
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
                                    "Are you sure you want to delete agent " +
                                        cell.getRow().getData().id +
                                        "?"
                                )
                            ) {
                                console.log(
                                    "delete agent " + cell.getRow().getData().id
                                );
                            }
                        },
                    },
                ],
                layout: "fitColumns",
            });
        });
}

function newServer() {
    console.log("new Server");
}

function flushServer() {
    console.log("flush Server");
}

function deleteIcon(cell, formatterParams, onRendered) {
    return '<svg t="1719488530356" class="icon" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="11441"><path d="M937.281581 799.254764 937.281581 799.254764 937.281581 799.254764 937.281581 799.254764zM1002.320395 510.91602c0-270.99506-220.409315-491.404375-491.404375-491.404375-270.99506 0-491.404375 220.409315-491.404375 491.404375 0 270.99506 220.409315 491.404375 491.404375 491.404375C781.91108 1002.320395 1002.320395 781.91108 1002.320395 510.91602M510.91602 931.500353c-231.971771 0-421.306987-188.612562-421.306987-421.306987 0-231.971771 188.612562-421.306987 421.306987-421.306987 231.971771 0 421.306987 188.612562 421.306987 421.306987C931.500353 742.887791 742.887791 931.500353 510.91602 931.500353M712.536344 664.841214l-151.757234-152.479887 151.757234-150.311927c13.730416-13.730416 13.730416-36.132675 0-49.863091-13.730416-13.730416-36.132675-13.730416-49.863091 0L510.91602 462.498236 360.604093 312.186309c-13.730416-13.730416-36.132675-13.730416-49.863091 0-13.730416 13.730416-13.730416 36.132675 0 49.863091l149.589273 150.311927L310.018349 661.227946c-13.730416 13.730416-13.730416 36.132675 0 49.863091 7.226535 7.226535 15.898377 10.117149 24.570219 10.117149 8.671842 0 18.066337-3.613267 24.570219-10.117149l151.03458-149.589273 152.479887 152.479887c6.503881 6.503881 15.898377 10.117149 24.570219 10.117149 8.671842 0 18.066337-3.613267 24.570219-10.117149C725.544107 700.973888 725.544107 678.57163 712.536344 664.841214" p-id="11442"></path></svg>';
}

function serverStatusIcon(cell, formatterParams, onRendered) {
    return '<div class="runs-table-status-tag running">running</div>';
}

// Initialize the server page with a table of servers
function initializeServerPage() {
    // init servers
    console.log("init server manager script");
    fetch("/api/servers/all")
        .then((response) => {
            if (!response.ok) {
                throw new Error("Failed to fetch servers data");
            }
            return response.json();
        })
        .then((data) => {
            let serversTable = new Tabulator("#server-table", {
                data: data,
                columns: [
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
                        formatter: serverStatusIcon,
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
                                    "Are you sure you want to stop server " +
                                        cell.getRow().getData().id +
                                        "?"
                                )
                            ) {
                                console.log(
                                    "stop server " + cell.getRow().getData().id
                                );
                            }
                        },
                    },
                ],
                layout: "fitColumns",
            });
            serversTable.on("rowClick", function (e, row) {
                loadServerDetail(row.getData());
            });
        });
}
