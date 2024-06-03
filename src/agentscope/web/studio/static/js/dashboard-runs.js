// Search functionality for runs table
function allColumnFilter(data) {
    let searchValue = document
        .getElementById("runs-search-input")
        .value.toLowerCase();

    for (var field in data) {
        if (data.hasOwnProperty(field)) {
            var value = data[field];

            if (value != null) {
                value = value.toString().toLowerCase();
                if (value.includes(searchValue)) {
                    return true;
                }
            }
        }
    }
    return false;
}

function renderIconInRunsTable(cell, formatterParams, onRendered) {
    let value = cell.getValue();
    switch (value) {
        case "running":
            return '<div class="runs-table-status-tag running"><svg class="runs-table-status-svg" viewBox="0 0 1027 1024" xmlns="http://www.w3.org/2000/svg"><path d="M770.879148 64.221893h159.70676a31.99895 31.99895 0 0 0 0-63.9979h-319.989501v320.629479a31.99895 31.99895 0 1 0 63.9979 0V93.052947A458.864943 458.864943 0 0 1 963.704821 510.863237 447.9853 447.9853 0 1 1 450.601657 64.221893h31.99895a31.99895 31.99895 0 0 0 0-63.9979h-31.99895A513.83914 513.83914 0 1 0 1027.702721 510.863237a534.382466 534.382466 0 0 0-256.823573-446.641344z"></path></svg>running</div>';

        case "waiting":
            return '<div class="runs-table-status-tag waiting"><svg class="runs-table-status-svg" viewBox="0 0 1027 1024" xmlns="http://www.w3.org/2000/svg"><path d="M770.879148 64.221893h159.70676a31.99895 31.99895 0 0 0 0-63.9979h-319.989501v320.629479a31.99895 31.99895 0 1 0 63.9979 0V93.052947A458.864943 458.864943 0 0 1 963.704821 510.863237 447.9853 447.9853 0 1 1 450.601657 64.221893h31.99895a31.99895 31.99895 0 0 0 0-63.9979h-31.99895A513.83914 513.83914 0 1 0 1027.702721 510.863237a534.382466 534.382466 0 0 0-256.823573-446.641344z"></path></svg>waiting</div>';

        case "finished":
            return '<div class="runs-table-status-tag finished"><svg class="runs-table-status-svg" viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg"><path d="M468.712727 676.421818a28.974545 28.974545 0 0 1-20.48-8.494545L264.145455 485.003636a29.090909 29.090909 0 1 1 40.96-41.309091l163.607272 162.909091 261.585455-260.421818a29.090909 29.090909 0 1 1 40.96 41.309091L488.727273 667.927273a28.974545 28.974545 0 0 1-20.014546 8.494545z"></path><path d="M512 1000.727273a488.727273 488.727273 0 1 1 488.727273-488.727273 488.727273 488.727273 0 0 1-488.727273 488.727273z m0-919.272728a430.545455 430.545455 0 1 0 430.545455 430.545455A430.545455 430.545455 0 0 0 512 81.454545z"></path></svg>finished</div>';

        default:
            return '<div class="runs-table-status-tag unknown"><svg class="runs-table-status-svg" viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg"><path d="M493.381818 642.56a29.090909 29.090909 0 0 1-29.090909-29.090909V593.454545a149.410909 149.410909 0 0 1 15.36-67.490909c11.636364-24.785455 33.978182-52.014545 68.770909-82.501818 22.341818-22.341818 27.461818-28.276364 28.509091-29.556363a64 64 0 0 0 15.36-39.68 68.305455 68.305455 0 0 0-17.221818-49.454546c-11.636364-11.636364-28.858182-16.756364-53.76-16.756364-27.345455 0-46.545455 8.029091-59.229091 25.25091a104.727273 104.727273 0 0 0-18.618182 66.792727 29.090909 29.090909 0 0 1-58.181818 0 160.116364 160.116364 0 0 1 30.836364-102.632727c23.272727-31.418182 59.345455-47.709091 104.727272-47.709091 40.494545 0 72.610909 11.636364 95.418182 34.909091a125.672727 125.672727 0 0 1 33.745455 90.065454 121.716364 121.716364 0 0 1-27.927273 75.752727c-3.258182 4.072727-9.774545 11.636364-33.629091 34.909091l-1.396364 1.396364c-34.909091 30.952727-49.687273 52.130909-55.272727 64.349091a91.694545 91.694545 0 0 0-9.309091 42.356363v19.781819a29.090909 29.090909 0 0 1-29.090909 29.323636z"></path><path d="M493.381818 726.341818m-40.261818 0a40.261818 40.261818 0 1 0 80.523636 0 40.261818 40.261818 0 1 0-80.523636 0Z"></path><path d="M517.934545 1011.665455a488.727273 488.727273 0 1 1 488.727273-488.727273 488.727273 488.727273 0 0 1-488.727273 488.727273z m0-919.272728a430.545455 430.545455 0 1 0 430.545455 430.545455 430.545455 430.545455 0 0 0-430.545455-430.545455z"></path></svg>unknown</div>';
    }
}

function initializeDashboardRunsPage() {
    //TODO: fetch runs data from server
    fetch("/api/runs/all")
        .then((response) => {
            if (!response.ok) {
                throw new Error("Failed to fetch runs data");
            }
            return response.json();
        })
        .then((data) => {
            var runsTable = new Tabulator("#runs-table", {
                data: data,
                columns: [
                    {
                        title: "Status",
                        field: "status",
                        editor: false,
                        vertAlign: "middle",
                        formatter: renderIconInRunsTable,
                    },
                    {
                        title: "ID",
                        field: "run_id",
                        editor: false,
                        vertAlign: "middle",
                    },
                    {
                        title: "Project",
                        field: "project",
                        editor: false,
                        vertAlign: "middle",
                    },
                    {
                        title: "Name",
                        field: "name",
                        editor: false,
                        vertAlign: "middle",
                    },
                    {
                        title: "Timestamp",
                        field: "timestamp",
                        editor: false,
                        vertAlign: "middle",
                    },
                ],
                layout: "fitColumns",
                initialSort: [{ column: "timestamp", dir: "desc" }],
            });

            // Search logic
            document
                .getElementById("runs-search-input")
                .addEventListener("input", function (e) {
                    let searchValue = e.target.value;
                    if (searchValue) {
                        // Filter the table
                        runsTable.setFilter(allColumnFilter);
                    } else {
                        //Clear the filter
                        runsTable.clearFilter();
                    }
                });

            // Set up row click event
            runsTable.on("rowClick", function (e, row) {
                // Jump to the run detail page
                loadDetailPageInDashboardContent(
                    "static/html/dashboard-detail.html",
                    "static/js/dashboard-detail.js",
                    row.getData()
                );
            });
        })
        .catch((error) => {
            console.error(error);
        });
}
