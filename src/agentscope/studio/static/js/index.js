const dashboardTabBtn = document.getElementById("dashboard-tab-btn");
const workstationTabBtn = document.getElementById("workstation-tab-btn");
const marketTabBtn = document.getElementById("market-tab-btn");
const serverTabBtn = document.getElementById("server-tab-btn");
const navigationBar = document.getElementById("navigation-bar");

let currentPageUrl = null;
let inGuidePage = true;
// When navigation bar collapsed, only when the mouse leaves the navigation bar, then navigation bar will be able to be expanded
let activeExpanded = false;

// Check if the script is already loaded
function isScriptLoaded(src) {
    return Array.from(document.scripts).some((script) => {
        return (
            new URL(script.src).pathname ===
            new URL(src, window.location.href).pathname
        );
    });
}

// After loading different pages, we need to call the initialization function of this page
function initializeTabPageByUrl(pageUrl) {
    switch (pageUrl) {
        case "static/html/dashboard.html":
            initializeDashboardPage();
            break;
        case "static/html/workstation_iframe.html":
            let script = document.createElement("script");
            script.src = "static/js/workstation_iframe.js";
            document.head.appendChild(script);
            break;
    }
}

// Loading different pages in index.html
function loadTabPage(pageUrl, javascriptUrl) {
    fetch(pageUrl)
        .then((response) => {
            if (!response.ok) {
                throw new Error("Connection error, cannot load the web page.");
            }
            return response.text();
        })
        .then((html) => {
            currentPageUrl = pageUrl;

            // Hide the sidebar for other pages except the guide page
            if (pageUrl === "static/html/index-guide.html") {
                navigationBar.classList.remove("collapsed");
                inGuidePage = true;
            } else {
                navigationBar.classList.add("collapsed");
                inGuidePage = false;
                activeExpanded = false;
            }

            // Load the javascript file
            if (javascriptUrl && !isScriptLoaded(javascriptUrl)) {
                let script = document.createElement("script");
                script.src = javascriptUrl;
                script.onload = function () {
                    // The first time we must initialize the page within the onload function to ensure the script is loaded
                    initializeTabPageByUrl(pageUrl);
                };
                document.head.appendChild(script);
            } else {
                console.log("Script already loaded for " + javascriptUrl);
                // If is not the first time, we can directly call the initialization function
                initializeTabPageByUrl(pageUrl);
            }

            // Load the page content
            document.getElementById("content").innerHTML = html;

            // switch selected status of the tab buttons
            switch (pageUrl) {
                case "static/html/dashboard.html":
                    dashboardTabBtn.classList.add("selected");
                    workstationTabBtn.classList.remove("selected");
                    marketTabBtn.classList.remove("selected");
                    serverTabBtn.classList.remove("selected");
                    break;

                case "static/html/workstation_iframe.html":
                    dashboardTabBtn.classList.remove("selected");
                    workstationTabBtn.classList.add("selected");
                    marketTabBtn.classList.remove("selected");
                    serverTabBtn.classList.remove("selected");
                    break;

                case "static/html/market.html":
                    dashboardTabBtn.classList.remove("selected");
                    workstationTabBtn.classList.remove("selected");
                    marketTabBtn.classList.add("selected");
                    serverTabBtn.classList.remove("selected");
                    break;

                case "static/html/server.html":
                    dashboardTabBtn.classList.remove("selected");
                    workstationTabBtn.classList.remove("selected");
                    marketTabBtn.classList.remove("selected");
                    serverTabBtn.classList.add("selected");
                    break;
            }
        })
        .catch((error) => {
            console.error("Error encountered while loading page: ", error);
            document.getElementById("content").innerHTML =
                "<p>Loading failed.</p>" + error;
        });
}

loadTabPage("static/html/index-guide.html", null);

document.addEventListener("DOMContentLoaded", function () {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has("run_id")) {
        loadTabPage("static/html/dashboard.html", "static/js/dashboard.js");
    }
});

navigationBar.addEventListener("mouseenter", function () {
    if (activeExpanded) {
        navigationBar.classList.remove("collapsed");
    }
});

navigationBar.addEventListener("mouseleave", function () {
    // In guide page, the navigation bar will not be collapsed
    if (!inGuidePage) {
        // Collapse the navigation bar when the mouse leaves the navigation bar
        navigationBar.classList.add("collapsed");
        // Allow the navigation bar to be expanded when the mouse leaves the navigation bar to avoid expanding right after collapsing (when not finished collapsing yet)
        activeExpanded = true;
    }
});
