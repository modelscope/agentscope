//TODO: move the following to chat js

let chatRowOtherTemplate, chatRowUserTemplate, infoRowTemplate;

async function loadChatTemplate() {
    const response = await fetch('static/html/chat-row-template.html');
    const htmlText = await response.text();
    const parser = new DOMParser();
    const doc = parser.parseFromString(htmlText, 'text/html');

    // save
    chatRowOtherTemplate = doc.querySelector('#chat-row-other-template').content;
    chatRowUserTemplate = doc.querySelector('#chat-row-user-template').content;
    infoRowTemplate = doc.querySelector("#dialogue-info-row-template").content;
}

// Add a chat row according to the role field in the message
function addChatRow(index, pMsg) {
    switch (pMsg.role.toLowerCase()) {
        case "user":
            return _addUserChatRow(index, pMsg)
            break;
        case "assistant":
            return _addAssistantChatRow(index, pMsg)
            break;
        case "system":
            return _addSystemChatRow(index, pMsg)
            break;
    }
}

function _determineFileType(url) {
    // Image
    let img_suffix = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp'];
    // Video
    let video_suffix = ['.mp4', '.webm', '.avi', '.mov', '.wmv', '.flv', '.f4v', '.m4v', '.rmvb', '.rm', '.3gp', '.dat', '.ts', '.mts', '.vob'];
    // Audio
    let audio_suffix = ['.mp3', '.wav', '.wma', '.ogg', '.aac', '.flac'];

    if (img_suffix.some(suffix => url.endsWith(suffix))) {
        return 'image';
    } else if (video_suffix.some(suffix => url.endsWith(suffix))) {
        return 'video';
    } else if (audio_suffix.some(suffix => url.endsWith(suffix))) {
        return 'audio';
    }
    return 'file';
}

function _renderMultiModalData(url) {
    if (!url || url === '') {
        return '';
    }
    // Determine the type of the file
    let urlType = _determineFileType(url);

    // If we need to fetch the url from the backend
    let src = null;
    if (url.startsWith("http://") || url.startsWith("https://")) {
        // Obtain the url from the backend
        src = url;
    } else {
        src = '/file?url=' + url;
    }

    switch (urlType) {
        case 'image':
            return `<img src=${src} alt="Image" class="chat-bubble-multimodal-item">`;
        case 'audio':
            return `<audio src=${src} controls="controls" class="chat-bubble-multimodal-item"></audio>`;
        case 'video':
            return `<video src=${src} controls="controls" class="chat-bubble-multimodal-item"></video>`;
        default:
            return `<a href=${src} class="chat-bubble-multimodal-item">${url}</a>`;
    }
}

function _addUserChatRow(index, pMsg) {
    const template = chatRowUserTemplate.cloneNode(true);
    // template.querySelector('.chat-icon').
    template.querySelector('.chat-name').textContent = pMsg.name;
    let chatBubble = template.querySelector('.chat-bubble');
    chatBubble.textContent = pMsg.content;
    chatBubble.innerHTML += _renderMultiModalData(pMsg.url);
    template.querySelector('.chat-row').setAttribute('data-index', index);
    return template.firstElementChild.outerHTML;
}

function _addAssistantChatRow(index, pMsg) {
    const template = chatRowOtherTemplate.cloneNode(true);
    // template.querySelector('.chat-icon').
    template.querySelector('.chat-name').textContent = pMsg.name;
    let chatBubble = template.querySelector('.chat-bubble');
    chatBubble.textContent = pMsg.content;
    chatBubble.innerHTML += _renderMultiModalData(pMsg.url);
    template.querySelector('.chat-row').setAttribute('data-index', index);
    return template.firstElementChild.outerHTML;
}

function _addSystemChatRow(index, pMsg) {
    const template = chatRowOtherTemplate.cloneNode(true);
    // template.querySelector('.chat-icon').
    template.querySelector('.chat-name').textContent = pMsg.name;
    let chatBubble = template.querySelector('.chat-bubble');
    chatBubble.textContent = pMsg.content;
    chatBubble.innerHTML += _renderMultiModalData(pMsg.url);
    template.querySelector('.chat-row').setAttribute('data-index', index);
    return template.firstElementChild.outerHTML;
}

function _addKeyValueInfoRow(pKey, pValue) {
    const template = infoRowTemplate.cloneNode(true);
    template.querySelector('.dialogue-info-key').textContent = pKey.toUpperCase();
    template.querySelector('.dialogue-info-value').textContent = pValue;
    return template.firstElementChild.outerHTML;
}

function _showInfoInDialogueDetailContent(data) {
    let infoRows = Object.keys(data).map(key => _addKeyValueInfoRow(key, data[key]));
    let infoClusterize = new Clusterize({
        rows: infoRows,
        scrollId: 'chat-detail',
        contentId: 'dialogue-detail-content'
    });
}

async function initializeDashboardDetailDialoguePage(pRuntimeInfo) {
    // Load the chat template
    await loadChatTemplate();

    // Fetch the chat history from backend
    fetch("/api/messages/" + pRuntimeInfo.id)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch messages data');
            }
            return response.json();
        })
        .then(data => {
            // Load the chat history
            let chatRows = data.map((msg, index) => addChatRow(index, msg))
            var clusterize = new Clusterize({
                rows: chatRows,
                scrollId: 'chat-box',
                contentId: 'chat-box-content'
            });

            document.getElementById('chat-box-content')
            addEventListener('click', function (event) {
                let target = event.target;

                // 检查是否点击了行元素，并获取 `data-index`
                while (target && target !== this) {
                    if (target.matches('.chat-row')) {
                        let rowIndex = target.getAttribute('data-index');
                        console.log("The " + rowIndex + " message is clicked.");
                        _showInfoInDialogueDetailContent(data[rowIndex])
                        break;
                    }
                    target = target.parentNode;
                }
            });

            // Load the detail content in the right panel
            // traverse all the keys in pRuntimeInfo and create a key-value row
            _showInfoInDialogueDetailContent(pRuntimeInfo)
        })
        .catch(error => {
            console.error('Failed to fetch messages data:', error);
        })
}
