function initializeDashboardRunsPage() {
    //TODO: fetch runs data from server
    fetch('/api/runs/all')
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch runs data');
            }
            return response.json();
        })
        .then(data => {
            var runsTable = new Tabulator("#runs-table", {
                data: data,

                columns: [
                    {title: "Status", field: "status", editor: false},
                    {title: "ID", field: "id", editor: false},
                    {title: "Project", field: "project", editor: false},
                    {title: "Name", field: "name", editor: false},
                    {title: "Create time", field: "create_time", editor: false},
                ],
                layout: "fitDataStretch",
            })

            // Set up row click event
            runsTable.on("rowClick", function (e, row) {
                // Jump to the run detail page
                loadDetailPageInDashboardContent('static/html/dashboard-detail.html', 'static/js/dashboard-detail.js', row.getData());
            });
        })
        .catch(error => {

        });
}