let invocationEditor = null;

function initializeDashboardDetailInvocationPage(runDir) {
    // load monaco editor
    if (invocationEditor === null) {
        require.config({paths: {'vs': 'https://cdn.jsdelivr.net/npm/monaco-editor@latest/min/vs'}});
        require(['vs/editor/editor.main'], function () {
            invocationEditor = monaco.editor.create(document.getElementById('invocation-content'), {
                language: 'json',
                theme: 'vs-light',
                minimap: {
                    enabled: false  // 禁用minimap
                },
                scrollBeyondLastLine: false,
                readOnly: true,
            });
        });
    }

    // fetch data from server
    fetch("/api/invocation?run_dir=" + runDir)
        .then(response => {
            if (response.ok) {
                return response.json();
            } else {
                throw new Error("Failed to fetch invocation detail");
            }
        })
        .then(data => {
            console.log(data);
            var invocationTable = new Tabulator("#invocation-list", {
                data: data,
                columns: [
                    {
                        title: "Model Wrapper",
                        field: "model_class",
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
                placeholder: "<div class='content-placeholder'>No invocation records available.</div>",
            });

            // Set up row click event
            invocationTable.on("rowClick", function (e, row) {
                // Jump to the run detail page
                invocationEditor.setValue(row.getData());
            });
        })
        .catch(error => {
            console.error(error);
        });
}

