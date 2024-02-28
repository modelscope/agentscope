const dialogList = document.getElementById('dialog-list');
const dialogInfoContent = document.getElementById('info-content');
const loggingList = document.getElementById('terminal');
const default_colors = ['#57baff', '#ff7162', '#53d29b', '#ffdd72', '#9b59b6', '#1abc9c', '#e67e22', '#95a5a6', '#34495e'];
const nameToColor = {};

$(document).ready(function () {
    // First clear dialog list
    while (dialogList.firstChild) {
        dialogList.removeChild(dialogList.firstChild);
    }

    // Clear logging terminal
    while (loggingList.firstChild) {
        loggingList.removeChild(loggingList.firstChild);
    }

    // Parse response information
    const dialogs = runInfo.dialog;
    const logging = runInfo.logging;

    if (dialogs === null) {
        dialogList.innerHTML = `<div class="empty-dialog">No file ended with ".log.chat" in ${runInfo.dir}.</div>`
    } else {
        // Append new dialog msgs
        appendDialogs(dialogs)
    }

    if (logging === null) {
        loggingList.innerHTML = `No file ended with ".log" in ${runInfo.dir}.`
    } else {
        // Append new logging info in terminal
        // TODO: for now, the logging info is only one
        //  string div, maybe we need to create a div for each
        //  line in the future.
        logging.forEach((log, index) => {
            console.log(log)
            const logElement = document.createElement('div');
            logElement.classList.add('terminal-line');
            logElement.innerHTML = `${log}`;
            loggingList.appendChild(logElement);
        });
    }

    // Init info panel
    $('#run-info').html(`
        <div class="single-line">NAME: ${runInfo.config.name}</div>
        <div class="single-line">PORJ: ${runInfo.config.project}</div>
        <div class="single-line">TIME: ${runInfo.config.timestamp}</div>`)


    // Init sidebar options
    initSidebarOption()
});

function initSidebarOption() {
    // Default option
    document.getElementById('dialogue-option').classList.add('selected');

    // Add listener to all project list items
    document.querySelectorAll('.project-list-item').forEach(div => {
        div.addEventListener('click', function () {
            // First remove .selected class from all divs
            document.querySelectorAll('.project-list-item').forEach(otherDiv => {
                otherDiv.classList.remove('selected');
            });

            // Add .selected class to this div
            this.classList.add('selected');
        });
    });
}

function getColorByName(name) {
    let color = null;
    if (name in nameToColor) {
        color = nameToColor[name];
    } else {
        // If the default color is used up, then generate a random color
        // and record to the map
        if (Object.keys(nameToColor).length >= default_colors.length) {
            color = '#' + Math.floor(Math.random() * 0xffffff).toString(16);
            nameToColor[name] = color;
        } else {
            color = default_colors[Object.keys(nameToColor).length];
        }
        // Record to the map
        nameToColor[name] = color;
    }
    return color;
}

function getMultiModalView(url) {
    // Image
    let img_suffix = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp'];
    // Video
    let video_suffix = ['.mp4', '.webm', '.avi', '.mov', '.wmv', '.flv', '.f4v', '.m4v', '.rmvb', '.rm', '.3gp', '.dat', '.ts', '.mts', '.vob'];
    // Audio
    let audio_suffix = ['.mp3', '.wav', '.wma', '.ogg', '.aac', '.flac'];

    if (img_suffix.some(suffix => url.endsWith(suffix))) {
        return `<img src=${url} alt="Image" class="msg-modal-data">`;
    } else if (video_suffix.some(suffix => url.endsWith(suffix))) {
        return `<video src=${url} controls="controls" class="msg-modal-data"></video>`;
    } else if (audio_suffix.some(suffix => url.endsWith(suffix))) {
        return `<audio src=${url} controls="controls" class="msg-modal-data"></audio>`;
    }
    return `<a href=${url} class="msg-modal-data">${url}</a>`;
}

// Create dialog
function appendDialogs(dialogs) {
    var promises = dialogs.map((dialog, index) => {
        return new Promise((resolve, reject) => {
            let htmlPath = dialog.name === "User" ? '/static/htmls/user-chat-item.html' : '/static/htmls/agent-chat-item.html';
            let color = getColorByName(dialog.name);
            let iconDataUrl = generateIcon(dialog.name[0].toUpperCase(), color);

            $.get(htmlPath, function (templateHtml) {
                // For multi-modal data
                var content = null;
                if ("url" in dialog) {
                    // Adding <img> after dialog.content
                    content = dialog.content + getMultiModalView(dialog.url);
                } else {
                    content = dialog.content;
                }

                var dialogHtml = templateHtml
                    .replace('{{name}}', dialog.name)
                    .replace('{{message}}', content)
                    .replace('{{speakerIcon}}', iconDataUrl);

                // Create a jQuery element from the HTML string to set event listeners
                var $dialogElement = $(dialogHtml);

                // Set event listeners
                // TODO: add html to a single file
                $dialogElement.on('click', function (event) {
                    event.preventDefault();
                    // Update dialog info
                    dialogInfoContent.innerHTML = `
                    <div class="info-label"><label>NAME</label></div>
                    <div class="info-block">${dialog.name}</div>

                    <div class="info-label"><label>CONTENT</label></div>
                    <div class="info-block">${dialog.content}</div>

                    <div class="info-label"><label>URLS</label></div>
                    <div class="info-block">${dialog.url || ""}</div>

                    <div class="info-label"><label>TIMESTAMP</label></div>
                    <div class="info-block">${dialog.timestamp || ""}</div>

                    <div class="info-label"><label>MODEL WRAPPER</label></div>
                    <div class="info-block">OpenAIModelWrapper</div>
                `;
                });

                resolve($dialogElement);
            });
        });
    });

    // Wait for all promises to be resolved
    Promise.all(promises).then(dialogElements => {
        dialogElements.forEach(($dialogElement) => {
            $(dialogList).append($dialogElement);
        });
    });
}

// generate icon
function generateIcon(name, color) {
    color = color || '#3498db'; // 设置默认颜色值

    // Create canvas
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');

    // Set canvas with & height
    canvas.width = 100;
    canvas.height = 100;

    // Draw background
    context.fillStyle = color;
    context.fillRect(0, 0, canvas.width, canvas.height);

    // Draw text
    context.fillStyle = 'white';
    context.font = 'bold 40px Arial';
    context.textAlign = 'center';
    context.textBaseline = 'middle';

    // Calculate x & y coordinates
    const textX = canvas.width / 2;
    const textY = canvas.height / 2;
    context.fillText(name, textX, textY);

    // Turn canvas into data URL
    return canvas.toDataURL();
}
