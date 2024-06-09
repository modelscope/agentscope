let runtimeInfo = null;
let currentContent = null;

function initializeDashboardDetailPageByUrl(pageUrl) {
    switch (pageUrl) {
        case "static/html/dashboard-detail-dialogue.html":
            initializeDashboardDetailDialoguePage(runtimeInfo);
            break;
        case "static/html/dashboard-detail-code.html":
            initializeDashboardDetailCodePage(runtimeInfo["run_dir"]);
            break;
        case "static/html/dashboard-detail-invocation.html":
            initializeDashboardDetailInvocationPage(runtimeInfo["run_dir"]);
            break;
    }
}

// The dashboard detail page supports three tabs:
// 1. dialogue tab: the dialogue history of the runtime instance
// 2. code tab: the code files
// 3. invocation tab: the model invocation records
function loadDashboardDetailContent(pageUrl, javascriptUrl) {
    const dialogueTabBtn = document.getElementById("dialogue-tab-btn");
    const codeTabBtn = document.getElementById("code-tab-btn");
    const invocationTabBtn = document.getElementById("invocation-tab-btn");
    if (currentContent === pageUrl) {
        return;
    } else {
        currentContent = pageUrl;
    }
    // switch selected status
    switch (pageUrl) {
        case "static/html/dashboard-detail-dialogue.html":
            dialogueTabBtn.classList.add("selected");
            codeTabBtn.classList.remove("selected");
            invocationTabBtn.classList.remove("selected");
            break;
        case "static/html/dashboard-detail-code.html":
            dialogueTabBtn.classList.remove("selected");
            codeTabBtn.classList.add("selected");
            invocationTabBtn.classList.remove("selected");
            break;
        case "static/html/dashboard-detail-invocation.html":
            dialogueTabBtn.classList.remove("selected");
            codeTabBtn.classList.remove("selected");
            invocationTabBtn.classList.add("selected");
            break;
    }

    fetch(pageUrl, { cache: "no-store" })
        .then((response) => {
            if (!response.ok) {
                throw new Error("Connection error, cannot load the web page.");
            }
            return response.text();
        })
        .then((html) => {
            // Load the page content
            document.getElementById("detail-content").innerHTML = html;

            if (!isScriptLoaded(javascriptUrl)) {
                let script = document.createElement("script");
                script.src = javascriptUrl;
                script.onload = function () {
                    initializeDashboardDetailPageByUrl(pageUrl);
                };
                document.head.appendChild(script);
            } else {
                initializeDashboardDetailPageByUrl(pageUrl);
            }
        })
        .catch((error) => {
            console.error("Error encountered while loading page: ", error);
            document.getElementById("content").innerHTML =
                "<p>Loading failed.</p>" + error;
        });
}

// Initialize the dashboard detail page, this function is the entry point of the dashboard detail page
function initializeDashboardDetailPage(pRuntimeInfo) {
    // The default content of the dashboard detail page
    console.log(
        "Initialize dashboard detail page with runtime id: " +
            pRuntimeInfo.run_id
    );
    runtimeInfo = pRuntimeInfo;
    currentContent = null;
    loadDashboardDetailContent(
        "static/html/dashboard-detail-dialogue.html",
        "static/js/dashboard-detail-dialogue.js"
    );
}
