//TODO: move the following to chat js

let chatRowOtherTemplate,
    chatRowUserTemplate,
    chatRowSystemTemplate,
    infoRowTemplate;

let currentRuntimeInfo, currentMsgInfo, currentAgentInfo;

let infoClusterize;

const agentIcons = [
    '<path d="M21.344 448h85.344v234.656H21.344V448zM554.656 192h64V106.656h-213.344V192h64v42.656h-320V896h725.344V234.656h-320V192z m234.688 128v490.656H234.688V320h554.656zM917.344 448h85.344v234.656h-85.344V448z"></path><path d="M341.344 512H448v106.656h-106.656V512zM576 512h106.656v106.656H576V512z"></path>',
    '<path d="M576 85.333333c0 18.944-8.234667 35.968-21.333333 47.701334V213.333333h213.333333a128 128 0 0 1 128 128v426.666667a128 128 0 0 1-128 128H256a128 128 0 0 1-128-128V341.333333a128 128 0 0 1 128-128h213.333333V133.034667A64 64 0 1 1 576 85.333333zM256 298.666667a42.666667 42.666667 0 0 0-42.666667 42.666666v426.666667a42.666667 42.666667 0 0 0 42.666667 42.666667h512a42.666667 42.666667 0 0 0 42.666667-42.666667V341.333333a42.666667 42.666667 0 0 0-42.666667-42.666666H256z m-170.666667 128H0v256h85.333333v-256z m853.333334 0h85.333333v256h-85.333333v-256zM384 618.666667a64 64 0 1 0 0-128 64 64 0 0 0 0 128z m256 0a64 64 0 1 0 0-128 64 64 0 0 0 0 128z"></path>',
    '<path d="M175.776914 292.571429h371.741257l35.108572-58.397258h-181.8624c-16.442514 0-18.783086-13.370514-14.628572-21.152914 12.873143-24.049371 39.7312-75.776 80.574172-155.2384 16.676571-23.610514 35.050057-35.401143 55.149714-35.401143 24.341943 0 35.693714 11.790629 34.026057 35.401143l-58.133943 116.9408c106.232686-1.404343 164.571429-1.404343 175.016229 0 8.192 1.082514 11.117714 0.321829 17.6128 10.532572 6.524343 10.210743-0.117029 14.1312 0 18.519771-8.250514 14.511543-12.756114 21.884343-17.6128 30.398171C648.8064 273.934629 635.582171 292.571429 645.12 292.571429h203.893029c11.849143 0 44.763429-3.861943 66.472228 22.293942 14.453029 17.437257 21.357714 39.789714 20.743314 66.998858 0.468114 116.677486 0.702171 184.290743 0.702172 202.839771 0 3.803429 19.0464-69.485714 57.841371-33.850514 17.642057 34.289371 21.328457 163.050057 0 209.832228C965.485714 813.290057 936.930743 729.673143 936.228571 732.511086c0 0 0.702171 109.626514 0.702172 177.005714 0 6.144 4.973714 38.5024-21.445486 62.142171-17.6128 15.798857-39.789714 23.610514-66.472228 23.522743l-703.429486-6.465828c-19.456-2.984229-34.523429-12.170971-45.290057-27.589486-10.708114-15.389257-14.921143-33.850514-12.522057-55.413029v-173.202285c-18.870857 33.938286-38.239086 43.680914-58.046172 29.257143C0 740.205714-3.042743 578.384457 27.735771 556.383086c20.509257-14.687086 40.521143-5.266286 60.035658 28.350171v-202.810514c0-27.326171 9.8304-49.649371 29.461942-66.998857 19.6608-17.378743 39.175314-24.810057 58.514286-22.3232zM175.542857 380.342857v526.628572h672.914286V380.342857H175.542857z"></path><path d="M365.714286 658.285714m-73.142857 0a73.142857 73.142857 0 1 0 146.285714 0 73.142857 73.142857 0 1 0-146.285714 0Z"></path><path d="M687.542857 658.285714m-73.142857 0a73.142857 73.142857 0 1 0 146.285714 0 73.142857 73.142857 0 1 0-146.285714 0Z"></path>',
    '<path d="M745.216 896H278.784a117.888 117.888 0 0 1-108.117-125.653V509.696a117.888 117.888 0 0 1 108.117-125.653h466.432a117.888 117.888 0 0 1 108.117 125.653v260.65A117.888 117.888 0 0 1 745.216 896z m-446.55-426.667A45.824 45.824 0 0 0 256 512v256a45.824 45.824 0 0 0 42.667 42.667h426.666c21.334-1.707 44.16-14.251 42.667-35.755V512a45.824 45.824 0 0 0-42.667-42.667z"></path><path d="M384 554.667q42.667 0 42.667 42.666v85.334q0 42.666-42.667 42.666t-42.667-42.666v-85.334q0-42.666 42.667-42.666zM640 554.667q42.667 0 42.667 42.666v85.334q0 42.666-42.667 42.666t-42.667-42.666v-85.334q0-42.666 42.667-42.666zM511.787 298.027l-42.667 128h85.333z"></path><path d="M598.485 164.864l-24.917 24.917a148.821 148.821 0 0 0-83.03-132.864s-8.533 91.35-49.834 124.544-124.587 132.864 41.515 207.574a98.133 98.133 0 0 1-28.203-85.334 98.133 98.133 0 0 1 53.12-72.533 69.419 69.419 0 0 0 33.28 66.432c41.6 33.152 0 91.35 0 91.35s199.253-49.707 58.07-224.086zM84.267 512H86.4q41.6 0 41.6 41.6v172.8q0 41.6-41.6 41.6h-2.133q-41.6 0-41.6-41.6V553.6q0-41.6 41.6-41.6zM937.6 512h2.133q41.6 0 41.6 41.6v172.8q0 41.6-41.6 41.6H937.6q-41.6 0-41.6-41.6V553.6q0-41.6 41.6-41.6z"></path>',
    '<path d="M512 32c-35.36 0-64 28.64-64 64 0 23.616 12.864 43.872 32 55.008V224h-160c-88 0-160 72-160 160v64H64v256h96v160h704v-160h96v-256h-96v-64c0-88-72-160-160-160h-160V151.008c19.136-11.136 32-31.36 32-55.008 0-35.36-28.64-64-64-64z m-192 256h384c53.376 0 96 42.624 96 96v416h-64v-160H288v160H224V384c0-53.376 42.624-96 96-96z m64 128a63.968 63.968 0 1 0 0 128 63.968 63.968 0 1 0 0-128z m256 0a63.968 63.968 0 1 0 0 128 63.968 63.968 0 1 0 0-128zM128 512h32v128H128z m736 0h32v128h-32z m-512 192h64v96h-64z m128 0h64v96h-64z m128 0h64v96h-64z"></path>',
    '<path d="M699.733333 89.6c21.333333 8.533333 29.866667 34.133333 21.333334 51.2v4.266667L665.6 256H725.333333c89.6 0 166.4 72.533333 170.666667 162.133333v8.533334h42.666667c46.933333 0 85.333333 38.4 85.333333 85.333333v170.666667c0 46.933333-38.4 85.333333-85.333333 85.333333h-42.666667c0 93.866667-76.8 170.666667-170.666667 170.666667H298.666667c-93.866667 0-170.666667-76.8-170.666667-170.666667H85.333333c-46.933333 0-85.333333-38.4-85.333333-85.333333v-170.666667c0-46.933333 38.4-85.333333 85.333333-85.333333h42.666667c0-93.866667 76.8-170.666667 170.666667-170.666667h59.733333L302.933333 145.066667c-8.533333-17.066667 0-42.666667 21.333334-55.466667 17.066667-8.533333 42.666667-4.266667 51.2 17.066667l4.266666 4.266666L452.266667 256h119.466666l72.533334-145.066667 4.266666-4.266666c8.533333-21.333333 34.133333-25.6 51.2-17.066667zM725.333333 341.333333H298.666667c-46.933333 0-81.066667 34.133333-85.333334 81.066667V768c0 46.933333 34.133333 81.066667 81.066667 85.333333H725.333333c46.933333 0 81.066667-34.133333 85.333334-81.066666V426.666667c0-46.933333-34.133333-81.066667-81.066667-85.333334H725.333333zM128 512H85.333333v170.666667h42.666667v-170.666667z m810.666667 0h-42.666667v170.666667h42.666667v-170.666667zM384 512c25.6 0 42.666667 17.066667 42.666667 42.666667v85.333333c0 25.6-17.066667 42.666667-42.666667 42.666667s-42.666667-17.066667-42.666667-42.666667v-85.333333c0-25.6 17.066667-42.666667 42.666667-42.666667z m256 0c25.6 0 42.666667 17.066667 42.666667 42.666667v85.333333c0 25.6-17.066667 42.666667-42.666667 42.666667s-42.666667-17.066667-42.666667-42.666667v-85.333333c0-25.6 17.066667-42.666667 42.666667-42.666667z"></path>',
];

let nameToIconAndColor = {};

function randomSelectAgentIcon() {
    return agentIcons[Math.floor(Math.random() * agentIcons.length)];
}

function randomIntFromInterval(min, max) {
    return Math.floor(Math.random() * (max - min + 1) + min);
}

function hslToHex(h, s, l) {
    l /= 100;
    const a = s * Math.min(l, 1 - l) / 100;
    const f = n => {
        const k = (n + h / 30) % 12;
        const color = l - a * Math.max(Math.min(k - 3, 9 - k, 1), -1);
        return Math.round(255 * color).toString(16).padStart(2, '0');   // 转换为16进制并补零
    };
    return `#${f(0)}${f(8)}${f(4)}`;
}

function randomSelectColor() {
    const h = randomIntFromInterval(0, 360);         // 色相：0°到360°
    const s = randomIntFromInterval(50, 100);        // 饱和度：50%到100%
    const l = randomIntFromInterval(25, 75);         // 亮度：25%到75%
    return hslToHex(h, s, l);
}

async function loadChatTemplate() {
    const response = await fetch("static/html/template.html");
    const htmlText = await response.text();
    const parser = new DOMParser();
    const doc = parser.parseFromString(htmlText, "text/html");

    // save
    chatRowOtherTemplate = doc.querySelector(
        "#chat-row-other-template"
    ).content;
    chatRowUserTemplate = doc.querySelector("#chat-row-user-template").content;
    chatRowSystemTemplate = doc.querySelector(
        "#chat-row-system-template"
    ).content;
    infoRowTemplate = doc.querySelector("#dialogue-info-row-template").content;
}

// Add a chat row according to the role field in the message
function addChatRow(index, pMsg) {
    switch (pMsg.role.toLowerCase()) {
        case "user":
            return _addUserChatRow(index, pMsg);
        case "assistant":
            return _addAssistantChatRow(index, pMsg);
        case "system":
            return _addSystemChatRow(index, pMsg);
    }
}

function _determineFileType(url) {
    // Image
    let img_suffix = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp"];
    // Video
    let video_suffix = [
        ".mp4",
        ".webm",
        ".avi",
        ".mov",
        ".wmv",
        ".flv",
        ".f4v",
        ".m4v",
        ".rmvb",
        ".rm",
        ".3gp",
        ".dat",
        ".ts",
        ".mts",
        ".vob",
    ];
    // Audio
    let audio_suffix = [".mp3", ".wav", ".wma", ".ogg", ".aac", ".flac"];

    if (img_suffix.some((suffix) => url.endsWith(suffix))) {
        return "image";
    } else if (video_suffix.some((suffix) => url.endsWith(suffix))) {
        return "video";
    } else if (audio_suffix.some((suffix) => url.endsWith(suffix))) {
        return "audio";
    }
    return "file";
}

function _renderMultiModalData(url) {
    if (!url || url === "") {
        return "";
    }
    // Determine the type of the file
    let urlType = _determineFileType(url);

    // If we need to fetch the url from the backend
    let src = null;
    if (url.startsWith("http://") || url.startsWith("https://")) {
        // Obtain the url from the backend
        src = url;
    } else {
        src = "/api/file?path=" + url;
    }

    switch (urlType) {
        case "image":
            return `<img src=${src} alt="Image" class="chat-bubble-multimodal-item">`;
        case "audio":
            return `<audio src=${src} controls="controls" class="chat-bubble-multimodal-item"></audio>`;
        case "video":
            return `<video src=${src} controls="controls" class="chat-bubble-multimodal-item"></video>`;
        default:
            return `<a href=${src} class="chat-bubble-multimodal-item">${url}</a>`;
    }
}

function _addUserChatRow(index, pMsg) {
    const template = chatRowUserTemplate.cloneNode(true);
    // template.querySelector('.chat-icon').
    template.querySelector(".chat-name").textContent = pMsg.name;
    let chatBubble = template.querySelector(".chat-bubble");
    chatBubble.innerHTML += marked.parse(pMsg.content);
    chatBubble.innerHTML += _renderMultiModalData(pMsg.url);
    template.querySelector(".chat-row").setAttribute("data-index", index);
    return template.firstElementChild.outerHTML;
}

function _addAssistantChatRow(index, pMsg) {
    const template = chatRowOtherTemplate.cloneNode(true);

    // If not record
    let svg_html, color;
    if (pMsg.name in nameToIconAndColor) {
        svg_html = nameToIconAndColor[pMsg.name][0];
        color = nameToIconAndColor[pMsg.name][1];
    } else {
        // First choose a svg icon
        svg_html = randomSelectAgentIcon();
        color = randomSelectColor();
        // Record the color and icon
        nameToIconAndColor[pMsg.name] = [svg_html, color];
    }
    template.querySelector(".chat-icon").innerHTML = svg_html;
    // change the background color randomly
    template.querySelector(".chat-icon").style.backgroundColor = color;

    template.querySelector(".chat-name").textContent = pMsg.name;
    let chatBubble = template.querySelector(".chat-bubble");
    chatBubble.innerHTML += marked.parse(pMsg.content);
    chatBubble.innerHTML += _renderMultiModalData(pMsg.url);
    template.querySelector(".chat-row").setAttribute("data-index", index);
    return template.firstElementChild.outerHTML;
}

function _addSystemChatRow(index, pMsg) {
    const template = chatRowSystemTemplate.cloneNode(true);
    template.querySelector(".chat-name").textContent = pMsg.name;
    let chatBubble = template.querySelector(".chat-bubble");
    chatBubble.innerHTML += marked.parse(pMsg.content);
    chatBubble.innerHTML += _renderMultiModalData(pMsg.url);
    template.querySelector(".chat-row").setAttribute("data-index", index);
    return template.firstElementChild.outerHTML;
}

function _addKeyValueInfoRow(pKey, pValue) {
    const template = infoRowTemplate.cloneNode(true);
    template.querySelector(".dialogue-info-key").textContent =
        pKey.toUpperCase();
    // Not null
    if (pValue !== null) {
        let infoValue = template.querySelector(".dialogue-info-value");
        if (pKey.toLowerCase() === 'url') {
            infoValue.style.wordBreak = 'break-all';
        }

        if (typeof pValue === 'object') {
            infoValue.textContent = JSON.stringify(pValue);
        } else {
            infoValue.textContent = pValue;
        }
    }
    return template.firstElementChild.outerHTML;
}


function _showInfoInDialogueDetailContent(data) {
    if (data === null) {
        infoClusterize.clear();
        return;
    }

    let priorityKeys = ['id', 'project', 'timestamp', 'name', 'role', 'url', 'metadata', 'content']
    // Deal with the priority keys first
    let infoRows = priorityKeys.filter(key => key in data).map(key => _addKeyValueInfoRow(key, data[key]));
    // Handle the rest of the keys
    Object.keys(data)
        .filter(key => !priorityKeys.includes(key)) // Skip the priority keys
        .forEach(key => infoRows.push(_addKeyValueInfoRow(key, data[key])));

    // Create table
    infoClusterize.update(infoRows);
}

function initializeDashboardDetailDialoguePage(pRuntimeInfo) {
    console.log("Initialize with runtime id: " + pRuntimeInfo.run_id);
    // empty the record dictionary
    nameToIconAndColor = {};

    // Load the chat template
    loadChatTemplate()
        .then(() => {
            // Initialize the detail objects
            currentRuntimeInfo = pRuntimeInfo;
            currentMsgInfo = null;
            currentAgentInfo = null;

            infoClusterize = new Clusterize({
                scrollId: "chat-detail",
                contentId: "dialogue-detail-content",
            });

            // Fetch the chat history from backend
            fetch("/api/messages/run/" + pRuntimeInfo.run_id + "?run_dir=" + pRuntimeInfo.run_dir)
                .then((response) => {
                    if (!response.ok) {
                        throw new Error("Failed to fetch messages data");
                    }
                    return response.json();
                })
                .then((data) => {
                    let send_btn = document.getElementById("chat-input-send-btn");
                    send_btn.disabled = true;
                    // Load the chat history
                    let chatRows = data.map((msg, index) => addChatRow(index, msg));
                    var clusterize = new Clusterize({
                        rows: chatRows,
                        scrollId: "chat-box",
                        contentId: "chat-box-content",
                    });

                    document.getElementById("chat-box-content");
                    addEventListener("click", function (event) {
                        let target = event.target;

                        while (target && target !== this && target instanceof Element) {
                            if (target.matches(".chat-row")) {
                                let rowIndex = target.getAttribute("data-index");
                                // Record the current message
                                currentMsgInfo = data[rowIndex];
                                // Update web ui
                                showInDetail("Message");
                                break;
                            }
                            target = target.parentNode;
                        }
                    });
                    // Load the detail content in the right panel
                    // traverse all the keys in pRuntimeInfo and create a key-value row
                    currentRuntimeInfo = pRuntimeInfo;
                    showInDetail("Runtime")

                    var socket = io();
                    socket.on("connect", () => {
                        socket.emit("join", {run_id: pRuntimeInfo.run_id});
                        send_btn.onclick = () => {
                            var message = document.getElementById(
                                "chat-input-textarea"
                            ).value;
                            socket.emit("user_input_ready", {
                                content: message,
                                run_id: pRuntimeInfo.run_id,
                            });
                            document.getElementById("chat-input-textarea").value = "";
                            document.getElementById(
                                "chat-input-send-btn"
                            ).disabled = true;
                        };
                    });
                    socket.on("display_message", (data) => {
                        if (data.run_id === pRuntimeInfo.run_id) {
                            let row = addChatRow(clusterize.getRowsAmount(), data);
                            clusterize.append([row]);
                            clusterize.refresh();
                        }
                    });
                    socket.on("enable_user_input", (data) => {
                        if (data.run_id === pRuntimeInfo.run_id) {
                            send_btn.disabled = false;
                            document.getElementById("chat-input-name").textContent =
                                data.name;
                        }
                    });
                })
                .catch((error) => {
                    console.error("Failed to fetch messages data:", error);
                });
        })
        .catch((error) => {
            console.error("Failed to load chat template:", error);
        });
}

function showInDetail(detailType) {
    document.getElementById("dialogue-info-title").innerHTML = detailType.toUpperCase();

    document.getElementById("runtimeSwitchBtn").classList.remove("selected");
    document.getElementById("msgSwitchBtn").classList.remove("selected");
    document.getElementById("agentSwitchBtn").classList.remove("selected");

    switch (detailType.toLowerCase()) {
        case "runtime":
            document.getElementById("runtimeSwitchBtn").classList.add("selected");
            _showInfoInDialogueDetailContent(currentRuntimeInfo)
            break;
        case "message":
            document.getElementById("msgSwitchBtn").classList.add("selected");
            _showInfoInDialogueDetailContent(currentMsgInfo)
            break;
        case "agent":
            document.getElementById("agentSwitchBtn").classList.add("selected");
            _showInfoInDialogueDetailContent(currentAgentInfo)
            break;
    }
}