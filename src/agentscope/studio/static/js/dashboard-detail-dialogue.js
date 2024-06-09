let chatRowOtherTemplate,
    chatRowUserTemplate,
    chatRowSystemTemplate,
    infoRowTemplate;

let currentRuntimeInfo, currentMsgInfo, currentAgentInfo;

let randomNumberGenerator;

let infoClusterize;

let inputFileList = document.getElementById("chat-control-file-list");

let waitForUserInput = false;
let userInputRequest = null;

const agentIcons = [
    '<path d="M21.344 448h85.344v234.656H21.344V448zM554.656 192h64V106.656h-213.344V192h64v42.656h-320V896h725.344V234.656h-320V192z m234.688 128v490.656H234.688V320h554.656zM917.344 448h85.344v234.656h-85.344V448z"></path><path d="M341.344 512H448v106.656h-106.656V512zM576 512h106.656v106.656H576V512z"></path>',
    '<path d="M576 85.333333c0 18.944-8.234667 35.968-21.333333 47.701334V213.333333h213.333333a128 128 0 0 1 128 128v426.666667a128 128 0 0 1-128 128H256a128 128 0 0 1-128-128V341.333333a128 128 0 0 1 128-128h213.333333V133.034667A64 64 0 1 1 576 85.333333zM256 298.666667a42.666667 42.666667 0 0 0-42.666667 42.666666v426.666667a42.666667 42.666667 0 0 0 42.666667 42.666667h512a42.666667 42.666667 0 0 0 42.666667-42.666667V341.333333a42.666667 42.666667 0 0 0-42.666667-42.666666H256z m-170.666667 128H0v256h85.333333v-256z m853.333334 0h85.333333v256h-85.333333v-256zM384 618.666667a64 64 0 1 0 0-128 64 64 0 0 0 0 128z m256 0a64 64 0 1 0 0-128 64 64 0 0 0 0 128z"></path>',
    '<path d="M175.776914 292.571429h371.741257l35.108572-58.397258h-181.8624c-16.442514 0-18.783086-13.370514-14.628572-21.152914 12.873143-24.049371 39.7312-75.776 80.574172-155.2384 16.676571-23.610514 35.050057-35.401143 55.149714-35.401143 24.341943 0 35.693714 11.790629 34.026057 35.401143l-58.133943 116.9408c106.232686-1.404343 164.571429-1.404343 175.016229 0 8.192 1.082514 11.117714 0.321829 17.6128 10.532572 6.524343 10.210743-0.117029 14.1312 0 18.519771-8.250514 14.511543-12.756114 21.884343-17.6128 30.398171C648.8064 273.934629 635.582171 292.571429 645.12 292.571429h203.893029c11.849143 0 44.763429-3.861943 66.472228 22.293942 14.453029 17.437257 21.357714 39.789714 20.743314 66.998858 0.468114 116.677486 0.702171 184.290743 0.702172 202.839771 0 3.803429 19.0464-69.485714 57.841371-33.850514 17.642057 34.289371 21.328457 163.050057 0 209.832228C965.485714 813.290057 936.930743 729.673143 936.228571 732.511086c0 0 0.702171 109.626514 0.702172 177.005714 0 6.144 4.973714 38.5024-21.445486 62.142171-17.6128 15.798857-39.789714 23.610514-66.472228 23.522743l-703.429486-6.465828c-19.456-2.984229-34.523429-12.170971-45.290057-27.589486-10.708114-15.389257-14.921143-33.850514-12.522057-55.413029v-173.202285c-18.870857 33.938286-38.239086 43.680914-58.046172 29.257143C0 740.205714-3.042743 578.384457 27.735771 556.383086c20.509257-14.687086 40.521143-5.266286 60.035658 28.350171v-202.810514c0-27.326171 9.8304-49.649371 29.461942-66.998857 19.6608-17.378743 39.175314-24.810057 58.514286-22.3232zM175.542857 380.342857v526.628572h672.914286V380.342857H175.542857z"></path><path d="M365.714286 658.285714m-73.142857 0a73.142857 73.142857 0 1 0 146.285714 0 73.142857 73.142857 0 1 0-146.285714 0Z"></path><path d="M687.542857 658.285714m-73.142857 0a73.142857 73.142857 0 1 0 146.285714 0 73.142857 73.142857 0 1 0-146.285714 0Z"></path>',
    '<path d="M745.216 896H278.784a117.888 117.888 0 0 1-108.117-125.653V509.696a117.888 117.888 0 0 1 108.117-125.653h466.432a117.888 117.888 0 0 1 108.117 125.653v260.65A117.888 117.888 0 0 1 745.216 896z m-446.55-426.667A45.824 45.824 0 0 0 256 512v256a45.824 45.824 0 0 0 42.667 42.667h426.666c21.334-1.707 44.16-14.251 42.667-35.755V512a45.824 45.824 0 0 0-42.667-42.667z"></path><path d="M384 554.667q42.667 0 42.667 42.666v85.334q0 42.666-42.667 42.666t-42.667-42.666v-85.334q0-42.666 42.667-42.666zM640 554.667q42.667 0 42.667 42.666v85.334q0 42.666-42.667 42.666t-42.667-42.666v-85.334q0-42.666 42.667-42.666zM511.787 298.027l-42.667 128h85.333z"></path><path d="M598.485 164.864l-24.917 24.917a148.821 148.821 0 0 0-83.03-132.864s-8.533 91.35-49.834 124.544-124.587 132.864 41.515 207.574a98.133 98.133 0 0 1-28.203-85.334 98.133 98.133 0 0 1 53.12-72.533 69.419 69.419 0 0 0 33.28 66.432c41.6 33.152 0 91.35 0 91.35s199.253-49.707 58.07-224.086zM84.267 512H86.4q41.6 0 41.6 41.6v172.8q0 41.6-41.6 41.6h-2.133q-41.6 0-41.6-41.6V553.6q0-41.6 41.6-41.6zM937.6 512h2.133q41.6 0 41.6 41.6v172.8q0 41.6-41.6 41.6H937.6q-41.6 0-41.6-41.6V553.6q0-41.6 41.6-41.6z"></path>',
    '<path d="M512 32c-35.36 0-64 28.64-64 64 0 23.616 12.864 43.872 32 55.008V224h-160c-88 0-160 72-160 160v64H64v256h96v160h704v-160h96v-256h-96v-64c0-88-72-160-160-160h-160V151.008c19.136-11.136 32-31.36 32-55.008 0-35.36-28.64-64-64-64z m-192 256h384c53.376 0 96 42.624 96 96v416h-64v-160H288v160H224V384c0-53.376 42.624-96 96-96z m64 128a63.968 63.968 0 1 0 0 128 63.968 63.968 0 1 0 0-128z m256 0a63.968 63.968 0 1 0 0 128 63.968 63.968 0 1 0 0-128zM128 512h32v128H128z m736 0h32v128h-32z m-512 192h64v96h-64z m128 0h64v96h-64z m128 0h64v96h-64z"></path>',
    '<path d="M699.733333 89.6c21.333333 8.533333 29.866667 34.133333 21.333334 51.2v4.266667L665.6 256H725.333333c89.6 0 166.4 72.533333 170.666667 162.133333v8.533334h42.666667c46.933333 0 85.333333 38.4 85.333333 85.333333v170.666667c0 46.933333-38.4 85.333333-85.333333 85.333333h-42.666667c0 93.866667-76.8 170.666667-170.666667 170.666667H298.666667c-93.866667 0-170.666667-76.8-170.666667-170.666667H85.333333c-46.933333 0-85.333333-38.4-85.333333-85.333333v-170.666667c0-46.933333 38.4-85.333333 85.333333-85.333333h42.666667c0-93.866667 76.8-170.666667 170.666667-170.666667h59.733333L302.933333 145.066667c-8.533333-17.066667 0-42.666667 21.333334-55.466667 17.066667-8.533333 42.666667-4.266667 51.2 17.066667l4.266666 4.266666L452.266667 256h119.466666l72.533334-145.066667 4.266666-4.266666c8.533333-21.333333 34.133333-25.6 51.2-17.066667zM725.333333 341.333333H298.666667c-46.933333 0-81.066667 34.133333-85.333334 81.066667V768c0 46.933333 34.133333 81.066667 81.066667 85.333333H725.333333c46.933333 0 81.066667-34.133333 85.333334-81.066666V426.666667c0-46.933333-34.133333-81.066667-81.066667-85.333334H725.333333zM128 512H85.333333v170.666667h42.666667v-170.666667z m810.666667 0h-42.666667v170.666667h42.666667v-170.666667zM384 512c25.6 0 42.666667 17.066667 42.666667 42.666667v85.333333c0 25.6-17.066667 42.666667-42.666667 42.666667s-42.666667-17.066667-42.666667-42.666667v-85.333333c0-25.6 17.066667-42.666667 42.666667-42.666667z m256 0c25.6 0 42.666667 17.066667 42.666667 42.666667v85.333333c0 25.6-17.066667 42.666667-42.666667 42.666667s-42.666667-17.066667-42.666667-42.666667v-85.333333c0-25.6 17.066667-42.666667 42.666667-42.666667z"></path>',
];

let nameToIconAndColor = {};

hljs.highlightAll();

const marked_options = {
    gfm: true,
    breaks: true,
    pedantic: false,
};

marked.use({
    renderer: {
        code(code, infostring, escaped) {
            const language = infostring
                ? hljs.getLanguage(infostring)
                    ? infostring
                    : "plaintext"
                : "plaintext";
            // Use Highlight.js to highlight code blocks
            return `<pre><code class="hljs ${language}">${
                hljs.highlight(code, {language}).value
            }</code></pre>`;
        },
    },
});

function randomSelectAgentIcon() {
    return agentIcons[Math.floor(randomNumberGenerator.nextFloat() * agentIcons.length)];
}

function randomIntFromInterval(min, max) {
    return Math.floor(randomNumberGenerator.nextFloat() * (max - min + 1) + min);
}

function hslToHex(h, s, l) {
    l /= 100;
    const a = (s * Math.min(l, 1 - l)) / 100;
    const f = (n) => {
        const k = (n + h / 30) % 12;
        const color = l - a * Math.max(Math.min(k - 3, 9 - k, 1), -1);
        return Math.round(255 * color)
            .toString(16)
            .padStart(2, "0"); // 转换为16进制并补零
    };
    return `#${f(0)}${f(8)}${f(4)}`;
}

function randomSelectColor() {
    const h = randomIntFromInterval(0, 360); // 色相：0°到360°
    const s = randomIntFromInterval(50, 100); // 饱和度：50%到100%
    const l = randomIntFromInterval(25, 75); // 亮度：25%到75%
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
        case "system":
            return _addSystemChatRow(index, pMsg);
        case "assistant":
            return _addAssistantChatRow(index, pMsg);
        default:
            console.error("Unknown role: " + pMsg.role);
            return _addAssistantChatRow(index, pMsg);
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

function _getMultiModalComponent(url) {
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

// Render multiple urls in a chat bubble
function _renderMultiModalUrls(urls) {
    if (urls == null || urls === "") {
        return ""
    }

    if (typeof urls === "string") {
        urls = [urls]
    }

    if (Array.isArray(urls) && urls.length > 0) {
        let innerHtml = "";
        for (let i = 0; i < urls.length; i++) {
            innerHtml += _getMultiModalComponent(urls[i]);
        }
        return innerHtml;
    } else {
        return ""
    }
}

function _addUserChatRow(index, pMsg) {
    const template = chatRowUserTemplate.cloneNode(true);
    // template.querySelector('.chat-icon').
    template.querySelector(".chat-name").textContent = pMsg.name;
    let chatBubble = template.querySelector(".chat-bubble");
    chatBubble.textContent += pMsg.content;
    chatBubble.innerHTML += _renderMultiModalUrls(pMsg.url);
    template.querySelector(".chat-row").setAttribute("data-index", index);
    template
        .querySelector(".chat-row")
        .setAttribute("data-msg", JSON.stringify(pMsg));
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
    chatBubble.innerHTML += marked.parse(pMsg.content, marked_options);
    chatBubble.innerHTML += _renderMultiModalUrls(pMsg.url);
    template.querySelector(".chat-row").setAttribute("data-index", index);
    template
        .querySelector(".chat-row")
        .setAttribute("data-msg", JSON.stringify(pMsg));
    return template.firstElementChild.outerHTML;
}

function _addSystemChatRow(index, pMsg) {
    const template = chatRowSystemTemplate.cloneNode(true);
    template.querySelector(".chat-name").textContent = pMsg.name;
    let chatBubble = template.querySelector(".chat-bubble");
    chatBubble.innerHTML += marked.parse(pMsg.content, marked_options);
    chatBubble.innerHTML += _renderMultiModalUrls(pMsg.url);
    template.querySelector(".chat-row").setAttribute("data-index", index);
    template
        .querySelector(".chat-row")
        .setAttribute("data-msg", JSON.stringify(pMsg));

    return template.firstElementChild.outerHTML;
}

function _addKeyValueInfoRow(pKey, pValue) {
    const template = infoRowTemplate.cloneNode(true);
    template.querySelector(".dialogue-info-key").textContent =
        pKey.toUpperCase();
    // Not null
    if (pValue !== null) {
        let infoValue = template.querySelector(".dialogue-info-value");
        if (pKey.toLowerCase() === "url") {
            infoValue.style.wordBreak = "break-all";
        }

        if (typeof pValue === "object") {
            infoValue.textContent = JSON.stringify(pValue);
        } else {
            infoValue.textContent = pValue;
        }
    }
    return template.firstElementChild.outerHTML;
}

function disableInput() {
    document.getElementById("chat-control-url-btn").disabled = true;
    document.getElementById("chat-control-send-btn").disabled = true;
}

function activateInput() {
    document.getElementById("chat-control-url-btn").disabled = false;
    document.getElementById("chat-control-send-btn").disabled = false;
}

function _showInfoInDialogueDetailContent(data) {
    if (data === null) {
        infoClusterize.clear();
        return;
    }

    let priorityKeys = [
        "run_id",
        "id",
        "project",
        "name",
        "timestamp",
        "role",
        "url",
        "metadata",
        "content",
    ];
    // Deal with the priority keys first
    let infoRows = priorityKeys
        .filter((key) => key in data)
        .map((key) => _addKeyValueInfoRow(key, data[key]));
    // Handle the rest of the keys
    Object.keys(data)
        .filter((key) => !priorityKeys.includes(key)) // Skip the priority keys
        .forEach((key) => infoRows.push(_addKeyValueInfoRow(key, data[key])));

    // Create table
    infoClusterize.update(infoRows);
}

function _obtainAllUrlFromFileList() {
    let urls = [];
    for (let i = 0; i < inputFileList.children.length; i++) {
        // obtain from the title attribute
        urls.push(inputFileList.children[i].title);
    }
    return urls;
}

function addFileListItem(url) {
    let svg;
    switch (_determineFileType(url)) {
        case "image":
            svg = `<svg viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg" >
                <path d="M160 0h512l256 256v704c0 35.3472-28.6528 64-64 64H160c-35.3472 0-64-28.6528-64-64V64c0-35.3472 28.6528-64 64-64z" fill="#F6AD00"></path>
                <path d="M258.528 742.0672L351.8336 604.928a14.5024 14.5024 0 0 1 22.1696-2.1824l61.664 60.416 135.296-212.064a14.5024 14.5024 0 0 1 24.8064 0.5568l168.1024 291.328a14.5024 14.5024 0 0 1-12.5696 21.7664H270.528a14.5024 14.5024 0 0 1-12.0064-22.6816z" fill="#FFF7F7"></path>
                <path d="M359.616 431.5456m-73.1456 0a73.1456 73.1456 0 1 0 146.2912 0 73.1456 73.1456 0 1 0-146.2912 0Z" fill="#FFFFFF"></path>
                <path d="M672 0l256 256h-192c-35.3472 0-64-28.6528-64-64V0z" fill="#FBDE99"></path>
            </svg>`;
            break;
        case "video":
            svg = `<svg viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg">
                <path d="M160 0h512l256 256v704c0 35.3472-28.6528 64-64 64H160c-35.3472 0-64-28.6528-64-64V64c0-35.3472 28.6528-64 64-64z" fill="#7C8EEE"></path>
                <path d="M702.2976 579.2896l-298.5664 177.984c-19.9488 12.0192-45.3312-2.4128-45.3312-25.856v-355.968c0-22.848 25.3824-37.2736 45.3312-25.856l298.56 177.984c19.3408 12.032 19.3408 40.288 0 51.712z" fill="#FFFFFF"></path>
                <path d="M672 0l256 256h-192c-35.3472 0-64-28.6528-64-64V0z" fill="#CAD1F8"></path>
            </svg>`;
            break;
        case "audio":
            svg = `<svg viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg"><path d="M160 0h512l256 256v704c0 35.3472-28.6528 64-64 64H160c-35.3472 0-64-28.6528-64-64V64c0-35.3472 28.6528-64 64-64z" fill="#F16C00" p-id="1463"></path><path d="M727.8016 510.9952a58.7456 58.7456 0 0 1-8.8 21.1392c-3.4944 5.312-7.04 8.8704-10.592 7.0656-3.4944 0-5.2992-22.944-6.9952-26.5024a68.5376 68.5376 0 0 1-5.2928-19.392c-1.7536-14.1184-7.0464-26.5472-15.8976-31.808-8.7936-7.0592-21.0816-12.3712-36.9728-15.936a116.0896 116.0896 0 0 1-47.5776-21.1328c-14.0864-10.624-29.9264-19.4368-38.72-30.0608-8.8512-8.8128-15.8976-10.624-19.392-8.8128-5.2992 1.7536-7.0464 7.0656-7.0464 12.3712v328.48c0 8.8704-1.7472 19.4368-5.2992 30.0608-3.4944 10.624-5.2992 21.184-14.0928 31.7568-8.7936 10.624-21.1328 17.6832-36.9728 24.7488-15.8976 7.0656-35.232 10.624-56.4224 12.3712a127.7184 127.7184 0 0 1-63.4112-12.3712 126.4384 126.4384 0 0 1-44.0256-33.568c-10.592-14.1248-15.8912-28.2496-15.8912-45.9392 0-15.872 7.104-31.7568 22.9376-45.888 14.0928-14.1248 29.9328-24.7424 47.5712-30.0544 17.5936-5.312 33.4848-8.8128 49.3248-8.8128 15.8912 0 40.5248 0 52.864 3.552 12.2944 3.5072 21.1456 5.312 28.1856 7.0656V346.688c0-10.624 3.5008-19.392 8.8-26.4512 5.2928-7.0656 14.0864-10.624 22.88-12.3712 8.8512-1.7536 15.8976 0 21.1904 5.312 5.2992 3.5008 0 10.6176 6.9952 17.6256 5.2992 7.0656 12.3456 15.936 21.1904 26.5024 8.7936 10.624 19.3344 19.4368 33.4272 28.256 12.3456 8.8128 22.9376 14.1248 31.7312 19.4368 8.8 3.5072 17.6448 7.0656 24.6912 10.624 7.04 3.5008 15.84 7.008 22.8864 12.32 7.04 5.312 15.8912 12.3712 24.6336 22.9952 8.8448 10.624 14.0928 19.3856 15.8912 30.0032 0 10.624 0 21.1904-1.7984 30.0096v0.0512z" fill="#FFFFFF" p-id="1464"></path><path d="M672 0l256 256h-192c-35.3472 0-64-28.6528-64-64V0z" fill="#F9C499" p-id="1465"></path></svg>`;
            break;
        default:
            svg = `<svg viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg"><path d="M160 0h512l256 256v704c0 35.3472-28.6528 64-64 64H160c-35.3472 0-64-28.6528-64-64V64c0-35.3472 28.6528-64 64-64z" fill="#CCCCCC" p-id="1633"></path><path d="M672 0l256 256h-192c-35.3472 0-64-28.6528-64-64V0z" fill="#EAEAEA" p-id="1634"></path><path d="M384 499.2c0-25.6 5.12-46.08 10.24-58.88 5.12-12.8 15.36-25.6 28.16-35.84 12.8-12.8 25.6-20.48 43.52-25.6 15.36-5.12 30.72-7.68 48.64-7.68 35.84 0 64 10.24 89.6 30.72C627.2 422.4 640 448 640 481.28c0 15.36-5.12 28.16-10.24 40.96s-17.92 28.16-38.4 46.08-28.16 30.72-35.84 38.4c-7.68 7.68-10.24 17.92-15.36 28.16-5.12 10.24-2.56 17.92-2.56 43.52h-51.2c0-25.6 2.56-38.4 5.12-51.2s7.68-23.04 15.36-33.28 15.36-23.04 33.28-40.96c17.92-17.92 30.72-30.72 35.84-38.4 5.12-7.68 10.24-20.48 10.24-38.4s-7.68-30.72-20.48-43.52-30.72-20.48-53.76-20.48c-51.2 0-76.8 35.84-76.8 87.04h-51.2z m153.6 281.6h-51.2v-51.2h51.2v51.2z" fill="#FFFFFF" p-id="1635"></path></svg>`;
            break;
    }

    let newItem = document.createElement("div");
    newItem.classList.add("chat-control-file-item");
    newItem.innerHTML = svg;
    newItem.title = url;

    // Delete btn
    const deleteBtn = document.createElement("div");
    deleteBtn.classList.add("chat-control-file-delete");
    // deleteBtn.innerHTML = `<svg viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg"><path d="M470.4256 524.8L280.064 334.4384A38.4512 38.4512 0 0 1 334.4384 280.064l190.3616 190.3616 190.3616-190.3616a38.4512 38.4512 0 1 1 54.3744 54.3744l-190.3616 190.3616 190.3616 190.3616a38.4512 38.4512 0 0 1-54.3744 54.3744l-190.3616-190.3616-190.3616 190.3616a38.4512 38.4512 0 0 1-54.3744-54.3744l190.3616-190.3616z"></path></svg>`;
    deleteBtn.innerHTML = `<svg viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg"><path d="M643.18 513.392 993.102 176.172c34.278-33.03 34.278-86.586 0-119.616l-15.514-14.952c-34.278-33.03-89.848-33.03-124.126 0L512.124 370.552 170.784 41.604c-34.276-33.03-89.848-33.03-124.122 0l-15.518 14.952c-34.274 33.03-34.274 86.586 0 119.616L380.84 513.172 30.918 850.39c-34.274 33.03-34.274 86.586 0 119.616l15.514 14.956c34.278 33.028 89.85 33.028 124.126 0l341.338-328.946 341.34 328.946c34.276 33.028 89.848 33.028 124.122 0l15.518-14.956c34.274-33.03 34.274-86.586 0-119.616L643.18 513.392z"></path></svg>`;
    deleteBtn.onclick = function () {
        inputFileList.removeChild(newItem);
    };
    newItem.appendChild(deleteBtn);

    inputFileList.appendChild(newItem);
    inputFileList.scrollLeft =
        inputFileList.scrollWidth - inputFileList.clientWidth;
}

function _showUrlPrompt() {
    const userInput = prompt("Please enter a local or web URL:", "");

    if (userInput !== null && userInput !== "") {
        addFileListItem(userInput);
    }
}

function _isMacOS() {
    return navigator.platform.toUpperCase().indexOf("MAC") >= 0;
}

function initializeDashboardDetailDialoguePage(pRuntimeInfo) {
    console.log("Initialize with runtime id: " + pRuntimeInfo.run_id);

    // Initialize the random seed generator by run_id
    randomNumberGenerator = new SeededRand(_hashStringToSeed(pRuntimeInfo.run_id));

    // Reset the flag
    waitForUserInput = false;

    // Empty the record dictionary
    nameToIconAndColor = {};

    let sendBtn = document.getElementById(
        "chat-control-send-btn"
    );

    let inputTextArea = document.getElementById(
        "chat-input-textarea"
    )

    inputTextArea.addEventListener("keydown", function (e) {
        if (e.key === "Enter" && !e.ctrlKey && !e.metaKey) {
            e.preventDefault();

            if (sendBtn.disabled === false) {
                sendBtn.click();
            }
        } else if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
            e.preventDefault();

            let cursorPosition = inputTextArea.selectionStart;
            let textBeforeCursor = inputTextArea.value.substring(0, cursorPosition);
            let textAfterCursor = inputTextArea.value.substring(cursorPosition);

            inputTextArea.value = textBeforeCursor + "\n" + textAfterCursor;

            // Update the cursor position
            inputTextArea.selectionStart = inputTextArea.selectionEnd = cursorPosition + 1;
        }
    })

    // Set the placeholder according to the platform
    if (_isMacOS()) {
        inputTextArea.placeholder = "Input message here, ⌘ + Enter for new line";
    } else {
        inputTextArea.placeholder = "Input message here, Ctrl + Enter for new line";
    }

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

            disableInput();

            // Fetch the chat history from backend
            fetch(
                "/api/messages/run/" +
                pRuntimeInfo.run_id +
                "?run_dir=" +
                pRuntimeInfo.run_dir
            )
                .then((response) => {
                    if (!response.ok) {
                        throw new Error("Failed to fetch messages data");
                    }
                    return response.json();
                })
                .then((data) => {
                    // Load the chat history
                    let chatRows = data.map((msg, index) =>
                        addChatRow(index, msg)
                    );
                    var clusterize = new Clusterize({
                        rows: chatRows,
                        scrollId: "chat-box",
                        contentId: "chat-box-content",
                    });

                    document.getElementById("chat-box-content");
                    addEventListener("click", function (event) {
                        let target = event.target;

                        while (
                            target &&
                            target !== this &&
                            target instanceof Element
                        ) {
                            if (target.matches(".chat-row")) {
                                // Record the current message
                                currentMsgInfo = JSON.parse(
                                    target.getAttribute("data-msg")
                                );

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
                    showInDetail("Runtime");

                    var socket = io();
                    socket.on("connect", () => {
                        // Tell flask server the web ui is ready
                        socket.emit("join", {run_id: pRuntimeInfo.run_id});

                        sendBtn.onclick = () => {
                            var message = document.getElementById(
                                "chat-input-textarea"
                            ).value;

                            if (message === "") {
                                alert("Please input a message!");
                                return;
                            }

                            // Send the message to the flask server according to the current request
                            let url = _obtainAllUrlFromFileList();
                            socket.emit("user_input_ready", {
                                run_id: userInputRequest.run_id,
                                agent_id: userInputRequest.agent_id,
                                name: userInputRequest.name,
                                url: url,
                                content: message,
                            });
                            // Finish a user input
                            while (inputFileList.firstChild) {
                                inputFileList.removeChild(inputFileList.firstChild);
                            }

                            waitForUserInput = false;

                            console.log("Studio: send user_input_ready");

                            document.getElementById(
                                "chat-input-textarea"
                            ).value = "";
                            disableInput();
                        };
                    });
                    socket.on("display_message", (data) => {
                        if (data.run_id === pRuntimeInfo.run_id) {
                            console.log("Studio: receive display_message");
                            let row = addChatRow(
                                clusterize.getRowsAmount(),
                                data
                            );
                            clusterize.append([row]);
                            clusterize.refresh();

                            var scrollElem =
                                document.getElementById("chat-box");
                            scrollElem.scrollTop = scrollElem.scrollHeight;
                        }
                    });
                    socket.on("enable_user_input", (data) => {
                        // Require user input in web ui
                        console.log("Studio: receive enable_user_input");

                        // If already waiting for user input, just abort the request
                        if (!waitForUserInput) {
                            // If not waiting for user input, enable the send button
                            waitForUserInput = true;
                            // Record the current request
                            userInputRequest = data;
                            activateInput();
                            document.getElementById(
                                "chat-input-name"
                            ).textContent = data.name;
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
    document.getElementById("dialogue-info-title").innerHTML =
        detailType.toUpperCase();

    document.getElementById("runtimeSwitchBtn").classList.remove("selected");
    document.getElementById("msgSwitchBtn").classList.remove("selected");
    document.getElementById("agentSwitchBtn").classList.remove("selected");

    switch (detailType.toLowerCase()) {
        case "runtime":
            document
                .getElementById("runtimeSwitchBtn")
                .classList.add("selected");
            _showInfoInDialogueDetailContent(currentRuntimeInfo);
            break;
        case "message":
            document.getElementById("msgSwitchBtn").classList.add("selected");
            _showInfoInDialogueDetailContent(currentMsgInfo);
            break;
        case "agent":
            document.getElementById("agentSwitchBtn").classList.add("selected");
            _showInfoInDialogueDetailContent(currentAgentInfo);
            break;
    }
}

function _hashStringToSeed(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        const char = str.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash; // Turn it into a 32bit integer
    }
    return hash;
}

// Linear congruential generator
class SeededRand {
    constructor(seed) {
        this.modulus = 2147483648; // 2**31
        this.multiplier = 48271; // 常数
        this.increment = 0; // 常数
        this.seed = seed % this.modulus;
        if (this.seed <= 0) this.seed += this.modulus - 1;
    }

    nextFloat() {
        this.seed = (this.seed * this.multiplier + this.increment) % this.modulus;
        return this.seed / this.modulus;
    }
}