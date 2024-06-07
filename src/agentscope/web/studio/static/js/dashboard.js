function loadRunsPageInDashboardContent(pageUrl, javascriptUrl) {
    fetch(pageUrl)
        .then((response) => {
            if (!response.ok) {
                throw new Error("Connection error, cannot load the web page.");
            }
            return response.text();
        })
        .then((html) => {
            // Load the page content
            document.getElementById("dashboard-content").innerHTML = html;

            // Load the javascript file
            if (!isScriptLoaded(javascriptUrl)) {
                console.log("Loading script from " + javascriptUrl + "...");
                let script = document.createElement("script");
                script.src = javascriptUrl;
                script.onload = function () {
                    // Initialize the runs tables
                    initializeDashboardRunsPage();
                };
                document.head.appendChild(script);
            } else {
                // Initialize the runs tables
                initializeDashboardRunsPage();
            }

            // Jump to specific run if url contains run_id
            const urlParams = new URLSearchParams(window.location.search);
            if (urlParams.has("run_id")) {
                var loc = window.location;
                var baseUrl = loc.protocol + "//" + loc.host;
                const run_id = urlParams.get("run_id");
                history.replaceState(null, null, baseUrl);
                fetch("/api/runs/get/" + run_id)
                    .then((response) => {
                        console.log("fetch /api/runs/get/");

                        if (!response.ok) {
                            throw new Error(
                                "Runtime id " + run_id + " not found."
                            );
                        }
                        return response.json();
                    })
                    .then((data) => {
                        console.log("get runs" + data);
                        loadDetailPageInDashboardContent(
                            "static/html/dashboard-detail.html",
                            "static/js/dashboard-detail.js",
                            data
                        );
                    });
            }
        })
        .catch((error) => {
            console.error("Error encountered while loading page: ", error);
            document.getElementById("content").innerHTML =
                "<p>Loading failed.</p>" + error;
        });
}

function loadDetailPageInDashboardContent(pageUrl, javascriptUrl, runtimeInfo) {
    fetch(pageUrl)
        .then((response) => {
            if (!response.ok) {
                throw new Error("Connection error, cannot load the web page.");
            }
            return response.text();
        })
        .then((html) => {
            // Load the page content
            document.getElementById("dashboard-content").innerHTML = html;

            if (!isScriptLoaded(javascriptUrl)) {
                console.log("Loading script from " + javascriptUrl + "...");
                let script = document.createElement("script");
                script.src = javascriptUrl;
                script.onload = function () {
                    initializeDashboardDetailPage(runtimeInfo);
                };
                document.head.appendChild(script);
            } else {
                initializeDashboardDetailPage(runtimeInfo);
            }

            // Update the title bar of the dashboard page
            let titleBar = document.getElementById("dashboard-titlebar");
            // TODO: Add link to the dashboard page
            titleBar.innerHTML +=
                '<svg class="dashboard-titlebar-svg" viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg"><path d="M718.16751787 491.2381952a38.36258987 38.36258987 0 0 0-4.898816-5.99763627L365.71163307 137.68349013c-14.9291008-14.9291008-39.1348224-14.9291008-54.0639232 0s-14.9291008 39.1348224 0 54.0639232l320.52456106 320.52565334-320.52565333 320.52456106c-14.9291008 14.9291008-14.9291008 39.1348224 0 54.0639232s39.1348224 14.9291008 54.0639232 0l347.5570688-347.5570688a38.08733867 38.08733867 0 0 0 11.1968256-27.03250773 38.141952 38.141952 0 0 0-6.29691733-21.0337792z"></path></svg>' +
                "<span class='dashboard-subtitlebar-span unselectable-text'>Runtime ID: " +
                runtimeInfo.run_id +
                "</span>";
            let mainTitle = document.getElementById("dashboard-main-title");
            mainTitle.onclick = () => {
                loadTabPage(
                    "static/html/dashboard.html",
                    "static/js/dashboard.js"
                );
            };
        })
        .catch((error) => {
            console.error("Error encountered while loading page: ", error);
            document.getElementById("content").innerHTML =
                "<p>Loading failed.</p>" + error;
        });
}

// Initialize the dashboard page with a table of runtime instances
function initializeDashboardPage() {
    // The default content of the dashboard page
    loadRunsPageInDashboardContent(
        "static/html/dashboard-runs.html",
        "static/js/dashboard-runs.js"
    );
}
