let currentCode = null;
let editorInstance = null;

function initializeDashboardDetailCodePage(codeUrl) {
    initializeMonacoEditor();

    fetch("/api/code?run_dir=" + codeUrl)
        .then((response) => {
            if (!response.ok) {
                throw new Error("Connection error, cannot load the web page.");
            }
            return response.json();
        })
        .then((data) => {
            console.log("Get ", data);
            currentCode = data;
            constructCodeFileList(codeUrl, data);
        })
        .catch((error) => {
            console.error("Error encountered while loading page: ", error);
        });
}

function constructCodeFileList(codeUrl, code) {
    let codeFileRows = [`<ul>${codeUrl}</ul>`];

    if (code !== null && code !== undefined) {
        if (Object.keys(code).length === 0) {
            codeFileRows = [
                '<div class="content-placeholder">No code available</div>',
            ];
        } else {
            Object.keys(code).forEach((key) =>
                codeFileRows.push(
                    `<li onclick="displayCode('${key}');return false;">${key}</li>`
                )
            );
        }
    }

    document.getElementById("code-list").innerHTML = codeFileRows.join("\n");
}

function initializeMonacoEditor() {
    require.config({
        paths: {
            vs: "https://cdn.jsdelivr.net/npm/monaco-editor@latest/min/vs",
        },
    });
    require(["vs/editor/editor.main"], function () {
        editorInstance = monaco.editor.create(
            document.getElementById("code-editor"),
            {
                language: "python",
                theme: "vs-light",
                scrollBeyondLastLine: false,
                readOnly: true,
            }
        );
    }, function (error) {
        console.error("Error encountered while loading monaco editor: ", error);
    });
}

function displayCode(codeFileName) {
    document.getElementById("code-filename").innerHTML = codeFileName;

    if (editorInstance) {
        editorInstance.setValue(currentCode[codeFileName]);
    } else {
        console.log(
            "Monaco editor instance is not available, set text content"
        );
        document.getElementById("code-editor").textContent =
            currentCode[codeFileName];
    }
}
