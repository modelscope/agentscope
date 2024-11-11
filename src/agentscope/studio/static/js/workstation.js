let editor;
let currentZIndex = 0;

let mobile_item_selec;
let mobile_last_move;

let importQueue;
let dataToImportStep;
let currentImportIndex;
let accumulatedImportData;
let descriptionStep;


let nameToHtmlFile = {
    'welcome': 'welcome.html',
    'dashscope_chat': 'model-dashscope-chat.html',
    'openai_chat': 'model-openai-chat.html',
    'post_api_chat': 'model-post-api-chat.html',
    'post_api_dall_e': 'model-post-api-dall-e.html',
    'Message': 'message-msg.html',
    'DialogAgent': 'agent-dialogagent.html',
    'UserAgent': 'agent-useragent.html',
    'DictDialogAgent': 'agent-dictdialogagent.html',
    'ReActAgent': 'agent-reactagent.html',
    'Placeholder': 'pipeline-placeholder.html',
    'MsgHub': 'pipeline-msghub.html',
    'SequentialPipeline': 'pipeline-sequentialpipeline.html',
    'ForLoopPipeline': 'pipeline-forlooppipeline.html',
    'WhileLoopPipeline': 'pipeline-whilelooppipeline.html',
    'IfElsePipeline': 'pipeline-ifelsepipeline.html',
    'SwitchPipeline': 'pipeline-switchpipeline.html',
    'BingSearchService': 'service-bing-search.html',
    'GoogleSearchService': 'service-google-search.html',
    'PythonService': 'service-execute-python.html',
    'ReadTextService': 'service-read-text.html',
    'WriteTextService': 'service-write-text.html',
}

// Cache the loaded html files
let htmlCache = {};

// When clicking the sidebar item, it will expand/collapse the next content
function onClickSidebarSubItem(element) {
    element.classList.toggle("active");
    let content = element.nextElementSibling;
    if (content.style.display === "block") {
        content.style.display = "none";
    } else {
        content.style.display = "block";
    }
}


// Load html source code dynamically
async function fetchHtml(fileName) {
    try {
        let filePath = 'static/html-drag-components/' + fileName;
        const response = await fetch(filePath);
        if (!response.ok) {
            throw new Error('Fail to load ' + filePath);
        }
        return await response.text();
    } catch (error) {
        return error;
    }
}


async function initializeWorkstationPage() {
    console.log("Initialize Workstation Page")
    // Initialize the Drawflow editor
    let id = document.getElementById("drawflow");
    editor = new Drawflow(id);
    editor.reroute = true;
    editor.createCurvature = function createCurvature(start_pos_x, start_pos_y, end_pos_x, end_pos_y, curvature_value, type) {
        var line_x = start_pos_x;
        var line_y = start_pos_y;
        var x = end_pos_x;
        var y = end_pos_y;
        var curvature = curvature_value;
        //type openclose open close other
        switch (type) {
            case 'open':
                if (start_pos_x >= end_pos_x) {
                    var hx1 = line_x + Math.abs(x - line_x) * curvature;
                    var hx2 = x - Math.abs(x - line_x) * (curvature * -1);
                } else {
                    var hx1 = line_x + Math.abs(x - line_x) * curvature;
                    var hx2 = x - Math.abs(x - line_x) * curvature;
                }
                return ' M ' + line_x + ' ' + line_y + ' C ' + hx1 + ' ' + line_y + ' ' + hx2 + ' ' + y + ' ' + x + '  ' + y;

            case 'close':
                if (start_pos_x >= end_pos_x) {
                    var hx1 = line_x + Math.abs(x - line_x) * (curvature * -1);
                    var hx2 = x - Math.abs(x - line_x) * curvature;
                } else {
                    var hx1 = line_x + Math.abs(x - line_x) * curvature;
                    var hx2 = x - Math.abs(x - line_x) * curvature;
                }                                                                                                                  //M0 75H10L5 80L0 75Z
                return ' M ' + line_x + ' ' + line_y + ' C ' + hx1 + ' ' + line_y + ' ' + hx2 + ' ' + y + ' ' + x + '  ' + y + ' M ' + (x - 11) + ' ' + y + ' L' + (x - 20) + ' ' + (y - 5) + '  L' + (x - 20) + ' ' + (y + 5) + 'Z';

            case 'other':
                if (start_pos_x >= end_pos_x) {
                    var hx1 = line_x + Math.abs(x - line_x) * (curvature * -1);
                    var hx2 = x - Math.abs(x - line_x) * (curvature * -1);
                } else {
                    var hx1 = line_x + Math.abs(x - line_x) * curvature;
                    var hx2 = x - Math.abs(x - line_x) * curvature;
                }
                return ' M ' + line_x + ' ' + line_y + ' C ' + hx1 + ' ' + line_y + ' ' + hx2 + ' ' + y + ' ' + x + '  ' + y;

            default:
                var hx1 = line_x + Math.abs(x - line_x) * curvature;
                var hx2 = x - Math.abs(x - line_x) * curvature;

                return ' M ' + line_x + ' ' + line_y + ' C ' + hx1 + ' ' + line_y + ' ' + hx2 + ' ' + y + ' ' + x + '  ' + y + ' M ' + (x - 11) + ' ' + y + ' L' + (x - 20) + ' ' + (y - 5) + '  L' + (x - 20) + ' ' + (y + 5) + 'Z';
        }
    }
    editor.start();
    editor.zoom_out();

    let welcome = await fetchHtml('welcome.html');
    const welcomeID = editor.addNode('welcome', 0, 0, 50, 50, 'welcome', {}, welcome);
    setupNodeListeners(welcomeID);

    editor.on('nodeCreated', function (id) {
        console.log("Node created " + id);
        disableButtons();
        makeNodeTop(id);
        setupNodeListeners(id);
        setupNodeCopyListens(id);
        addEventListenersToNumberInputs(id);
        setupTextInputListeners(id);
    })

    editor.on('nodeRemoved', function (id) {
        console.log("Node removed " + id);
        disableButtons();
        Object.keys(editor.drawflow.drawflow[editor.module].data).forEach(nodeKey => {
            var node = editor.drawflow.drawflow[editor.module].data[nodeKey];
            var nodeData =
                editor.drawflow.drawflow[editor.module].data[nodeKey].data;
            console.log("nodeKey", nodeKey);
            console.log("node", node);
            console.log("nodeData", nodeData);
            console.log("id", id);

            if (nodeData && nodeData.copies) {
                console.log("Array.isArray(nodeData.copies)", Array.isArray(nodeData.copies))
                if (nodeData.copies.includes(id)) {
                    console.log("nodeData.copies", nodeData.copies);
                    console.log("nodeData.copies.includes(id)",
                        nodeData.copies.includes(id));
                    var index = nodeData.copies.indexOf(id);
                    console.log("index", index);
                    if (index > -1) {
                        nodeData.copies.splice(index, 1);
                        editor.updateNodeDataFromId(nodeKey, nodeData);
                    }
                }
            }
        })
    })

    editor.on('nodeSelected', function (id) {
        console.log("Node selected " + id);
        makeNodeTop(id);
    })

    editor.on('moduleCreated', function (name) {
        console.log("Module Created " + name);
    })

    editor.on('moduleChanged', function (name) {
        console.log("Module Changed " + name);
    })

    editor.on('connectionCreated', function (connection) {
        console.log('Connection created');
        console.log(connection);
        disableButtons();
    })

    editor.on('connectionRemoved', function (connection) {
        console.log('Connection removed');
        console.log(connection);
        disableButtons();
    })

    editor.on('mouseMove', function (position) {
        // console.log('Position mouse x:' + position.x + ' y:' + position.y);
    })

    editor.on('nodeMoved', function (id) {
        console.log("Node moved " + id);
        disableButtons();
    })

    editor.on('zoom', function (zoom) {
        console.log('Zoom level ' + zoom);
    })

    editor.on('translate', function (position) {
        console.log('Translate x:' + position.x + ' y:' + position.y);
    })

    editor.on('addReroute', function (id) {
        console.log("Reroute added " + id);
    })

    editor.on('removeReroute', function (id) {
        console.log("Reroute removed " + id);
    })

    editor.selectNode = function (id) {
        if (this.node_selected != null) {
            this.node_selected.classList.remove("selected");
            if (this.node_selected !== this.ele_selected) {
                this.dispatch('nodeUnselected', true);
            }
        }
        const element = document.querySelector(`#node-${id}`);
        this.ele_selected = element;
        this.node_selected = element;
        this.node_selected.classList.add("selected");
        if (this.node_selected !== this.ele_selected) {
            this.node_selected = element;
            this.node_selected.classList.add('selected');
            this.dispatch('nodeSelected', this.ele_selected.id.slice(5));
        }
        console.log(id)
    }

    let last_x = 0;
    let last_y = 0;
    let dragElementHover = null;

    editor.on("mouseMove", ({x, y}) => {
        const hoverEles = document.elementsFromPoint(x, y);
        const nextGroup = hoverEles.find(ele => ele.classList.contains('GROUP') && (!editor.node_selected || ele.id !== editor.node_selected.id));

        if (nextGroup) {
            if (dragElementHover !== nextGroup) {
                if (dragElementHover) {
                    dragElementHover.classList.remove("hover-drop");
                }
                dragElementHover = nextGroup;
                dragElementHover.classList.add("hover-drop");
            }
        } else if (dragElementHover) {
            dragElementHover.classList.remove("hover-drop");
            dragElementHover = null;
        }

        if (editor.node_selected && editor.drag) {
            const selectedNodeId = editor.node_selected.id.slice(5);
            var dx = (last_x - x) * editor.precanvas.clientWidth / (editor.precanvas.clientWidth * editor.zoom);
            var dy = (last_y - y) * editor.precanvas.clientHeight / (editor.precanvas.clientHeight * editor.zoom);

            if (editor.node_selected.classList.contains("GROUP")) {
                moveGroupNodes(selectedNodeId, -dx, -dy);
            }
        } else {
            if (dragElementHover) {
                dragElementHover.classList.remove("hover-drop");
                dragElementHover = null;
            }
        }

        last_x = x;
        last_y = y;
    });

    editor.on("nodeMoved", (id) => {
        const dragNode = id;
        if (dragElementHover !== null) {
            const dropNode = dragElementHover.id.slice(5);
            if (dragNode !== dropNode) {
                removeOfGroupNode(dragNode);
                dragElementHover.classList.remove("hover-drop");
                const dropNodeInfo = editor.getNodeFromId(dropNode);
                const dropNodeInfoData = dropNodeInfo.data;
                if (dropNodeInfoData.elements.indexOf(dragNode) === -1) {
                    dropNodeInfoData.elements.push(dragNode);
                    editor.updateNodeDataFromId(dropNode, dropNodeInfoData);
                    // remove connections
                    editor.removeConnectionNodeId('node-' + id);
                    // Hide the ports when node is inside the group
                    togglePortsDisplay(dragNode, 'none');
                    const dragNodeData = editor.getNodeFromId(dragNode);
                    if (dragNodeData.class !== "GROUP") {
                        collapseNode(dragNode);
                    }
                }
            }
            dragElementHover = null;
        } else {
            // If the node is moved outside of any group, show the ports
            togglePortsDisplay(dragNode, '');
            removeOfGroupNode(dragNode);
        }
    })

    editor.on("nodeRemoved", (id) => {
        removeOfGroupNode(id);
    });

    /* DRAG EVENT */

    /* Mouse and Touch Actions */

    var elements = document.getElementsByClassName('workstation-sidebar-dragitem');
    for (var i = 0; i < elements.length; i++) {
        elements[i].addEventListener('touchend', drop, false);
        elements[i].addEventListener('touchmove', positionMobile, false);
        elements[i].addEventListener('touchstart', drag, false);
    }

    mobile_item_selec = '';
    mobile_last_move = null;

    importQueue = [];
    currentImportIndex = 0;
    accumulatedImportData = {};
    descriptionStep = [];
    console.log("importQueue", importQueue)

    document.getElementById('surveyButton').addEventListener('click', function () {
        window.open('https://survey.aliyun.com/apps/zhiliao/vgpTppn22', '_blank');
    });

    document.getElementById('surveyClose').addEventListener('click', function () {
        hideSurveyModal();
    });

    setTimeout(showSurveyModal, 30000);
}


function makeNodeTop(id) {
    const node = document.getElementById(`node-${id}`);
    const nodeInfo = editor.getNodeFromId(id);

    if (nodeInfo) {
        console.log("currentZIndex: " + currentZIndex);
        currentZIndex += 1;
        node.style.zIndex = currentZIndex;

        if (nodeInfo.class === 'GROUP') {
            nodeInfo.data.elements.forEach((elementId) => {
                makeNodeTop(elementId);
            });
        }
    }
}


function moveGroupNodes(groupId, dx, dy) {
    const groupInfo = editor.getNodeFromId(groupId);
    const elements = groupInfo.data.elements || [];
    elements.forEach(eleId => {
        const eleNode = document.getElementById(`node-${eleId}`);
        const eleNodeInfo = editor.getNodeFromId(eleId);

        if (eleNode) {
            const nodeData = editor.drawflow.drawflow[editor.module].data[eleId];
            const newPosX = nodeData.pos_x + dx;
            const newPosY = nodeData.pos_y + dy;

            eleNode.style.left = newPosX + "px";
            eleNode.style.top = newPosY + "px";

            if (editor.drawflow.drawflow[editor.module] &&
                editor.drawflow.drawflow[editor.module].data &&
                editor.drawflow.drawflow[editor.module].data[eleId]) {
                editor.drawflow.drawflow[editor.module].data[eleId].pos_x = newPosX;
                editor.drawflow.drawflow[editor.module].data[eleId].pos_y = newPosY;
            }

            editor.updateConnectionNodes(`node-${eleId}`);
        }

        if (eleNodeInfo.class && eleNodeInfo.class === "GROUP") {
            moveGroupNodes(eleId, dx, dy);
        }
    });
}


function collapseNode(nodeId) {
    const nodeElement = document.getElementById(`node-${nodeId}`);
    const contentBox = nodeElement.querySelector('.box');
    const toggleArrow = nodeElement.querySelector('.toggle-arrow');

    contentBox.classList.add('hidden');
    toggleArrow.textContent = "\u25BC";
}


function togglePortsDisplay(nodeId, displayStyle) {
    const nodeElement = document.querySelector(`#node-${nodeId}`);
    if (nodeElement) {
        const inputs = nodeElement.querySelectorAll('.inputs .input');
        const outputs = nodeElement.querySelectorAll('.outputs .output');
        inputs.forEach(input => {
            input.style.display = displayStyle;
        });
        outputs.forEach(output => {
            output.style.display = displayStyle;
        });
    }
}


function removeOfGroupNode(id) {
    Object.keys(editor.drawflow.drawflow[editor.module].data).forEach(ele => {
        if (editor.drawflow.drawflow[editor.module].data[ele].class === "GROUP") {
            const findIndex = editor.drawflow.drawflow[editor.module].data[ele].data.elements.indexOf(id);
            if (findIndex !== -1) {
                editor.drawflow.drawflow[editor.module].data[ele].data.elements.splice(findIndex, 1);
            }
        }
    })
}


function positionMobile(ev) {
    mobile_last_move = ev;
}


function allowDrop(ev) {
    ev.preventDefault();
}


function drag(ev) {
    if (ev.type === "touchstart") {
        mobile_item_selec = ev.target.closest(".workstation-sidebar-dragitem").getAttribute('data-node');
    } else {
        ev.dataTransfer.setData("node", ev.target.getAttribute('data-node'));
    }
}


function drop(ev) {
    if (ev.type === "touchend") {
        var parentdrawflow = document.elementFromPoint(mobile_last_move.touches[0].clientX, mobile_last_move.touches[0].clientY).closest("#drawflow");
        if (parentdrawflow != null) {
            addNodeToDrawFlow(mobile_item_selec, mobile_last_move.touches[0].clientX, mobile_last_move.touches[0].clientY);
        }
        mobile_item_selec = '';
    } else {
        ev.preventDefault();
        var data = ev.dataTransfer.getData("node");
        addNodeToDrawFlow(data, ev.clientX, ev.clientY);
    }

}


async function addNodeToDrawFlow(name, pos_x, pos_y) {
    if (editor.editor_mode === 'fixed') {
        return false;
    }
    pos_x = pos_x * (editor.precanvas.clientWidth / (editor.precanvas.clientWidth * editor.zoom)) - (editor.precanvas.getBoundingClientRect().x * (editor.precanvas.clientWidth / (editor.precanvas.clientWidth * editor.zoom)));
    pos_y = pos_y * (editor.precanvas.clientHeight / (editor.precanvas.clientHeight * editor.zoom)) - (editor.precanvas.getBoundingClientRect().y * (editor.precanvas.clientHeight / (editor.precanvas.clientHeight * editor.zoom)));

    var htmlSourceCode = await fetchHtmlSourceCodeByName(name);

    switch (name) {
        // Workflow-Model
        case 'dashscope_chat':
            const dashscope_chatId = editor.addNode('dashscope_chat', 0, 0, pos_x,
                pos_y,
                'dashscope_chat', {
                    "args":
                        {
                            "config_name": '',
                            "model_name": '',
                            "api_key": '',
                            "temperature": 0.0,
                            "seed": 0,
                            "model_type": 'dashscope_chat',
                            "messages_key": 'input'
                        }
                },
                htmlSourceCode);
            addEventListenersToNumberInputs(dashscope_chatId);
            break;

        case 'openai_chat':
            const openai_chatId = editor.addNode('openai_chat', 0, 0, pos_x,
                pos_y,
                'openai_chat', {
                    "args":
                        {
                            "config_name": '',
                            "model_name": '',
                            "api_key": '',
                            "temperature": 0.0,
                            "seed": 0,
                            "model_type": 'openai_chat',
                            "messages_key": 'messages'
                        }
                },
                htmlSourceCode);
            addEventListenersToNumberInputs(openai_chatId);
            break;

        case 'post_api_chat':
            const post_api_chatId = editor.addNode('post_api_chat', 0, 0, pos_x, pos_y,
                'post_api_chat', {
                    "args":
                        {
                            "config_name": '',
                            "api_url": '',
                            "headers": {
                                "content_type": 'application/json',
                                "authorization": '',
                            },
                            "json_args": {
                                "model": '',
                                "temperature": 0.0,
                                "seed": 0,
                            },
                            "model_type": 'post_api_chat',
                            "messages_key": 'messages'
                        }
                },
                htmlSourceCode);
            addEventListenersToNumberInputs(post_api_chatId);
            break;

        case 'post_api_dall_e':
            const post_api_dall_eId = editor.addNode('post_api_dall_e', 0,
                0,
                pos_x, pos_y,
                'post_api_dall_e', {
                    "args":
                        {
                            "config_name": '',
                            "api_url": '',
                            "headers": {
                                "content_type": 'application/json',
                                "authorization": '',
                            },
                            "json_args": {
                                "model": '',
                                "n": 1,
                                "size": "",
                                "temperature": 0.0,
                                "seed": 0,
                            },
                            "model_type": 'post_api_dall_e',
                            "messages_key": 'prompt'
                        }
                },
                htmlSourceCode);
            addEventListenersToNumberInputs(post_api_dall_eId);
            break;

        // Message
        case 'Message':
            editor.addNode('Message', 1, 1, pos_x,
                pos_y, 'Message', {
                    "args":
                        {
                            "name": '',
                            "role": '',
                            "content": '',
                            "url": ''
                        }
                }, htmlSourceCode);
            break;

        // Workflow-Agent
        case 'DialogAgent':
            const DialogAgentID = editor.addNode('DialogAgent', 1, 1,
                pos_x,
                pos_y,
                'DialogAgent', {
                    "args": {
                        "name": '',
                        "sys_prompt": '',
                        "model_config_name": ''
                    }
                }, htmlSourceCode);
            var nodeElement = document.querySelector(`#node-${DialogAgentID} .node-id`);
            if (nodeElement) {
                nodeElement.textContent = DialogAgentID;
            }
            break;

        case 'UserAgent':
            const UserAgentID = editor.addNode('UserAgent', 1, 1, pos_x,
                pos_y, 'UserAgent', {
                    "args": {"name": 'User'}
                }, htmlSourceCode);
            var nodeElement = document.querySelector(`#node-${UserAgentID} .node-id`);
            if (nodeElement) {
                nodeElement.textContent = UserAgentID;
            }
            break;

        case 'DictDialogAgent':
            const DictDialogAgentID = editor.addNode('DictDialogAgent', 1,
                1, pos_x, pos_y,
                'DictDialogAgent', {
                    "args": {
                        "name": '',
                        "sys_prompt": '',
                        "model_config_name": '',
                        "parse_func": '',
                        "fault_handler": '',
                        "max_retries": 3,
                    }
                }, htmlSourceCode);
            var nodeElement = document.querySelector(`#node-${DictDialogAgentID} .node-id`);
            if (nodeElement) {
                nodeElement.textContent = DictDialogAgentID;
            }
            break;

        case 'ReActAgent':
            const ReActAgentID = editor.addNode('ReActAgent', 1, 1, pos_x, pos_y,
                'GROUP', {
                    elements: [],
                    "args": {
                        "name": '',
                        "sys_prompt": '',
                        "model_config_name": '',
                        "max_iters": 10,
                        "verbose": '',
                    }
                }, htmlSourceCode);
            var nodeElement = document.querySelector(`#node-${ReActAgentID} .node-id`);
            if (nodeElement) {
                nodeElement.textContent = ReActAgentID;
            }
            break;

        // Workflow-Pipeline
        case 'Placeholder':
            editor.addNode('Placeholder', 1, 1,
                pos_x, pos_y, 'Placeholder', {}, htmlSourceCode);
            break;

        case 'MsgHub':
            editor.addNode('MsgHub', 1, 1, pos_x, pos_y,
                'GROUP', {
                    elements: [],
                    "args": {
                        "announcement": {
                            "name": '',
                            "content": ''
                        }
                    }
                }, htmlSourceCode);
            break;

        case 'SequentialPipeline':
            editor.addNode('SequentialPipeline', 1, 1, pos_x, pos_y,
                'GROUP', {elements: []}, htmlSourceCode);
            break;

        case 'ForLoopPipeline':
            const ForLoopPipelineID =
                editor.addNode('ForLoopPipeline', 1, 1, pos_x, pos_y,
                    'GROUP', {
                        elements: [],
                        "args": {
                            "max_loop": 3,
                            "break_func": ''
                        }
                    }, htmlSourceCode);
            addEventListenersToNumberInputs(ForLoopPipelineID);
            break;

        case 'WhileLoopPipeline':
            editor.addNode('WhileLoopPipeline', 1, 1, pos_x, pos_y,
                'GROUP', {
                    elements: [],
                    "args": {
                        "condition_func": ''
                    }
                }, htmlSourceCode);
            break;

        case 'IfElsePipeline':
            editor.addNode('IfElsePipeline', 1,
                1, pos_x, pos_y, 'GROUP', {
                    elements: [], args: {
                        "condition_func": ''
                    }
                }, htmlSourceCode);
            break;

        case 'SwitchPipeline':
            const SwitchPipelineID = editor.addNode('SwitchPipeline', 1, 1, pos_x, pos_y, 'GROUP', {
                elements: [], args: {
                    "condition_func": '',
                    "cases": [],
                }
            }, htmlSourceCode);
            setupSwitchPipelineListeners(SwitchPipelineID);
            const caseContainer = document.querySelector(`#node-${SwitchPipelineID} .case-container`);
            if (caseContainer) {
                addDefaultCase(caseContainer);
            } else {
                console.error(`Case container not found in node-${SwitchPipelineID}.`);
            }
            break;

        // Workflow-Service
        case 'BingSearchService':
            editor.addNode('BingSearchService', 0, 0,
                pos_x, pos_y, 'BingSearchService', {
                    "args": {
                        "api_key": "",
                        "num_results": 3,
                    }
                }, htmlSourceCode);
            break;

        case 'GoogleSearchService':
            editor.addNode('GoogleSearchService', 0, 0,
                pos_x, pos_y, 'GoogleSearchService', {
                    "args": {
                        "api_key": "",
                        "cse_id": "",
                        "num_results": 3,
                    }
                }, htmlSourceCode);
            break;

        case 'PythonService':
            editor.addNode('PythonService', 0, 0,
                pos_x, pos_y, 'PythonService', {}, htmlSourceCode);
            break;

        case 'ReadTextService':
            editor.addNode('ReadTextService', 0, 0,
                pos_x, pos_y, 'ReadTextService', {}, htmlSourceCode);
            break;

        case 'WriteTextService':
            editor.addNode('WriteTextService', 0, 0,
                pos_x, pos_y, 'WriteTextService', {}, htmlSourceCode);
            break;

        default:
    }
}

function setupTextInputListeners(nodeId) {
    const newNode = document.getElementById(`node-${nodeId}`);
    if (newNode) {
        const stopPropagation = function (event) {
            event.stopPropagation();
        };
        newNode.addEventListener('mousedown', function (event) {
            const target = event.target;
            if (target.tagName === 'TEXTAREA' || target.tagName === 'INPUT') {
                stopPropagation(event);
            }
        }, false);
    }
}

function toggleAdvanced() {
    var advancedBox = document.querySelector('.advanced-box');
    if (advancedBox.style.display === "none") {
        advancedBox.style.display = "block";
    } else {
        advancedBox.style.display = "none";
    }
}


function handleInputChange(event) {
    const input = event.target;

    if (input.type === 'number') {
        const value = input.value;
        const floatValue = parseFloat(value);
        const nodeId = input.closest('.drawflow_content_node').parentElement.id.slice(5);

        if (!isNaN(floatValue)) {
            const node = editor.getNodeFromId(nodeId);
            const dataAttributes =
                Array.from(input.attributes).filter(attr =>
                    attr.name.startsWith('df-args-'));
            dataAttributes.forEach(attr => {
                const attrName = attr.name;
                if (attrName.startsWith('df-args-json_args-')) {
                    const dataAttribute = attrName.substring(18)
                    if
                    (node.data.args.json_args.hasOwnProperty(dataAttribute)) {
                        node.data.args.json_args[dataAttribute] = floatValue;
                        editor.updateNodeDataFromId(nodeId, node.data);
                    }
                } else {
                    const dataAttribute = attrName.substring(8);
                    if (node.data.args.hasOwnProperty(dataAttribute)) {
                        node.data.args[dataAttribute] = floatValue;
                        editor.updateNodeDataFromId(nodeId, node.data);
                    }
                }
            });
        } else {
            console.error("Invalid input value:", value);
        }
    }
}


function addEventListenersToNumberInputs(nodeId) {
    const nodeElement = document.getElementById(`node-${nodeId}`);
    if (nodeElement) {
        const numberInputs = nodeElement.querySelectorAll('input[type=number]');
        numberInputs.forEach(input => {
            input.addEventListener('change', handleInputChange);
        });
    }
}


function validateTemperature(input) {
    const value = input.valueAsNumber;
    if (isNaN(value) || value < 0 || value >= 2) {
        input.setCustomValidity('Temperature must be greater or equal than 0 and less than 2!');
    } else {
        input.setCustomValidity('');
    }
    input.reportValidity();
}


function validateSeed(input) {
    const value = parseInt(input.value, 10); // Parse the value as an integer.
    if (isNaN(value) || value < 0 || !Number.isInteger(parseFloat(input.value))) {
        input.setCustomValidity('Seed must be a non-negative integer!');
    } else {
        input.setCustomValidity('');
    }
    input.reportValidity();
}


document.addEventListener('input', function (event) {
    const input = event.target;

    if (input.getAttribute('df-args-temperature') !== null ||
        input.getAttribute('df-args-json_args-temperature') !== null) {
        validateTemperature(input);
    }

    if (input.getAttribute('df-args-seed') !== null ||
        input.getAttribute('df-args-json_args-seed') !== null) {
        validateSeed(input);
    }
});

var transform = '';


function updateReadmeAndTrimExtrasInHTML(htmlString, nodeId) {
    const parser = new DOMParser();
    const doc = parser.parseFromString(htmlString, 'text/html');
    const containerDiv = doc.body.firstChild;

    removeNonReadmeChildren(containerDiv);
    updateReadmeContent(containerDiv, nodeId);

    return containerDiv.innerHTML;
}

function updateReadmeContent(containerDiv, nodeId) {
    const readmeDiv = containerDiv.querySelector('.readme');
    if (readmeDiv) {
        console.log("readmeDiv", readmeDiv);

        let newDiv = document.createElement('div');
        newDiv.innerHTML = `Copy from Node ID: ${nodeId}`;
        readmeDiv.appendChild(newDiv);

        console.log("readmeDiv after", readmeDiv);
    }
}

function removeNonReadmeChildren(containerDiv) {
    const boxDiv = containerDiv.querySelector('.box');
    if (boxDiv) {
        boxDiv.querySelectorAll('*:not(.readme)').forEach(child => child.remove());
    }
}

function createNodeHTML(node, isCopy, originalNodeId) {
    let modifiedHtml = isCopy ? processNodeCopyHTML(node.html) : node.html;
    return updateReadmeAndTrimExtrasInHTML(modifiedHtml, originalNodeId);
}

function processNodeCopyHTML(htmlString) {
    const parser = new DOMParser();
    const doc = parser.parseFromString(htmlString, 'text/html');

    ['.copy-button', 'div .node-id'].forEach(selector => {
        const element = doc.querySelector(selector);
        if (element) element.remove();
    });

    return doc.body.innerHTML;
}

function copyNode(originalNodeId) {
    const originalNode = editor.getNodeFromId(originalNodeId);
    originalNode.data.copies = originalNode.data.copies || [];

    const newNodeHTML = createNodeHTML(originalNode, true, originalNodeId);
    const [posX, posY] = [originalNode.pos_x + 30, originalNode.pos_y + 30];

    editor.addNode("CopyNode",
        Object.keys(originalNode.inputs).length,
        Object.keys(originalNode.outputs).length,
        posX, posY, 'node-' + originalNode.name, {elements: [originalNodeId.toString()]},
        newNodeHTML);
}

function setupNodeCopyListens(nodeId) {
    const newNode = document.getElementById(`node-${nodeId}`);
    if (newNode) {
        const copyButton = newNode.querySelector('.copy-button');
        if (copyButton) {
            copyButton.addEventListener('click', function () {
                copyNode(nodeId);
            });
        }
    }
}

function hideShowGroupNodes(groupId, show) {
    const groupInfo = editor.getNodeFromId(groupId);
    if (groupInfo && groupInfo.class === 'GROUP') {
        groupInfo.data.elements.forEach(elementNodeId => {
            const elementNode = document.getElementById(`node-${elementNodeId}`);
            const childNodeInfo = editor.getNodeFromId(elementNodeId);
            const contentBox = elementNode.querySelector('.box') ||
                elementNode.querySelector('.box-highlight');
            if (elementNode) {
                elementNode.style.display = show ? '' : 'none';
            }
            if (childNodeInfo.class === 'GROUP') {
                if (!show || (contentBox && !contentBox.classList.contains('hidden'))) {
                    hideShowGroupNodes(elementNodeId, show);
                }
            }
        });
    }
}

function setupNodeListeners(nodeId) {
    const newNode = document.getElementById(`node-${nodeId}`);
    if (newNode) {

        const titleBox = newNode.querySelector('.title-box');
        const contentBox = newNode.querySelector('.box') ||
            newNode.querySelector('.box-highlight');

        // Add resize handle to the bottom right corner of the node
        const resizeHandleSE = document.createElementNS('http://www.w3.org/2000/svg', 'svg');

        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', 'M932.37602347 512.88874453l-420.37602347 420.37602347 56.43525867 56.43525867 420.37602453-420.37602347-56.43525973-56.43525867z m-3.55497707-474.58942293L34.29997333 933.264768l56.43525867 56.43525867L985.25630613 95.1789536l-56.43525973-56.879632z');

        resizeHandleSE.setAttribute('viewBox', '0 0 1024 1024');
        resizeHandleSE.appendChild(path);

        resizeHandleSE.classList.add('resize-handle-se');

        contentBox.appendChild(resizeHandleSE);

        const toggleArrow = newNode.querySelector('.toggle-arrow');

        if (toggleArrow && contentBox && titleBox) {
            toggleArrow.addEventListener('click', function () {
                contentBox.classList.toggle('hidden');

                if (contentBox.classList.contains('hidden')) {
                    toggleArrow.textContent = "\u25BC";
                    hideShowGroupNodes(nodeId, false);
                } else {
                    toggleArrow.textContent = "\u25B2";
                    hideShowGroupNodes(nodeId, true);
                }
                editor.updateConnectionNodes('node-' + nodeId);
            });

            let startX, startY, startWidth, startHeight;

            resizeHandleSE.addEventListener('mousedown', function (e) {
                e.stopPropagation();
                document.addEventListener('mousemove', doDragSE, false);
                document.addEventListener('mouseup', stopDragSE, false);

                startX = e.clientX;
                startY = e.clientY;
                startWidth = parseInt(document.defaultView.getComputedStyle(contentBox).width, 10);
                startHeight = parseInt(document.defaultView.getComputedStyle(contentBox).height, 10);
            });

            function doDragSE(e) {
                newNode.style.width = 'auto';

                const newWidth = (startWidth + e.clientX - startX);
                if (newWidth > 200) {
                    contentBox.style.width = newWidth + 'px';
                    titleBox.style.width = newWidth + 'px';
                }

                const newHeight = (startHeight + e.clientY - startY);
                contentBox.style.height = newHeight + 'px';

                editor.updateConnectionNodes('node-' + nodeId);
            }

            function stopDragSE(e) {
                document.removeEventListener('mousemove', doDragSE, false);
                document.removeEventListener('mouseup', stopDragSE, false);
            }

        }
    }
}

function setupSwitchPipelineListeners(nodeId) {
    const newNode = document.getElementById(`node-${nodeId}`);
    if (!newNode) {
        console.error(`Node with ID node-${nodeId} not found.`);
        return;
    }
    const addCaseButton = newNode.querySelector('.add-case');
    if (!addCaseButton) {
        console.error(`Add Case button not found in node-${nodeId}.`);
        return;
    }
    addCaseButton.addEventListener('click', function () {
        var caseContainer = newNode.querySelector('.case-container');
        if (!caseContainer) {
            console.error(`Case container not found in node-${nodeId}.`);
            return;
        }
        var defaultCaseElement = caseContainer.querySelector('.default-case');
        if (defaultCaseElement) {
            caseContainer.removeChild(defaultCaseElement);
        }
        var caseCount = caseContainer.getElementsByClassName('case-placeholder').length;
        var caseElement = document.createElement('div');
        caseElement.classList.add('case-placeholder');

        var caseText = document.createTextNode(`Case ${caseCount + 1}: `);
        caseElement.appendChild(caseText);

        var inputElement = document.createElement('input');
        inputElement.type = 'text';
        inputElement.placeholder = `Case Pattern`;

        inputElement.dataset.caseIndex = caseCount;

        caseElement.appendChild(inputElement);
        caseContainer.appendChild(caseElement);

        inputElement.addEventListener('input', function (e) {
            var nodeData = editor.getNodeFromId(nodeId).data;
            console.log("nodeData", nodeData);
            var index = e.target.dataset.caseIndex;
            console.log("index", index);
            nodeData.args.cases[index] = e.target.value;
            editor.updateNodeDataFromId(nodeId, nodeData);
        });

        editor.getNodeFromId(nodeId).data.args.cases.push('');

        addDefaultCase(caseContainer);
        editor.updateConnectionNodes('node-' + nodeId);
    });

    const removeCaseButton = newNode.querySelector('.remove-case');
    if (!removeCaseButton) {
        console.error(`Remove Case button not found in node-${nodeId}.`);
        return;
    }
    removeCaseButton.addEventListener('click', function () {
        var caseContainer = newNode.querySelector('.case-container');
        var cases = caseContainer.getElementsByClassName('case-placeholder');
        if (cases.length > 1) {
            caseContainer.removeChild(cases[cases.length - 2]);
            var nodeData = editor.getNodeFromId(nodeId).data;
            nodeData.args.cases.splice(nodeData.args.cases.length - 1, 1);
            editor.updateNodeDataFromId(nodeId, nodeData);
        }
        editor.updateConnectionNodes('node-' + nodeId);
    });
}

function addDefaultCase(caseContainer) {
    var defaultCaseElement = document.createElement('div');
    defaultCaseElement.classList.add('case-placeholder', 'default-case');
    defaultCaseElement.textContent = `Default Case`;
    caseContainer.appendChild(defaultCaseElement);
}


function closemodal(e) {
    e.target.closest(".drawflow-node").style.zIndex = "2";
    e.target.parentElement.parentElement.style.display = "none";
    editor.precanvas.style.transform = transform;
    editor.precanvas.style.left = '0px';
    editor.precanvas.style.top = '0px';
    editor.editor_mode = "edit";
}


function changeModule(event) {
    var all = document.querySelectorAll(".menu ul li");
    for (var i = 0; i < all.length; i++) {
        all[i].classList.remove('selected');
    }
    event.target.classList.add('selected');
}


function changeLockMode(option) {
    let lockSvg = document.getElementById('lock-svg');
    let unlockSvg = document.getElementById('unlock-svg');
    if (option === 'lock') {
        editor.editor_mode = 'edit';
        lockSvg.style.display = 'none';
        unlockSvg.style.display = 'block';
    } else {
        editor.editor_mode = 'fixed';
        lockSvg.style.display = 'block';
        unlockSvg.style.display = 'none';
    }
}


function toggleDraggable(element) {
    var content = element.nextElementSibling;
    if (content.classList.contains('visible')) {
        content.classList.remove('visible');
    } else {
        content.classList.add('visible');
    }
}


function filterEmptyValues(obj) {
    return Object.entries(obj).reduce((acc, [key, value]) => {
        if (Array.isArray(value)) {
            const filteredArray = value.map(item => {
                if (typeof item === 'object' && item !== null) {
                    return filterEmptyValues(item);
                }
                return item !== '' ? item : null;
            }).filter(item => item !== null);

            if (filteredArray.length > 0) {
                acc[key] = filteredArray;
            }
        } else if (typeof value === 'object' && value !== null) {
            const filteredNestedObj = filterEmptyValues(value);
            if (Object.keys(filteredNestedObj).length > 0) {
                acc[key] = filteredNestedObj;
            }
        } else if (value !== '') {
            acc[key] = value;
        }
        return acc;
    }, {});
}


// This function is the most important to AgentScope config.
function reorganizeAndFilterConfigForAgentScope(inputData) {
    // Assuming there's only one tab ('Home'), but adjust if there are more
    const homeTab = inputData.drawflow.Home;
    // Create a new object to hold the reorganized and filtered nodes
    const filteredNodes = {};

    // Iterate through the nodes and copy them to the filteredNodes object
    Object.entries(homeTab.data).forEach(([key, node]) => {
        // Skip the node if the name is 'welcome' or 'readme'
        const nodeName = node.name.toLowerCase();
        if (nodeName === 'welcome' || nodeName === 'readme') {
            return;
        }

        // Create a copy of the node without 'html', 'typenode', 'class', 'id', and 'name' fields
        const {
            html,
            typenode,
            pos_x,
            pos_y,
            class: classField,
            id,
            ...cleanNode
        } = node;

        if (cleanNode.data && cleanNode.data.args) {
            cleanNode.data.args = filterEmptyValues(cleanNode.data.args);
        }

        // Add the cleaned node to the filteredNodes object using its id as the key
        filteredNodes[key] = cleanNode;
    });

    // Return the filtered and reorganized nodes instead of the original structure
    return filteredNodes;
}


function sortElementsByPosition(inputData) {
    let hasError = false;

    Object.keys(inputData.drawflow).forEach((moduleKey) => {
        const moduleData = inputData.drawflow[moduleKey];
        Object.entries(moduleData.data).forEach(([nodeId, node]) => {
            if (node.class === 'GROUP') {
                let elements = node.data.elements;
                let elementsWithPosition = elements.map(elementId => {
                    const elementNode = document.querySelector(`#node-${elementId}`);
                    return elementNode ? {
                        id: elementId,
                        position: {
                            x: elementNode.style.left,
                            y: elementNode.style.top
                        }
                    } : null;
                }).filter(el => el);

                try {
                    elementsWithPosition.sort((a, b) => {
                        let y1 = parseInt(a.position.y, 10);
                        let y2 = parseInt(b.position.y, 10);
                        if (y1 === y2) {
                            throw new Error(`Two elements have the same y position: Element ${a.id} and Element ${b.id}`);
                        }
                        return y1 - y2;
                    });
                } catch (error) {
                    alert(error.message);
                    hasError = true;
                }
                node.data.elements = elementsWithPosition.map(el => el.id);
            }
        });
    });
    return hasError;
}


function checkConditions() {
    let hasModelTypeError = true;
    let hasAgentError = true;
    let agentModelConfigNames = new Set();
    let modelConfigNames = new Set();
    let isApiKeyEmpty = false;
    const nodesData = editor.export().drawflow.Home.data;

    for (let nodeId in nodesData) {
        let node = nodesData[nodeId];
        console.log("node", node);
        console.log("node.inputs", node.inputs);

        if (node.inputs) {
            for (let inputKey in node.inputs) {
                if (node.inputs[inputKey].connections &&
                    node.inputs[inputKey].connections.length > 1) {
                    Swal.fire({
                        title: 'Invalid Connections',
                        text:
                            `${node.name} has more than one connection in inputs.`,
                        icon: 'error',
                        confirmButtonText: 'Ok'
                    });
                    return false;
                }
            }
        }

        let nodeElement = document.getElementById('node-' + nodeId);
        const requiredInputs = nodeElement.querySelectorAll('input[data-required="true"]');

        let titleBox = nodeElement.querySelector('.title-box');

        let titleText = titleBox.getAttribute("data-class");

        for (const input of requiredInputs) {
            if (input.value.trim() === '') {
                let inputLabel = input.previousElementSibling;
                if (inputLabel && inputLabel.tagName.toLowerCase() === "label") {
                    let labelText = inputLabel.textContent.trim();

                    Swal.fire({
                        title: 'Value Missing!',
                        text: `${labelText} is missing in ${titleText}.`,
                        icon: 'error',
                        confirmButtonText: 'Ok'
                    });
                    return false;
                }
            }
        }

        if (node.data && node.data.args && node.data.args.model_type) {
            hasModelTypeError = false;
            modelConfigNames.add(node.data.args.config_name);
            if (node.data.args.api_key === "") {
                isApiKeyEmpty = isApiKeyEmpty || true;
            }
        }

        if (node.name === "Message") {
            const validRoles = ["system", "assistant", "user"];
            if (!validRoles.includes(node.data.args.role)) {
                Swal.fire({
                        title: 'Invalid Role for Message',
                        html:
                            `Invalid role ${node.data.args.role}. <br>The role must be in ['system', 'user', 'assistant']`,
                        icon: 'error',
                        confirmButtonText: 'Ok'
                    });
                return false;
            }
        }

        if (node.name.includes('Agent') && "model_config_name" in node.data.args) {
            hasAgentError = false;
            if (node.data && node.data.args) {
                agentModelConfigNames.add(node.data.args.model_config_name);
            }
        }
        if (node.name === 'ReActAgent') {
            const elements = node.data.elements;
            for (const nodeId of elements) {
                const childNode = nodesData[nodeId]
                if (!childNode || !childNode.name.includes('Service')) {
                    Swal.fire({
                        title: 'Invalid ReActAgent Configuration',
                        text:
                            `ReActAgent must only contain Tool nodes as child nodes.`,
                        icon: 'error',
                        confirmButtonText: 'Ok'
                    });
                    return false;
                }
            }
        }
        if (node.name === 'IfElsePipeline') {
            const elementsSize = node.data.elements.length;
            if (elementsSize !== 1 && elementsSize !== 2) {
                Swal.fire({
                    title: 'Invalid IfElsePipeline Configuration',
                    text: `IfElsePipeline should have 1 or 2 elements, but has ${elementsSize}.`,
                    icon: 'error',
                    confirmButtonText: 'Ok'
                });
                return false;
            }
        }
        if (['ForLoopPipeline', 'WhileLoopPipeline', 'MsgHub'].includes(node.name)) {
            if (node.data.elements.length !== 1) {
                hasError = true;
                Swal.fire({
                    title: 'Invalid Configuration',
                    text: `${node.name} must have exactly one element.`,
                    icon: 'error',
                    confirmButtonText: 'Ok'
                });
                return false;
            }
            let childNodeId = node.data.elements[0];
            let childNode = nodesData[childNodeId];
            if (!childNode || !childNode.name.includes('Pipeline')) {
                Swal.fire({
                    title: 'Invalid Configuration',
                    text:
                        ` ${childNode.name} contained in ${node.name} is not a Pipeline node.`,
                    icon: 'error',
                    confirmButtonText: 'Ok'
                });
                return false;
            }
        }
    }

    let unmatchedConfigNames = [...agentModelConfigNames].filter(name => !modelConfigNames.has(name));
    console.log("modelConfigNames", modelConfigNames);
    console.log("agentModelConfigNames", agentModelConfigNames);
    console.log("unmatchedConfigNames", unmatchedConfigNames);
    if (hasModelTypeError) {
        Swal.fire({
            title: 'Error!',
            text:
                'Error: At least one Model node must be present.',
            icon: 'error',
            confirmButtonText: 'Ok'
        });
    } else if (hasAgentError) {
        Swal.fire({
            title: 'No Agent Nodes Found',
            text: "Error: At least one Agent node must be present.",
            icon: 'error',
            confirmButtonText: 'Ok'
        });
    } else if (unmatchedConfigNames.length > 0) {
        Swal.fire({
            title: 'Configuration Mismatch',
            html:
                "Each Agent's 'Model config name' must match a Model node's 'Config Name'.<br> Unmatched: " + unmatchedConfigNames.join(', '),
            icon: 'error',
            confirmButtonText: 'Ok'
        });
    } else if (isApiKeyEmpty) {
        Swal.fire({
            title: 'API KEY Missing',
            text:
                "API KEY is missing in your model nodes. Please either enter the API KEY in the corresponding position, or enter a random bit of content and replace it with the real value in the exported files.",
            icon: 'error',
            confirmButtonText: 'Ok'
        });
    } else {
        return true;
    }
}


function showCheckPopup() {
    var btnCovers = document.querySelectorAll('.btn-cover');
    if (checkConditions()) {
        Swal.fire({
            title: 'Validation Success',
            text: "All checks are passed!",
            icon: 'success',
            confirmButtonText: 'Great!'
        });
        btnCovers.forEach(function (btnCover) {
            var button = btnCover.querySelector('.btn-disabled');
            if (button) {
                button.classList.remove('btn-disabled');
            }
            btnCover.removeAttribute('data-title');
        });
    }
}


function disableButtons() {
    var btnCovers = document.querySelectorAll('.btn-cover');

    btnCovers.forEach(function (btnCover) {
        var button = btnCover.querySelector('div');
        if (button) {
            button.classList.add('btn-disabled');
        }
        btnCover.setAttribute('data-title',
            'Please click the "Check" button first.');
    });
}


function showExportPyPopup() {
    if (checkConditions()) {
        const rawData = editor.export();

        const hasError = sortElementsByPosition(rawData);
        if (hasError) {
            return;
        }

        const filteredData = reorganizeAndFilterConfigForAgentScope(rawData);

        Swal.fire({
            title: 'Processing...',
            text: 'Please wait.',
            allowOutsideClick: false,
            willOpen: () => {
                Swal.showLoading()
            }
        });

        fetch('/convert-to-py', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                data: JSON.stringify(filteredData, null, 4),
            })
        }).then(response => {
            if (!response.ok) {
                throw new Error('Network error.');
            }
            return response.json();
        })
            .then(data => {
                Swal.close();
                if (data.is_success === 'True') {
                    Swal.fire({
                        title: '<b>Workflow Python Code</b>',
                        html:
                            '<p>Save as main.py<br>' +
                            'Then run the following command in your terminal:<br>' +
                            '<div class="code-snippet">python main.py</div><br>' +
                            'or <div class="code-snippet">as_gradio main.py</div></p>' +
                            '<pre class="line-numbers"><code class="language-py" id="export-data">' +
                            data.py_code +
                            '</code></pre>',
                        showCloseButton: true,
                        showCancelButton: true,
                        confirmButtonText: 'Copy',
                        cancelButtonText: 'Close',
                        willOpen: (element) => {
                            const codeElement = element.querySelector('code');
                            Prism.highlightElement(codeElement);
                            const copyButton = Swal.getConfirmButton();
                            copyButton.addEventListener('click', () => {
                                copyToClipboard(codeElement.textContent);
                            });
                        }
                    });
                } else {
                    const errorMessage = `
                <p>An error occurred during the Python code generation process. Please check the following error:</p>
                <pre class="line-numbers"><code class="language-py">${data.py_code}</code></pre>
        `;
                    Swal.fire({
                        title: 'Error!',
                        html: errorMessage,
                        icon: 'error',
                        customClass: {
                            popup: 'error-popup'
                        },
                        confirmButtonText: 'Close',
                        willOpen: (element) => {
                            const codeElement = element.querySelector('code');
                            Prism.highlightElement(codeElement);
                        }
                    });
                }
            })
            .catch(error => {
                console.error('Error:', error);
                Swal.fire('Failed!',
                    'There was an error generating your code.',
                    'error');
            });
    }
}


function showExportRunPopup(version) {
    if (version === "local") {
        showExportRunLocalPopup();
    } else {
        showExportRunMSPopup();
    }
}


function showExportRunLocalPopup() {
    if (checkConditions()) {
        const rawData = editor.export();
        const hasError = sortElementsByPosition(rawData);
        if (hasError) {
            return;
        }
        const filteredData = reorganizeAndFilterConfigForAgentScope(rawData);

        Swal.fire({
            title: 'Processing...',
            text: 'Please wait.',
            allowOutsideClick: false,
            willOpen: () => {
                Swal.showLoading()
            }
        });

        fetch('/convert-to-py-and-run', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                data: JSON.stringify(filteredData, null, 4),
            })
        }).then(response => {
            if (!response.ok) {
                throw new Error('Network error.');
            }
            return response.json();
        })
            .then(data => {
                Swal.close();
                if (data.is_success === 'True') {
                    Swal.fire({
                        title: '<b>Application Running in Background</b>',
                        html:
                            '<p>Your application has been successfully run ' +
                            'in background.<br>' +
                            '<p><strong>Task ID:</strong>' +
                            data.run_id + '</p>' +
                            '<pre class="line-numbers"><code class="language-py" id="export-data">' +
                            data.py_code +
                            '</code></pre>',
                        showCloseButton: true,
                        showCancelButton: true,
                        confirmButtonText: 'Copy Code',
                        cancelButtonText: 'Close',
                        willOpen: (element) => {
                            const codeElement = element.querySelector('code');
                            Prism.highlightElement(codeElement);
                            const copyButton = Swal.getConfirmButton();
                            copyButton.addEventListener('click', () => {
                                copyToClipboard(codeElement.textContent);
                            });
                        }
                    });
                } else {
                    const errorMessage = `
        <p>An error occurred during the Python code running process. Please check the following error:</p>
        <pre class="line-numbers"><code class="language-py">${data.py_code}</code></pre>
    `;
                    Swal.fire({
                        title: 'Error!',
                        html: errorMessage,
                        icon: 'error',
                        customClass: {
                            popup: 'error-popup'
                        },
                        confirmButtonText: 'Close',
                        willOpen: (element) => {
                            const codeElement = element.querySelector('code');
                            Prism.highlightElement(codeElement);
                        }
                    });
                }
            })
            .catch(error => {
                console.error('Error:', error);
                Swal.close();
                Swal.fire('Failed!',
                    'There was an error running your workflow.',
                    'error');
            });
    }
}


function filterOutApiKey(obj) {
    for (let key in obj) {
        if (typeof obj[key] === 'object' && obj[key] !== null) {
            filterOutApiKey(obj[key]);
        }
        if (key === 'api_key') {
            delete obj[key];
        }
    }
}


function showExportRunMSPopup() {
    if (checkConditions()) {
        Swal.fire({
            title: 'Are you sure to run the workflow in ModelScope Studio?',
            text:
                "You are about to navigate to another page. " +
                "Please make sure all the configurations are set " +
                "besides your api-key " +
                "(your api-key should be set in ModelScope Studio page).",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#3085d6',
            cancelButtonColor: '#d33',
            confirmButtonText: 'Yes, create it!',
            cancelButtonText: 'Close'
        }).then((result) => {
            if (result.isConfirmed) {
                const rawData = editor.export();
                const hasError = sortElementsByPosition(rawData);
                if (hasError) {
                    return;
                }
                const filteredData = reorganizeAndFilterConfigForAgentScope(rawData);
                filterOutApiKey(filteredData)

                Swal.fire({
                    title: 'Processing...',
                    text: 'Please wait.',
                    allowOutsideClick: false,
                    willOpen: () => {
                        Swal.showLoading()
                    }
                });
                fetch('/upload-to-oss', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        data: JSON.stringify(filteredData, null, 4),
                    })
                })
                    .then(response => response.json())
                    .then(data => {
                        const params = {'CONFIG_URL': data.config_url};
                        const paramsStr = encodeURIComponent(JSON.stringify(params));
                        const org = "agentscope";
                        const fork_repo = "agentscope_workstation";
                        const url = `https://www.modelscope.cn/studios/fork?target=${org}/${fork_repo}&overwriteEnv=${paramsStr}`;
                        window.open(url, '_blank');
                        Swal.fire('Success!', '', 'success');
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        Swal.fire('Failed', data.message || 'An error occurred while uploading to oss', 'error');
                    });
            }
        })
    }
}


function showExportHTMLPopup() {
    const rawData = editor.export();

    // Remove the html attribute from the nodes to avoid inconsistencies in html
    removeHtmlFromUsers(rawData);
    sortElementsByPosition(rawData);

    const exportData = JSON.stringify(rawData, null, 4);

    const escapedExportData = exportData
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

    Swal.fire({
        title: '<b>Workflow HTML</b>',
        html:
            '<p>This is used for generating HTML code, not for running.<br>' +
            '<pre class="line-numbers"><code class="language-javascript" id="export-data">'
            + escapedExportData +
            '</code></pre>',
        showCloseButton: true,
        showCancelButton: true,
        confirmButtonText: 'Copy',
        cancelButtonText: 'Close',
        willOpen: (element) => {
            // Find the code element inside the Swal content
            const codeElement = element.querySelector('code');

            // Now highlight the code element with Prism
            Prism.highlightElement(codeElement);

            // Copy to clipboard logic
            const content = codeElement.textContent;
            const copyButton = Swal.getConfirmButton();
            copyButton.addEventListener('click', () => {
                copyToClipboard(content);
            });
        }
    });
}


function isValidDataStructure(data) {
    if (
        data.hasOwnProperty('drawflow') &&
        data.drawflow.hasOwnProperty('Home') &&
        data.drawflow.Home.hasOwnProperty('data')
    ) {

        for (const nodeId in data.drawflow.Home.data) {
            const node = data.drawflow.Home.data[nodeId];

            if (
                !node.hasOwnProperty('id') ||
                typeof node.id !== 'number' ||
                !node.hasOwnProperty('name') ||
                typeof node.name !== 'string' ||
                !node.hasOwnProperty('class') ||
                typeof node.class !== 'string'
            ) {
                return false;
            }
        }
        return true;
    }
    return false;
}


function showImportHTMLPopup() {
    Swal.fire({
        title: 'Import Workflow Data',
        html:
            "<p>Please paste your HTML data below. Ensure that the source of the HTML data is trusted, as importing HTML from unknown or untrusted sources may pose security risks.</p>",
        input: 'textarea',
        inputLabel: 'Paste your HTML data here:',
        inputPlaceholder:
            'Paste your HTML data generated from `Export HTML` button...',
        inputAttributes: {
            'aria-label': 'Paste your HTML data here',
            'class': 'code'
        },
        customClass: {
            input: 'code'
        },
        showCancelButton: true,
        confirmButtonText: 'Import',
        cancelButtonText: 'Cancel',
        inputValidator: (value) => {
            if (!value) {
                return 'You need to paste code generated from `Export HTML` button!';
            }
            try {
                const parsedData = JSON.parse(value);
                if (isValidDataStructure(parsedData)) {

                } else {
                    return 'The data is invalid. Please check your data and try again.';
                }
            } catch (e) {
                return 'Invalid data! You need to paste code generated from `Export HTML` button!';
            }
        },
        preConfirm: (data) => {
            try {
                const parsedData = JSON.parse(data);

                // Add html source code to the nodes data
                addHtmlAndReplacePlaceHolderBeforeImport(parsedData)
                    .then(() => {
                        editor.clear();
                        editor.import(parsedData);
                        importSetupNodes(parsedData);
                        Swal.fire('Imported!', '', 'success');
                    });

            } catch (error) {
                Swal.showValidationMessage(`Import error: ${error}`);
            }
        }
    });
}


function showSaveWorkflowPopup() {
    Swal.fire({
        title: 'Save Workflow',
        input: 'text',
        inputPlaceholder: 'Enter filename',
        showCancelButton: true,
        confirmButtonText: 'Save',
        cancelButtonText: 'Cancel'
    }).then(result => {
        if (result.isConfirmed) {
            const filename = result.value;
            saveWorkflow(filename);
        }
    });
}

function saveWorkflow(fileName) {
    const rawData = editor.export();
    filterOutApiKey(rawData)

    // Remove the html attribute from the nodes to avoid inconsistencies in html
    removeHtmlFromUsers(rawData);

    const exportData = JSON.stringify(rawData, null, 4);
    fetch('/save-workflow', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            filename: fileName,
            workflow: exportData,
            overwrite: false,
        })
    }).then(response => response.json())
        .then(data => {
            if (data.message === "Workflow file saved successfully") {
                Swal.fire('Success', data.message, 'success');
            } else {
                Swal.fire('Error', data.message || 'An error occurred while saving the workflow.', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            Swal.fire('Error', 'An error occurred while saving the workflow.', 'error');
        });
}

function showLoadWorkflowPopup() {
    fetch('/list-workflows', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({})
    })
        .then(response => response.json())
        .then(data => {
            if (!Array.isArray(data.files)) {
                throw new TypeError('The return data is not an array');
            }
            const inputOptions = data.files.reduce((options, file) => {
                options[file] = file;
                return options;
            }, {});
            Swal.fire({
                title: 'Loading Workflow from Disks',
                input: 'select',
                inputOptions: inputOptions,
                inputPlaceholder: 'Select',
                showCancelButton: true,
                showDenyButton: true,
                confirmButtonText: 'Load',
                cancelButtonText: 'Cancel',
                denyButtonText: 'Delete',
                didOpen: () => {
                    const selectElement = Swal.getInput();
                    selectElement.addEventListener('change', (event) => {
                        selectedFilename = event.target.value;
                    });
                }
            }).then(result => {
                if (result.isConfirmed) {
                    loadWorkflow(selectedFilename);
                } else if (result.isDenied) {
                    Swal.fire({
                        title: `Are you sure to delete ${selectedFilename}?`,
                        text: "This operation cannot be undone!",
                        icon: 'warning',
                        showCancelButton: true,
                        confirmButtonColor: '#d33',
                        cancelButtonColor: '#3085d6',
                        confirmButtonText: 'Delete',
                        cancelButtonText: 'Cancel'
                    }).then((deleteResult) => {
                        if (deleteResult.isConfirmed) {
                            deleteWorkflow(selectedFilename);
                        }
                    });
                }
            });
        })
        .catch(error => {
            console.error('Error:', error);
            Swal.fire('Error', 'An error occurred while loading the workflow.', 'error');
        });
}


function loadWorkflow(fileName) {
    fetch('/load-workflow', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            filename: fileName,
        })
    }).then(response => response.json())
        .then(data => {
            if (data.error) {
                Swal.fire('Error', data.error, 'error');
            } else {
                console.log(data)
                try {
                    // Add html source code to the nodes data
                    addHtmlAndReplacePlaceHolderBeforeImport(data)
                        .then(() => {
                            console.log(data)
                            editor.clear();
                            editor.import(data);
                            importSetupNodes(data);
                            Swal.fire('Imported!', '', 'success');
                        });

                } catch (error) {
                    Swal.showValidationMessage(`Import error: ${error}`);
                }
                Swal.fire('Success', 'Workflow loaded successfully', 'success');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            Swal.fire('Error', 'An error occurred while loading the workflow.', 'error');
        });
}

function deleteWorkflow(fileName) {
    fetch('/delete-workflow', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            filename: fileName,
        })
    }).then(response => response.json())
        .then(data => {
            if (data.error) {
                Swal.fire('Error', data.error, 'error');
            } else {
                Swal.fire('Deleted!', 'Workflow has been deleted.', 'success');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            Swal.fire('Error', 'An error occurred while deleting the workflow.', 'error');
        });
}


function removeHtmlFromUsers(data) {
    Object.keys(data.drawflow.Home.data).forEach((nodeId) => {
        const node = data.drawflow.Home.data[nodeId];
        // Remove the html attribute from the node
        delete node.html;
    });
}


async function fetchHtmlSourceCodeByName(name) {
    // Fetch the HTML source code from the cache if it exists
    if (name in htmlCache) {
        return htmlCache[name];
    }

    // Load the HTML source code
    let htmlSourceCode = await fetchHtml(nameToHtmlFile[name]);
    htmlCache[name] = htmlSourceCode;
    return htmlSourceCode;
}


async function addHtmlAndReplacePlaceHolderBeforeImport(data) {
    const idPlaceholderRegex = /ID_PLACEHOLDER/g;
    for (const nodeId of Object.keys(data.drawflow.Home.data)) {
        const node = data.drawflow.Home.data[nodeId];
        if (!node.html) {
            if (node.name === "readme") {
                // Remove the node if its name is "readme"
                delete data.drawflow.Home.data[nodeId];
                continue; // Skip to the next iteration
            }
            console.log(node.name)
            const sourceCode = await fetchHtmlSourceCodeByName(node.name);

            // Add new html attribute to the node
            console.log(sourceCode)
            node.html = sourceCode.replace(idPlaceholderRegex, nodeId);
        }
    }
}


function importSetupNodes(dataToImport) {
    Object.keys(dataToImport.drawflow.Home.data).forEach((nodeId) => {
        setupNodeListeners(nodeId);

        const nodeElement = document.getElementById(`node-${nodeId}`);
        if (nodeElement) {
            const copyButton = nodeElement.querySelector('.button.copy-button');
            if (copyButton) {
                setupNodeCopyListens(nodeId);
            }
        }
    });
}


function copyToClipboard(contentToCopy) {
    var tempTextarea = document.createElement("textarea");
    tempTextarea.value = contentToCopy;
    document.body.appendChild(tempTextarea);
    tempTextarea.select();
    tempTextarea.setSelectionRange(0, 99999);

    try {
        var successful = document.execCommand("copy");
        if (successful) {
            Swal.fire('Copied!', '', 'success');
        } else {
            Swal.fire('Failed to copy', '', 'error');
        }
    } catch (err) {
        Swal.fire('Failed to copy', '', 'error');
    }
    document.body.removeChild(tempTextarea);
}


function fetchExample(index, processData) {
    fetch('/read-examples', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            data: index,
            lang: getCookie('locale') || 'en',
        })
    }).then(response => {
        if (!response.ok) {
            throw new Error('Network error.');
        }
        return response.json();
    })
        .then(processData);
}


function importExample(index) {
    fetchExample(index, data => {
        const dataToImport = data.json;

        addHtmlAndReplacePlaceHolderBeforeImport(dataToImport)
            .then(() => {
                clearModuleSelected();
                editor.import(dataToImport);
                Object.keys(dataToImport.drawflow.Home.data).forEach((nodeId) => {
                    setupNodeListeners(nodeId);
                    setupTextInputListeners(nodeId);
                    const nodeElement = document.getElementById(`node-${nodeId}`);
                    if (nodeElement) {
                        const copyButton = nodeElement.querySelector('.button.copy-button');
                        if (copyButton) {
                            setupNodeCopyListens(nodeId);
                        }
                    }
                });
            });
    })
}


function importExample_step(index) {
    fetchExample(index, data => {
        const dataToImportStep = data.json;
        addHtmlAndReplacePlaceHolderBeforeImport(dataToImportStep).then(() => {
            clearModuleSelected();
            descriptionStep = ["Readme", "Model", "UserAgent",
                "DialogAgent"];
            initializeImport(dataToImportStep);
        })
    });
}


function updateImportButtons() {
    document.getElementById('import-prev').disabled = currentImportIndex
        <= 1;
    document.getElementById('import-next').disabled = currentImportIndex >= importQueue.length;
    document.getElementById('import-skip').disabled = currentImportIndex >= importQueue.length;
}


function createElement(tag, id, html = '', parent = document.body) {
    let element = document.getElementById(id) || document.createElement(tag);
    element.id = id;
    element.innerHTML = html;
    if (!element.parentNode) {
        parent.appendChild(element);
    }
    return element;
}


function initializeImport(data) {
    ['menu-btn', 'menu-btn-svg'].forEach(cls => {
        let containers = document.getElementsByClassName(cls);
        Array.from(containers).forEach(container => container.style.display = 'none');
    });

    createElement('div', 'left-sidebar-blur', '', document.body).style.cssText = `
            position: fixed; top: 60px; left: 0; bottom: 0; width: 250px;
            background: rgba(128, 128, 128, 0.7);
            filter: blur(2px); z-index: 1000; cursor: not-allowed;
        `;

    createElement('div', 'import-buttons', '', document.body);

    dataToImportStep = data;
    importQueue = Object.keys(dataToImportStep.drawflow.Home.data);

    const importButtonsDiv = document.getElementById('import-buttons');
    createElement('div', 'step-info', '', importButtonsDiv);
    createElement('button', 'import-prev',
        '<i class="fas fa-arrow-left"></i> <span>Previous</span>',
        importButtonsDiv).onclick = importPreviousComponent;
    createElement('button', 'import-next',
        '<i class="fas fa-arrow-right"></i> <span>Next</span>',
        importButtonsDiv).onclick = importNextComponent;
    createElement('button', 'import-skip',
        '<i class="fas fa-forward"></i> <span>Skip</span>',
        importButtonsDiv).onclick = importSkipComponent;
    createElement('button', 'import-quit',
        '<i class="fas fa-sign-out-alt"></i> <span>Quit</span>',
        importButtonsDiv).onclick = importQuitComponent;
    createElement('div', 'step-warning',
        'Caution: You are currently in the tutorial mode where modifications are restricted.<br>Please click <strong>Quit</strong> to exit and start creating your custom multi-agent applications.', document.body);

    accumulatedImportData = {};
    currentImportIndex = 0;
    importNextComponent();

    updateImportButtons();
}


function importPreviousComponent() {
    if (currentImportIndex > 0) {
        currentImportIndex--;
        accumulatedImportData = Object.assign({}, ...importQueue.slice(0, currentImportIndex).map(k => ({[k]: dataToImportStep.drawflow.Home.data[k]})));
        editor.import({drawflow: {Home: {data: accumulatedImportData}}});
        updateStepInfo();
    }
    updateImportButtons();
}


function importNextComponent() {
    const nodeId = importQueue[currentImportIndex];
    accumulatedImportData[nodeId] = dataToImportStep.drawflow.Home.data[nodeId];

    editor.import({drawflow: {Home: {data: accumulatedImportData}}});
    currentImportIndex++;
    updateStepInfo();
    updateImportButtons();
}


function importSkipComponent() {
    accumulatedImportData = Object.assign({}, ...importQueue.map(k => ({[k]: dataToImportStep.drawflow.Home.data[k]})));
    editor.import({drawflow: {Home: {data: accumulatedImportData}}});
    currentImportIndex = importQueue.length;
    updateImportButtons();
    updateStepInfo();
}


function importQuitComponent() {
    clearModuleSelected();
    ['menu-btn', 'menu-btn-svg'].forEach(cls => {
        let containers = document.getElementsByClassName(cls);
        Array.from(containers).forEach(container => container.style.display = '');
    });
}


function updateStepInfo() {
    let stepInfoDiv = document.getElementById('step-info');
    if (stepInfoDiv && currentImportIndex > 0) {
        stepInfoDiv.innerHTML =
            `Current Step (${currentImportIndex}/${importQueue.length}) <br> ${descriptionStep[currentImportIndex - 1]}`;
    } else if (stepInfoDiv) {
        stepInfoDiv.innerHTML = 'No steps to display.';
    }
}


function clearModuleSelected() {
    editor.clearModuleSelected();

    let importButtonsDiv = document.getElementById("import-buttons");
    if (importButtonsDiv) {
        importButtonsDiv.remove();
    }

    let stepWarningDiv = document.getElementById("step-warning");
    if (stepWarningDiv) {
        stepWarningDiv.remove();
    }

    let blurDiv = document.getElementById('left-sidebar-blur');
    if (blurDiv) {
        blurDiv.remove();
    }
}


function getCookie(name) {
    var matches = document.cookie.match(new RegExp(
        "(?:^|; )" + name.replace(/([\.$?*|{}\(\)\[\]\\\/\+^])/g, '\\$1') + "=([^;]*)"
    ));
    return matches ? decodeURIComponent(matches[1]) : undefined;
}


function showSurveyModal() {
    document.getElementById("surveyModal").style.display = "block";
}


function hideSurveyModal() {
    document.getElementById("surveyModal").style.display = "none";
}
