let editor;
let currentZIndex = 0;

let mobile_item_selec;
let mobile_last_move;

let importQueue;
let dataToImportStep;
let currentImportIndex;
let accumulatedImportData;
let descriptionStep;
let allimportNodeId = [];
let imporTempData;


const nameToHtmlFile = {
  "welcome": "welcome.html",
  "dashscope_chat": "model-dashscope-chat.html",
  "openai_chat": "model-openai-chat.html",
  "post_api_chat": "model-post-api-chat.html",
  "Message": "message-msg.html",
  "DialogAgent": "agent-dialogagent.html",
  "UserAgent": "agent-useragent.html",
  "DictDialogAgent": "agent-dictdialogagent.html",
  "ReActAgent": "agent-reactagent.html",
  "BroadcastAgent": "agent-broadcastagent.html",
  "Placeholder": "pipeline-placeholder.html",
  "MsgHub": "pipeline-msghub.html",
  "SequentialPipeline": "pipeline-sequentialpipeline.html",
  "ForLoopPipeline": "pipeline-forlooppipeline.html",
  "WhileLoopPipeline": "pipeline-whilelooppipeline.html",
  "IfElsePipeline": "pipeline-ifelsepipeline.html",
  "SwitchPipeline": "pipeline-switchpipeline.html",
  "BingSearchService": "service-bing-search.html",
  "GoogleSearchService": "service-google-search.html",
  "PythonService": "service-execute-python.html",
  "ReadTextService": "service-read-text.html",
  "WriteTextService": "service-write-text.html",
  "Post": "tool-post.html",
  "TextToAudioService": "service-text-to-audio.html",
  "TextToImageService": "service-text-to-image.html",
  "ImageSynthesis": "tool-image-synthesis.html",
  "ImageComposition": "tool-image-composition.html",
  "Code": "tool-code.html",
  // 'IF/ELSE': 'tool-if-else.html',
  "ImageMotion": "tool-image-motion.html",
  "VideoComposition": "tool-video-composition.html",
  "CopyNode": "agent-copyagent.html"
};

const ModelNames48k = [
  "sambert-zhinan-v1",
  "sambert-zhiqi-v1",
  "sambert-zhichu-v1",
  "sambert-zhide-v1",
  "sambert-zhijia-v1",
  "sambert-zhiru-v1",
  "sambert-zhiqian-v1",
  "sambert-zhixiang-v1",
  "sambert-zhiwei-v1",
];

// Cache the loaded html files
const htmlCache = {};

// When clicking the sidebar item, it will expand/collapse the next content
function onClickSidebarSubItem(element) {
  element.classList.toggle("active");
  const content = element.nextElementSibling;
  if (content.style.display === "block") {
    content.style.display = "none";
  } else {
    content.style.display = "block";
  }
}


// Load html source code dynamically
async function fetchHtml(fileName) {
  try {
    const filePath = "static/html-drag-components/" + fileName;
    const response = await fetch(filePath);
    if (!response.ok) {
      throw new Error("Fail to load " + filePath);
    }
    return await response.text();
  } catch (error) {
    return error;
  }
}

async function initializeWorkstationPage() {
  console.log("Initialize Workstation Page");
  // Initialize the Drawflow editor
  const id = document.getElementById("drawflow");
  editor = new Drawflow(id);
  editor.reroute = true;
  editor.createCurvature = function createCurvature(start_pos_x, start_pos_y, end_pos_x, end_pos_y, curvature_value, type) {
    const line_x = start_pos_x;
    const line_y = start_pos_y;
    const x = end_pos_x;
    const y = end_pos_y;
    const curvature = curvature_value;
    //type openclose open close other
    switch (type) {
    case "open":
      if (start_pos_x >= end_pos_x) {
        var hx1 = line_x + Math.abs(x - line_x) * curvature;
        var hx2 = x - Math.abs(x - line_x) * (curvature * -1);
      } else {
        var hx1 = line_x + Math.abs(x - line_x) * curvature;
        var hx2 = x - Math.abs(x - line_x) * curvature;
      }
      return " M " + line_x + " " + line_y + " C " + hx1 + " " + line_y + " " + hx2 + " " + y + " " + x + "  " + y;

    case "close":
      if (start_pos_x >= end_pos_x) {
        var hx1 = line_x + Math.abs(x - line_x) * (curvature * -1);
        var hx2 = x - Math.abs(x - line_x) * curvature;
      } else {
        var hx1 = line_x + Math.abs(x - line_x) * curvature;
        var hx2 = x - Math.abs(x - line_x) * curvature;
      }                                                                                                                  //M0 75H10L5 80L0 75Z
      return " M " + line_x + " " + line_y + " C " + hx1 + " " + line_y + " " + hx2 + " " + y + " " + x + "  " + y + " M " + (x - 11) + " " + y + " L" + (x - 20) + " " + (y - 5) + "  L" + (x - 20) + " " + (y + 5) + "Z";

    case "other":
      if (start_pos_x >= end_pos_x) {
        var hx1 = line_x + Math.abs(x - line_x) * (curvature * -1);
        var hx2 = x - Math.abs(x - line_x) * (curvature * -1);
      } else {
        var hx1 = line_x + Math.abs(x - line_x) * curvature;
        var hx2 = x - Math.abs(x - line_x) * curvature;
      }
      return " M " + line_x + " " + line_y + " C " + hx1 + " " + line_y + " " + hx2 + " " + y + " " + x + "  " + y;

    default:
      var hx1 = line_x + Math.abs(x - line_x) * curvature;
      var hx2 = x - Math.abs(x - line_x) * curvature;

      return " M " + line_x + " " + line_y + " C " + hx1 + " " + line_y + " " + hx2 + " " + y + " " + x + "  " + y + " M " + (x - 11) + " " + y + " L" + (x - 20) + " " + (y - 5) + "  L" + (x - 20) + " " + (y + 5) + "Z";
    }
  };
  editor.start();
  editor.zoom_out();

  const welcome = await fetchHtml("welcome.html");
  const welcomeID = editor.addNode("welcome", 0, 0, 50, 50, "welcome", {}, welcome);
  setupNodeListeners(welcomeID);

  editor.on("nodeCreated", function (id) {
    console.log("Node created " + id);
    disableButtons();
    makeNodeTop(id);
    setupNodeListeners(id);
    setupNodeCopyListens(id);
    addEventListenersToNumberInputs(id);
    setupTextInputListeners(id);
    setupNodeServiceDrawer(id);
    reloadi18n();
  });

  editor.on("nodeRemoved", function (id) {
    console.log("Node removed " + id);
    disableButtons();
    Object.keys(editor.drawflow.drawflow[editor.module].data).forEach(nodeKey => {
      const node = editor.drawflow.drawflow[editor.module].data[nodeKey];
      const nodeData =
                editor.drawflow.drawflow[editor.module].data[nodeKey].data;
      console.log("nodeKey", nodeKey);
      console.log("node", node);
      console.log("nodeData", nodeData);
      console.log("id", id);

      if (nodeData && nodeData.copies) {
        console.log("Array.isArray(nodeData.copies)", Array.isArray(nodeData.copies));
        if (nodeData.copies.includes(id)) {
          console.log("nodeData.copies", nodeData.copies);
          console.log("nodeData.copies.includes(id)",
            nodeData.copies.includes(id));
          const index = nodeData.copies.indexOf(id);
          console.log("index", index);
          if (index > -1) {
            nodeData.copies.splice(index, 1);
            editor.updateNodeDataFromId(nodeKey, nodeData);
          }
        }
      }
    });
  });

  editor.on("nodeSelected", function (id) {
    console.log("Node selected " + id);
    makeNodeTop(id);
  });

  editor.on("moduleCreated", function (name) {
    console.log("Module Created " + name);
  });

  editor.on("moduleChanged", function (name) {
    console.log("Module Changed " + name);
  });

  editor.on("connectionCreated", function (connection) {
    console.log("Connection created");
    console.log(connection);
    disableButtons();
  });

  editor.on("connectionRemoved", function (connection) {
    console.log("Connection removed");
    console.log(connection);
    disableButtons();
  });

  editor.on("mouseMove", function (position) {
    // console.log('Position mouse x:' + position.x + ' y:' + position.y);
  });

  editor.on("zoom", function (zoom) {
    console.log("Zoom level " + zoom);
  });

  editor.on("translate", function (position) {
    console.log("Translate x:" + position.x + " y:" + position.y);
  });

  editor.on("addReroute", function (id) {
    console.log("Reroute added " + id);
  });

  editor.on("removeReroute", function (id) {
    console.log("Reroute removed " + id);
  });

  editor.selectNode = function (id) {
    if (this.node_selected != null) {
      this.node_selected.classList.remove("selected");
      if (this.node_selected !== this.ele_selected) {
        this.dispatch("nodeUnselected", true);
      }
    }
    const element = document.querySelector(`#node-${id}`);
    this.ele_selected = element;
    this.node_selected = element;
    this.node_selected.classList.add("selected");
    if (this.node_selected !== this.ele_selected) {
      this.node_selected = element;
      this.node_selected.classList.add("selected");
      this.dispatch("nodeSelected", this.ele_selected.id.slice(5));
    }
    console.log(id);
  };

  let last_x = 0;
  let last_y = 0;
  let dragElementHover = null;

  editor.on("mouseMove", ({x, y}) => {
    const hoverEles = document.elementsFromPoint(x, y);
    const nextGroup = hoverEles.find(ele => ele.classList.contains("GROUP") && (!editor.node_selected || ele.id !== editor.node_selected.id));

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
      const dx = Math.ceil((last_x - x) * editor.precanvas.clientWidth / (editor.precanvas.clientWidth * editor.zoom));
      const dy = Math.ceil((last_y - y) * editor.precanvas.clientHeight / (editor.precanvas.clientHeight * editor.zoom));

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
          editor.removeConnectionNodeId("node-" + id);
          // Hide the ports when node is inside the group
          togglePortsDisplay(dragNode, "none");
          const dragNodeData = editor.getNodeFromId(dragNode);
          if (dragNodeData.class !== "GROUP") {
            collapseNode(dragNode);
          }
        }
      }
      dragElementHover = null;
    } else {
      // If the node is moved outside of any group, show the ports
      togglePortsDisplay(dragNode, "");
      removeOfGroupNode(dragNode);
    }
    disableButtons();
  });

  editor.on("nodeRemoved", (id) => {
    removeOfGroupNode(id);
  });

  /* DRAG EVENT */

  /* Mouse and Touch Actions */

  const elements = document.getElementsByClassName("workstation-sidebar-dragitem");
  for (let i = 0; i < elements.length; i++) {
    elements[i].addEventListener("touchend", drop, false);
    elements[i].addEventListener("touchmove", positionMobile, false);
    elements[i].addEventListener("touchstart", drag, false);
  }

  mobile_item_selec = "";
  mobile_last_move = null;

  importQueue = [];
  currentImportIndex = 0;
  accumulatedImportData = {};
  descriptionStep = [];
  console.log("importQueue", importQueue);

  document.getElementById("surveyButton").addEventListener("click", function () {
    window.open("https://survey.aliyun.com/apps/zhiliao/vgpTppn22", "_blank");
  });

  document.getElementById("surveyClose").addEventListener("click", function () {
    hideSurveyModal();
  });

  setTimeout(showSurveyModal, 30000);

  if (!localStorage.getItem("firstGuide")) {
    startGuide();
  }
  reloadi18n();
}


function makeNodeTop(id) {
  const node = document.getElementById(`node-${id}`);
  const nodeInfo = editor.getNodeFromId(id);

  if (nodeInfo) {
    console.log("currentZIndex: " + currentZIndex);
    currentZIndex += 1;
    node.style.zIndex = currentZIndex;

    if (nodeInfo.class === "GROUP") {
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
  const contentBox = nodeElement.querySelector(".box");
  const toggleArrow = nodeElement.querySelector(".toggle-arrow");

  contentBox.classList.add("hidden");
  toggleArrow.textContent = "\u25BC";
}


function togglePortsDisplay(nodeId, displayStyle) {
  const nodeElement = document.querySelector(`#node-${nodeId}`);
  if (nodeElement) {
    const inputs = nodeElement.querySelectorAll(".inputs .input");
    const outputs = nodeElement.querySelectorAll(".outputs .output");
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
  });
}


function positionMobile(ev) {
  mobile_last_move = ev;
}


function allowDrop(ev) {
  ev.preventDefault();
}


function drag(ev) {
  if (ev.type === "touchstart") {
    mobile_item_selec = ev.target.closest(".workstation-sidebar-dragitem").getAttribute("data-node");
  } else {
    ev.dataTransfer.setData("node", ev.target.getAttribute("data-node"));
  }
}


function drop(ev) {
  if (ev.type === "touchend") {
    const parentdrawflow = document.elementFromPoint(mobile_last_move.touches[0].clientX, mobile_last_move.touches[0].clientY).closest("#drawflow");
    if (parentdrawflow != null) {
      addNodeToDrawFlow(mobile_item_selec, mobile_last_move.touches[0].clientX, mobile_last_move.touches[0].clientY);
    }
    mobile_item_selec = "";
  } else {
    ev.preventDefault();
    const data = ev.dataTransfer.getData("node");
    addNodeToDrawFlow(data, ev.clientX, ev.clientY);
  }

}


async function addNodeToDrawFlow(name, pos_x, pos_y) {
  if (editor.editor_mode === "fixed") {
    return false;
  }
  pos_x = Math.ceil(pos_x * (editor.precanvas.clientWidth / (editor.precanvas.clientWidth * editor.zoom)) - (editor.precanvas.getBoundingClientRect().x * (editor.precanvas.clientWidth / (editor.precanvas.clientWidth * editor.zoom))));
  pos_y = Math.ceil(pos_y * (editor.precanvas.clientHeight / (editor.precanvas.clientHeight * editor.zoom)) - (editor.precanvas.getBoundingClientRect().y * (editor.precanvas.clientHeight / (editor.precanvas.clientHeight * editor.zoom))));

  const htmlSourceCode = await fetchHtmlSourceCodeByName(name);

  switch (name) {
  // Workflow-Model
  case "dashscope_chat":
    editor.addNode("dashscope_chat", 0, 0, pos_x,
      pos_y,
      "dashscope_chat", {
        "args":
                        {
                          "config_name": "",
                          "model_name": "",
                          "api_key": "",
                          "temperature": 0.0,
                          "seed": 0,
                          "model_type": "dashscope_chat"
                        }
      },
      htmlSourceCode);
    break;

  case "openai_chat":
    editor.addNode("openai_chat", 0, 0, pos_x,
      pos_y,
      "openai_chat", {
        "args":
                        {
                          "config_name": "",
                          "model_name": "",
                          "api_key": "",
                          "temperature": 0.0,
                          "seed": 0,
                          "model_type": "openai_chat"
                        }
      },
      htmlSourceCode);
    break;

  case "post_api_chat":
    editor.addNode("post_api_chat", 0, 0, pos_x, pos_y,
      "post_api_chat", {
        "args":
                        {
                          "config_name": "",
                          "api_url": "",
                          "headers": {
                            "content_type": "application/json",
                            "authorization": "",
                          },
                          "json_args": {
                            "model": "",
                            "temperature": 0.0,
                            "seed": 0,
                          },
                          "model_type": "post_api_chat",
                          "messages_key": "messages"
                        }
      },
      htmlSourceCode);
    break;

    // Message
  case "Message":
    editor.addNode("Message", 1, 1, pos_x,
      pos_y, "Message", {
        "args":
                        {
                          "name": "",
                          "content": "",
                          "url": ""
                        }
      }, htmlSourceCode);
    break;


    // Workflow-Agent
  case "DialogAgent":
    const DialogAgentID = editor.addNode("DialogAgent", 1, 1,
      pos_x,
      pos_y,
      "DialogAgent", {
        "args": {
          "name": "",
          "sys_prompt": "",
          "model_config_name": ""
        }
      }, htmlSourceCode);
    var nodeElement = document.querySelector(`#node-${DialogAgentID} .node-id`);
    if (nodeElement) {
      nodeElement.textContent = DialogAgentID;
    }
    break;

  case "UserAgent":
    const UserAgentID = editor.addNode("UserAgent", 1, 1, pos_x,
      pos_y, "UserAgent", {
        "args": {"name": "User"}
      }, htmlSourceCode);
    var nodeElement = document.querySelector(`#node-${UserAgentID} .node-id`);
    if (nodeElement) {
      nodeElement.textContent = UserAgentID;
    }
    break;

  case "DictDialogAgent":
    const DictDialogAgentID = editor.addNode("DictDialogAgent", 1,
      1, pos_x, pos_y,
      "DictDialogAgent", {
        "args": {
          "name": "",
          "sys_prompt": "",
          "model_config_name": "",
          "parse_func": "",
          "fault_handler": "",
          "max_retries": 3,
        }
      }, htmlSourceCode);
    var nodeElement = document.querySelector(`#node-${DictDialogAgentID} .node-id`);
    if (nodeElement) {
      nodeElement.textContent = DictDialogAgentID;
    }
    break;

  case "ReActAgent":
    const ReActAgentID = editor.addNode("ReActAgent", 1, 1, pos_x, pos_y,
      "GROUP", {
        elements: [],
        "args": {
          "name": "",
          "sys_prompt": "",
          "model_config_name": "",
          "max_iters": 10,
          "verbose": "",
        }
      }, htmlSourceCode);
    var nodeElement = document.querySelector(`#node-${ReActAgentID} .node-id`);
    if (nodeElement) {
      nodeElement.textContent = ReActAgentID;
    }
    break;

  case "BroadcastAgent":
    const BroadcastAgentID = editor.addNode("BroadcastAgent", 1, 1,
      pos_x,
      pos_y,
      "BroadcastAgent", {
        "args": {
          "name": "",
          "content": ""
        }
      }, htmlSourceCode);
    var nodeElement = document.querySelector(`#node-${BroadcastAgentID} .node-id`);
    if (nodeElement) {
      nodeElement.textContent = BroadcastAgentID;
    }
    break;

  case "CopyNode":
    const CopyNodeID = editor.addNode("CopyNode", 1, 1,
      pos_x,
      pos_y,
      "CopyNode", {}, htmlSourceCode);
    var nodeElement = document.querySelector(`#node-${CopyNodeID} .node-id`);
    if (nodeElement) {
      nodeElement.textContent = nodeElement;
    }
    break;

    // Workflow-Pipeline
  case "Placeholder":
    editor.addNode("Placeholder", 1, 1,
      pos_x, pos_y, "Placeholder", {}, htmlSourceCode);
    break;

  case "MsgHub":
    editor.addNode("MsgHub", 1, 1, pos_x, pos_y,
      "GROUP", {
        elements: [],
        "args": {
          "announcement": {
            "name": "",
            "content": ""
          }
        }
      }, htmlSourceCode);
    break;

  case "SequentialPipeline":
    editor.addNode("SequentialPipeline", 1, 1, pos_x, pos_y,
      "GROUP", {elements: []}, htmlSourceCode);
    break;

  case "ForLoopPipeline":
    editor.addNode("ForLoopPipeline", 1, 1, pos_x, pos_y,
      "GROUP", {
        elements: [],
        "args": {
          "max_loop": 3,
          "condition_op": "",
          "target_value": "",
        }
      }, htmlSourceCode);
    break;

  case "WhileLoopPipeline":
    editor.addNode("WhileLoopPipeline", 1, 1, pos_x, pos_y,
      "GROUP", {
        elements: [],
        "args": {
          "condition_func": ""
        }
      }, htmlSourceCode);
    break;

  case "IfElsePipeline":
    editor.addNode("IfElsePipeline", 1,
      1, pos_x, pos_y, "GROUP", {
        elements: [], args: {
          "condition_op": "",
          "target_value": "",
        }
      }, htmlSourceCode);
    break;

  case "SwitchPipeline":
    const SwitchPipelineID = editor.addNode("SwitchPipeline", 1, 1, pos_x, pos_y, "GROUP", {
      elements: [], args: {
        "condition_func": "",
        "cases": [],
      }
    }, htmlSourceCode);
    break;

    // Workflow-Service
  case "BingSearchService":
    editor.addNode("BingSearchService", 0, 0,
      pos_x, pos_y, "BingSearchService", {
        "args": {
          "api_key": "",
          "num_results": 3,
        }
      }, htmlSourceCode);
    break;

  case "GoogleSearchService":
    editor.addNode("GoogleSearchService", 0, 0,
      pos_x, pos_y, "GoogleSearchService", {
        "args": {
          "api_key": "",
          "cse_id": "",
          "num_results": 3,
        }
      }, htmlSourceCode);
    break;

  case "PythonService":
    editor.addNode("PythonService", 0, 0,
      pos_x, pos_y, "PythonService", {}, htmlSourceCode);
    break;

  case "ReadTextService":
    editor.addNode("ReadTextService", 0, 0,
      pos_x, pos_y, "ReadTextService", {}, htmlSourceCode);
    break;

  case "WriteTextService":
    editor.addNode("WriteTextService", 0, 0,
      pos_x, pos_y, "WriteTextService", {}, htmlSourceCode);
    break;

  case "TextToAudioService":
    const TextToAudioServiceID = editor.addNode("TextToAudioService", 0, 0,
      pos_x, pos_y, "TextToAudioService", {
        "args": {
          "model": "",
          "api_key": "",
          "sample_rate": ""
        }
      }, htmlSourceCode);
    break;
  case "TextToImageService":
    editor.addNode("TextToImageService", 0, 0,
      pos_x, pos_y, "TextToImageService", {
        "args": {
          "model": "",
          "api_key": "",
          "n": 1,
          "size": ""
        }
      }, htmlSourceCode);
    break;

  case "ImageSynthesis":
    editor.addNode("ImageSynthesis", 1, 1,
      pos_x, pos_y, "ImageSynthesis", {
        "args": {
          "model": "",
          "api_key": "",
          "n": 1,
          "size": "",
          "save_dir": ""
        }
      }, htmlSourceCode);
    break;

  case "ImageComposition":
    editor.addNode("ImageComposition", 1, 1,
      pos_x, pos_y, "ImageComposition", {
        "args": {
          "titles": "",
          "output_path": "",
          "row": 1,
          "column": 1,
          "spacing": 10,
          "title_height": 100,
          "font_name": "PingFang",
        }
      }, htmlSourceCode);
    break;
  case "Code":
    const CodeID = editor.addNode("Code", 1, 1,
      pos_x, pos_y, "Code", {
        "args": {
          "code": "def function(msg1: Msg) -> Msg:\n    content1 = msg1.get(\"content\", \"\")\n    return {\n        \"role\": \"assistant\",\n        \"content\": content1,\n        \"name\": \"function\",\n    }"
        }
      }, htmlSourceCode);
    break;

  case "ImageMotion":
    editor.addNode("ImageMotion", 1, 1,
      pos_x, pos_y, "ImageMotion", {
        "args": {
          "output_path": "",
          "output_format": "",
          "duration": "",
        }
      }, htmlSourceCode);
    break;

  case "VideoComposition":
    editor.addNode("VideoComposition", 1, 1,
      pos_x, pos_y, "VideoComposition", {
        "args": {
          "output_path": "",
          "target_width": "",
          "target_height": "",
          "fps": "",
        }
      }, htmlSourceCode);
    break;

  case "Post":
    editor.addNode("Post", 1, 1,
      pos_x, pos_y, "Post", {
        "args": {
          "url": "",
          "headers": "",
          "data": "",
          "json": "",
          "kwargs": "",
          "output_path": "",
          "output_type": "",
        }
      }, htmlSourceCode);
    break;

  default:
  }
}


function initializeMonacoEditor(nodeId) {
  require.config({
    paths: {
      vs: "https://cdn.jsdelivr.net/npm/monaco-editor@latest/min/vs",
    },
  });

  require(["vs/editor/editor.main"], function () {
    const parentSelector = `#node-${nodeId}`;
    const parentNode = document.querySelector(parentSelector);

    if (!parentNode) {
      console.error(`Parent node with selector ${parentSelector} not found.`);
      return;
    }

    const codeContentElement = parentNode.querySelector(".code-content");
    if (!codeContentElement) {
      return;
    }

    const node = editor.getNodeFromId(nodeId);
    if (!node) {
      console.error(`Node with ID ${nodeId} not found.`);
      return;
    }

    const editorInstance = monaco.editor.create(codeContentElement, {
      value: node.data.args.code,
      language: "python",
      theme: "vs-light",
      minimap: {
        enabled: false,
      },
      wordWrap: "on",
      lineNumbersMinChars: 1,
      scrollBeyondLastLine: false,
      readOnly: false,
    });

    editorInstance.onDidChangeModelContent(function () {
      const updatedNode = editor.getNodeFromId(nodeId);
      if (updatedNode) {
        updatedNode.data.args.code = editorInstance.getValue().trim();
        editor.updateNodeDataFromId(nodeId, updatedNode.data);
      }
    });

    const resizeObserver = new ResizeObserver(() => {
      editorInstance.layout();
    });
    resizeObserver.observe(parentNode);
    parentNode.addEventListener("DOMNodeRemoved", function () {
      resizeObserver.disconnect();
    });
  }, function (error) {
    console.error("Error encountered while loading monaco editor: ", error);
  });
}


function updateSampleRate(nodeId) {
  const newNode = document.getElementById(`node-${nodeId}`);
  if (!newNode) {
    console.error(`Node with ID node-${nodeId} not found.`);
    return;
  }

  const modelNameInput = newNode.querySelector("#model_name");

  function updateSampleRateValue() {
    const modelName = modelNameInput ? modelNameInput.value : "";

    if (ModelNames48k.includes(modelName)) {
      sampleRate = 48000;
    } else {
      sampleRate = 16000;
    }

    const sampleRateInput = newNode.querySelector("#sample_rate");

    if (sampleRateInput) {
      sampleRateInput.value = sampleRate;
      const nodeData = editor.getNodeFromId(nodeId).data;
      nodeData.args.sample_rate = sampleRate;
      nodeData.args.model = modelName;
      editor.updateNodeDataFromId(nodeId, nodeData);

      console.log(`${modelName} sample rate updated to: ${sampleRate}`);
    } else {
      console.log("Sample Rate input not found.");
    }
  }

  if (modelNameInput) {
    modelNameInput.addEventListener("input", updateSampleRateValue);
  }
}

function setupTextInputListeners(nodeId) {
  const newNode = document.getElementById(`node-${nodeId}`);
  if (newNode) {
    const stopPropagation = function (event) {
      event.stopPropagation();
    };
    newNode.addEventListener("mousedown", function (event) {
      const target = event.target;
      if (target.tagName === "TEXTAREA" || target.tagName === "INPUT" || target.closest(".code-content")) {
        stopPropagation(event);
      }
    }, false);
  }
}

function toggleAdvanced() {
  const advancedBox = document.querySelector(".advanced-box");
  if (advancedBox.style.display === "none") {
    advancedBox.style.display = "block";
  } else {
    advancedBox.style.display = "none";
  }
}


function handleInputChange(event) {
  const input = event.target;

  if (input.type === "number") {
    const value = input.value;
    const floatValue = parseFloat(value);
    const nodeId = input.closest(".drawflow_content_node").parentElement.id.slice(5);

    if (!isNaN(floatValue)) {
      const node = editor.getNodeFromId(nodeId);
      const dataAttributes =
                Array.from(input.attributes).filter(attr =>
                  attr.name.startsWith("df-args-"));
      dataAttributes.forEach(attr => {
        const attrName = attr.name;
        if (attrName.startsWith("df-args-json_args-")) {
          const dataAttribute = attrName.substring(18);
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
    const numberInputs = nodeElement.querySelectorAll("input[type=number]");
    numberInputs.forEach(input => {
      input.addEventListener("change", handleInputChange);
    });
  }
}


function validateTemperature(input) {
  const value = input.valueAsNumber;
  if (isNaN(value) || value < 0 || value >= 2) {
    input.setCustomValidity("Temperature must be greater or equal than 0 and less than 2!");
  } else {
    input.setCustomValidity("");
  }
  input.reportValidity();
}


function validateSeed(input) {
  const value = parseInt(input.value, 10); // Parse the value as an integer.
  if (isNaN(value) || value < 0 || !Number.isInteger(parseFloat(input.value))) {
    input.setCustomValidity("Seed must be a non-negative integer!");
  } else {
    input.setCustomValidity("");
  }
  input.reportValidity();
}

function validateDuration(input) {
  const value = parseInt(input.value, 10); // Parse the value as an integer.
  if (isNaN(value) || value < 0 || !Number.isInteger(parseFloat(input.value))) {
    input.setCustomValidity("Duration must be a non-negative integer!");
  } else {
    input.setCustomValidity("");
  }
  input.reportValidity();
}


document.addEventListener("input", function (event) {
  const input = event.target;

  if (input.getAttribute("df-args-temperature") !== null ||
        input.getAttribute("df-args-json_args-temperature") !== null) {
    validateTemperature(input);
  }

  if (input.getAttribute("df-args-seed") !== null ||
        input.getAttribute("df-args-json_args-seed") !== null) {
    validateSeed(input);
  }

  if (input.getAttribute("df-args-duration") !== null) {
    validateDuration(input);
  }
});

var transform = "";


function updateReadmeAndTrimExtrasInHTML(htmlString, nodeId) {
  const parser = new DOMParser();
  const doc = parser.parseFromString(htmlString, "text/html");
  const containerDiv = doc.body.firstChild;

  removeNonReadmeChildren(containerDiv);
  updateReadmeContent(containerDiv, nodeId);

  return containerDiv.innerHTML;
}

function updateReadmeContent(containerDiv, nodeId) {
  const readmeDiv = containerDiv.querySelector(".readme");
  if (readmeDiv) {
    console.log("readmeDiv", readmeDiv);

    const newDiv = document.createElement("div");
    newDiv.innerHTML = `Copy from Node ID: ${nodeId}`;
    readmeDiv.appendChild(newDiv);

    console.log("readmeDiv after", readmeDiv);
  }
}

function removeNonReadmeChildren(containerDiv) {
  const boxDiv = containerDiv.querySelector(".box");
  if (boxDiv) {
    boxDiv.querySelectorAll("*:not(.readme)").forEach(child => child.remove());
  }
}

function createNodeHTML(node, isCopy, originalNodeId) {
  const modifiedHtml = isCopy ? processNodeCopyHTML(node.html) : node.html;
  return updateReadmeAndTrimExtrasInHTML(modifiedHtml, originalNodeId);
}

function processNodeCopyHTML(htmlString) {
  const parser = new DOMParser();
  const doc = parser.parseFromString(htmlString, "text/html");

  [".copy-button", "div .node-id"].forEach(selector => {
    const element = doc.querySelector(selector);
    if (element) {
      element.remove();
    }
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
    posX, posY, "node-" + originalNode.name, {elements: [originalNodeId.toString()]},
    newNodeHTML);
}

function setupNodeCopyListens(nodeId) {
  const newNode = document.getElementById(`node-${nodeId}`);
  if (newNode) {
    const copyButton = newNode.querySelector(".copy-button");
    if (copyButton) {
      copyButton.addEventListener("click", function () {
        copyNode(nodeId);
      });
    }
  }
}

function hideShowGroupNodes(groupId, show) {
  const groupInfo = editor.getNodeFromId(groupId);
  if (groupInfo && groupInfo.class === "GROUP") {
    groupInfo.data.elements.forEach(elementNodeId => {
      const elementNode = document.getElementById(`node-${elementNodeId}`);
      const childNodeInfo = editor.getNodeFromId(elementNodeId);
      const contentBox = elementNode.querySelector(".box") ||
                elementNode.querySelector(".box-highlight");
      if (elementNode) {
        elementNode.style.display = show ? "" : "none";
      }
      if (childNodeInfo.class === "GROUP") {
        if (!show || (contentBox && !contentBox.classList.contains("hidden"))) {
          hideShowGroupNodes(elementNodeId, show);
        }
      }
    });
  }
}

function setupConditionListeners(nodeId) {
  const newNode = document.getElementById(`node-${nodeId}`);
  if (newNode) {
    const conditionOp = newNode.querySelector("#condition_op");
    const targetContainer = newNode.querySelector("#target-container");
    console.log(conditionOp, targetContainer);

    function updateTargetVisibility() {
      const condition_op = conditionOp ? conditionOp.value : "";
      const hideConditions = ["", "is empty", "is null", "is not empty", "is not null"];
      if (hideConditions.includes(condition_op)) {
        targetContainer.style.display = "none";
      } else {
        targetContainer.style.display = "block";
      }
    }

    if (conditionOp) {
      conditionOp.addEventListener("input", updateTargetVisibility);
      updateTargetVisibility();
    }
  }
}

function setupNodeListeners(nodeId) {
  const newNode = document.getElementById(`node-${nodeId}`);
  if (newNode) {

    initializeMonacoEditor(nodeId);
    setupConditionListeners(nodeId);
    updateSampleRate(nodeId);
    setupSwitchPipelineListeners(nodeId);

    const titleBox = newNode.querySelector(".title-box");
    const contentBox = newNode.querySelector(".box") ||
            newNode.querySelector(".box-highlight");

    // Add resize handle to the bottom right corner of the node
    const resizeHandleSE = document.createElementNS("http://www.w3.org/2000/svg", "svg");

    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("d", "M932.37602347 512.88874453l-420.37602347 420.37602347 56.43525867 56.43525867 420.37602453-420.37602347-56.43525973-56.43525867z m-3.55497707-474.58942293L34.29997333 933.264768l56.43525867 56.43525867L985.25630613 95.1789536l-56.43525973-56.879632z");

    resizeHandleSE.setAttribute("viewBox", "0 0 1024 1024");
    resizeHandleSE.appendChild(path);

    resizeHandleSE.classList.add("resize-handle-se");

    contentBox.appendChild(resizeHandleSE);

    const toggleArrow = newNode.querySelector(".toggle-arrow");

    if (toggleArrow && contentBox && titleBox) {
      toggleArrow.addEventListener("click", function () {
        const serivceArr = ["BingSearchService", "GoogleSearchService", "PythonService", "ReadTextService", "WriteTextService", "TextToAudioService", "AudioToTextService"];
        if (serivceArr.includes(newNode.querySelector(".title-box").getAttribute("data-class"))) {
          return;
        }
        contentBox.classList.toggle("hidden");

        if (contentBox.classList.contains("hidden")) {
          toggleArrow.textContent = "\u25BC";
          hideShowGroupNodes(nodeId, false);
        } else {
          toggleArrow.textContent = "\u25B2";
          hideShowGroupNodes(nodeId, true);
        }
        editor.updateConnectionNodes("node-" + nodeId);
      });

      let startX, startY, startWidth, startHeight;

      resizeHandleSE.addEventListener("mousedown", function (e) {
        e.stopPropagation();
        document.addEventListener("mousemove", doDragSE, false);
        document.addEventListener("mouseup", stopDragSE, false);

        startX = e.clientX;
        startY = e.clientY;
        startWidth = parseInt(document.defaultView.getComputedStyle(contentBox).width, 10);
        startHeight = parseInt(document.defaultView.getComputedStyle(contentBox).height, 10);
      });

      function doDragSE(e) {
        newNode.style.width = "auto";
        newNode.style.height = "auto";

        const newWidth = (startWidth + e.clientX - startX);
        if (newWidth > 200) {
          contentBox.style.width = newWidth + "px";
          titleBox.style.width = newWidth + "px";
        }

        const newHeight = (startHeight + e.clientY - startY);
        contentBox.style.height = newHeight + "px";

        editor.updateConnectionNodes("node-" + nodeId);
      }

      function stopDragSE(e) {
        document.removeEventListener("mousemove", doDragSE, false);
        document.removeEventListener("mouseup", stopDragSE, false);
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
  const addCaseButton = newNode.querySelector(".add-case");
  if (!addCaseButton) {
    return;
  }
  addCaseButton.addEventListener("click", function () {
    const caseContainer = newNode.querySelector(".case-container");
    if (!caseContainer) {
      console.error(`Case container not found in node-${nodeId}.`);
      return;
    }
    const defaultCaseElement = caseContainer.querySelector(".default-case");
    if (defaultCaseElement) {
      caseContainer.removeChild(defaultCaseElement);
    }
    const caseCount = caseContainer.getElementsByClassName("case-placeholder").length;
    const caseElement = document.createElement("div");
    caseElement.classList.add("case-placeholder");

    const caseText = document.createTextNode(`Case ${caseCount + 1}: `);
    caseElement.appendChild(caseText);

    const inputElement = document.createElement("input");
    inputElement.type = "text";
    inputElement.placeholder = "Case Pattern";

    inputElement.dataset.caseIndex = caseCount;

    caseElement.appendChild(inputElement);
    caseContainer.appendChild(caseElement);

    inputElement.addEventListener("input", function (e) {
      const nodeData = editor.getNodeFromId(nodeId).data;
      console.log("nodeData", nodeData);
      const index = e.target.dataset.caseIndex;
      console.log("index", index);
      nodeData.args.cases[index] = e.target.value;
      editor.updateNodeDataFromId(nodeId, nodeData);
    });

    editor.getNodeFromId(nodeId).data.args.cases.push("");

    addDefaultCase(caseContainer);
    editor.updateConnectionNodes("node-" + nodeId);
  });

  const removeCaseButton = newNode.querySelector(".remove-case");
  if (!removeCaseButton) {
    return;
  }
  removeCaseButton.addEventListener("click", function () {
    const caseContainer = newNode.querySelector(".case-container");
    const cases = caseContainer.getElementsByClassName("case-placeholder");
    if (cases.length > 1) {
      caseContainer.removeChild(cases[cases.length - 2]);
      const nodeData = editor.getNodeFromId(nodeId).data;
      nodeData.args.cases.splice(nodeData.args.cases.length - 1, 1);
      editor.updateNodeDataFromId(nodeId, nodeData);
    }
    editor.updateConnectionNodes("node-" + nodeId);
  });

  const caseContainer = newNode.querySelector(".case-container");
  if (!caseContainer) {
    console.error(`Case container not found in node-${nodeId}.`);
    return;
  }

  const defaultCaseElement = caseContainer.querySelector(".default-case");
  if (defaultCaseElement) {
    caseContainer.removeChild(defaultCaseElement);
  }

  const cases = editor.getNodeFromId(nodeId).data.args.cases;
  for (let caseCount = 0; caseCount < cases.length; caseCount++) {

    const caseElement = document.createElement("div");
    caseElement.classList.add("case-placeholder");

    const caseText = document.createTextNode(`Case ${caseCount + 1}: `);
    caseElement.appendChild(caseText);

    const inputElement = document.createElement("input");
    inputElement.type = "text";
    inputElement.placeholder = "Case Pattern";
    inputElement.value = cases[caseCount];

    inputElement.dataset.caseIndex = caseCount;

    caseElement.appendChild(inputElement);
    caseContainer.appendChild(caseElement);

    inputElement.addEventListener("input", function (e) {
      const nodeData = editor.getNodeFromId(nodeId).data;
      console.log("nodeData", nodeData);
      const index = e.target.dataset.caseIndex;
      console.log("index", index);
      nodeData.args.cases[index] = e.target.value;
      editor.updateNodeDataFromId(nodeId, nodeData);
    });
  }
  addDefaultCase(caseContainer);
}

function addDefaultCase(caseContainer) {
  const defaultCaseElement = document.createElement("div");
  defaultCaseElement.classList.add("case-placeholder", "default-case");
  defaultCaseElement.textContent = "Default Case";
  caseContainer.appendChild(defaultCaseElement);
}


function closemodal(e) {
  e.target.closest(".drawflow-node").style.zIndex = "2";
  e.target.parentElement.parentElement.style.display = "none";
  editor.precanvas.style.transform = transform;
  editor.precanvas.style.left = "0px";
  editor.precanvas.style.top = "0px";
  editor.editor_mode = "edit";
}


function changeModule(event) {
  const all = document.querySelectorAll(".menu ul li");
  for (let i = 0; i < all.length; i++) {
    all[i].classList.remove("selected");
  }
  event.target.classList.add("selected");
  importSetupNodes(editor.drawflow);
}


function changeLockMode(option) {
  const lockSvg = document.getElementById("lock-svg");
  const unlockSvg = document.getElementById("unlock-svg");
  if (option === "lock") {
    editor.editor_mode = "edit";
    lockSvg.style.display = "none";
    unlockSvg.style.display = "block";
  } else {
    editor.editor_mode = "fixed";
    lockSvg.style.display = "block";
    unlockSvg.style.display = "none";
  }
}


function toggleDraggable(element) {
  const content = element.nextElementSibling;
  if (content.classList.contains("visible")) {
    content.classList.remove("visible");
  } else {
    content.classList.add("visible");
  }
}


function filterEmptyValues(obj) {
  return Object.entries(obj).reduce((acc, [key, value]) => {
    if (Array.isArray(value)) {
      const filteredArray = value.map(item => {
        if (typeof item === "object" && item !== null) {
          return filterEmptyValues(item);
        }
        return item !== "" ? item : null;
      }).filter(item => item !== null);

      if (filteredArray.length > 0) {
        acc[key] = filteredArray;
      }
    } else if (typeof value === "object" && value !== null) {
      const filteredNestedObj = filterEmptyValues(value);
      if (Object.keys(filteredNestedObj).length > 0) {
        acc[key] = filteredNestedObj;
      }
    } else if (value !== "") {
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
    if (nodeName === "welcome" || nodeName === "readme") {
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
      if (node.class === "GROUP" && node.name !== "ReActAgent") {
        const elements = node.data.elements;
        const elementsWithPosition = elements.map(elementId => {
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
            const y1 = parseInt(a.position.y, 10);
            const y2 = parseInt(b.position.y, 10);
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
  let hasModelTypeError = false;
  let hasAgentError = false;
  const agentModelConfigNames = new Set();
  const modelConfigNames = new Set();
  let isApiKeyEmpty = false;
  const nodesData = editor.export().drawflow.Home.data;

  for (const nodeId in nodesData) {
    const node = nodesData[nodeId];
    console.log("node", node);
    console.log("node.inputs", node.inputs);

    const nodeElement = document.getElementById("node-" + nodeId);
    const requiredInputs = nodeElement.querySelectorAll("input[data-required=\"true\"]");

    const titleBox = nodeElement.querySelector(".title-box");

    const titleText = titleBox.getAttribute("data-class");

    for (const input of requiredInputs) {
      if (input.value.trim() === "") {
        const inputLabel = input.previousElementSibling;
        if (inputLabel && inputLabel.tagName.toLowerCase() === "label") {
          const labelText = inputLabel.textContent.trim();

          Swal.fire({
            title: "Value Missing!",
            text: `${labelText} is missing in ${titleText}.`,
            icon: "error",
            confirmButtonText: "Ok"
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
    if (node.name.includes("Agent") && "model_config_name" in node.data.args) {
      hasAgentError = false;
      if (node.data && node.data.args) {
        agentModelConfigNames.add(node.data.args.model_config_name);
      }
    }
    if (node.name === "ReActAgent") {
      const elements = node.data.elements;
      for (const nodeId of elements) {
        const childNode = nodesData[nodeId];
        if (!childNode || !childNode.name.includes("Service")) {
          Swal.fire({
            title: "Invalid ReActAgent Configuration",
            text:
                            "ReActAgent must only contain Tool nodes as child nodes.",
            icon: "error",
            confirmButtonText: "Ok"
          });
          return false;
        }
      }
    }
    if (node.name === "IfElsePipeline") {
      const elementsSize = node.data.elements.length;
      if (elementsSize !== 1 && elementsSize !== 2) {
        Swal.fire({
          title: "Invalid IfElsePipeline Configuration",
          text: `IfElsePipeline should have 1 or 2 elements, but has ${elementsSize}.`,
          icon: "error",
          confirmButtonText: "Ok"
        });
        return false;
      }
    }
    if (["ForLoopPipeline", "WhileLoopPipeline", "MsgHub"].includes(node.name)) {
      if (node.data.elements.length !== 1) {
        hasError = true;
        Swal.fire({
          title: "Invalid Configuration",
          text: `${node.name} must have exactly one element.`,
          icon: "error",
          confirmButtonText: "Ok"
        });
        return false;
      }
      const childNodeId = node.data.elements[0];
      const childNode = nodesData[childNodeId];
      if (!childNode || !childNode.name.includes("Pipeline")) {
        Swal.fire({
          title: "Invalid Configuration",
          text:
                        ` ${childNode.name} contained in ${node.name} is not a Pipeline node.`,
          icon: "error",
          confirmButtonText: "Ok"
        });
        return false;
      }
    }
    if (node.name === "Code") {
      const code = node.data.args.code;
      const pattern = /\bdef\s+function\s*\(/;

      if (!pattern.test(code)) {
        Swal.fire({
          title: "Invalid Code Function Name",
          text: `${node.name} only support "function" as the function name.`,
          icon: "error",
          confirmButtonText: "Ok"
        });
        return false;
      }
    }
  }

  const unmatchedConfigNames = [...agentModelConfigNames].filter(name => !modelConfigNames.has(name));
  console.log("modelConfigNames", modelConfigNames);
  console.log("agentModelConfigNames", agentModelConfigNames);
  console.log("unmatchedConfigNames", unmatchedConfigNames);
  if (hasModelTypeError) {
    Swal.fire({
      title: "Error!",
      text:
                "Error: At least one Model node must be present.",
      icon: "error",
      confirmButtonText: "Ok"
    });
  } else if (hasAgentError) {
    Swal.fire({
      title: "No Agent Nodes Found",
      text: "Error: At least one Agent node must be present.",
      icon: "error",
      confirmButtonText: "Ok"
    });
  } else if (unmatchedConfigNames.length > 0) {
    Swal.fire({
      title: "Configuration Mismatch",
      html:
                "Each Agent's 'Model config name' must match a Model node's 'Config Name'.<br> Unmatched: " + unmatchedConfigNames.join(", "),
      icon: "error",
      confirmButtonText: "Ok"
    });
  } else if (isApiKeyEmpty) {
    Swal.fire({
      title: "API KEY Missing",
      text:
                "API KEY is missing in your model nodes. Please either enter the API KEY in the corresponding position, or enter a random bit of content and replace it with the real value in the exported files.",
      icon: "error",
      confirmButtonText: "Ok"
    });
  } else {
    return true;
  }
}


function showCheckPopup() {
  const btnCovers = document.querySelectorAll(".btn-cover");
  if (checkConditions()) {
    Swal.fire({
      title: "Validation Success",
      text: "All checks are passed!",
      icon: "success",
      confirmButtonText: "Great!"
    });
    btnCovers.forEach(function (btnCover) {
      const button = btnCover.querySelector(".btn-disabled");
      if (button) {
        button.classList.remove("btn-disabled");
      }
      btnCover.removeAttribute("data-title");
    });
  }
}


function disableButtons() {
  const btnCovers = document.querySelectorAll(".btn-cover");

  btnCovers.forEach(function (btnCover) {
    const button = btnCover.querySelector("div");
    if (button) {
      button.classList.add("btn-disabled");
    }
    btnCover.setAttribute("data-title",
      "Please click the \"Check\" button first.");
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
      title: "Processing...",
      text: "Please wait.",
      allowOutsideClick: false,
      willOpen: () => {
        Swal.showLoading();
      }
    });

    fetch("/convert-to-py", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        data: JSON.stringify(filteredData, null, 4),
      })
    }).then(response => {
      if (!response.ok) {
        throw new Error("Network error.");
      }
      return response.json();
    })
      .then(data => {
        Swal.close();
        if (data.is_success === "True") {
          Swal.fire({
            title: "<b>Workflow Python Code</b>",
            html:
                            "<p>Save as main.py<br>" +
                            "Then run the following command in your terminal:<br>" +
                            "<div class=\"code-snippet\">python main.py</div><br>" +
                            "or <div class=\"code-snippet\">as_gradio main.py</div></p>" +
                            "<pre class=\"line-numbers\"><code class=\"language-py\" id=\"export-data\">" +
                            data.py_code +
                            "</code></pre>",
            showCloseButton: true,
            showCancelButton: true,
            confirmButtonText: "Copy",
            cancelButtonText: "Close",
            willOpen: (element) => {
              const codeElement = element.querySelector("code");
              Prism.highlightElement(codeElement);
              const copyButton = Swal.getConfirmButton();
              copyButton.addEventListener("click", () => {
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
            title: "Error!",
            html: errorMessage,
            icon: "error",
            customClass: {
              popup: "error-popup"
            },
            confirmButtonText: "Close",
            willOpen: (element) => {
              const codeElement = element.querySelector("code");
              Prism.highlightElement(codeElement);
            }
          });
        }
      })
      .catch(error => {
        console.error("Error:", error);
        Swal.fire("Failed!",
          "There was an error generating your code.",
          "error");
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
      title: "Processing...",
      text: "Please wait.",
      allowOutsideClick: false,
      willOpen: () => {
        Swal.showLoading();
      }
    });

    fetch("/convert-to-py-and-run", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        data: JSON.stringify(filteredData, null, 4),
      })
    }).then(response => {
      if (!response.ok) {
        throw new Error("Network error.");
      }
      return response.json();
    })
      .then(data => {
        Swal.close();
        if (data.is_success === "True") {
          Swal.fire({
            title: "<b>Application Running in Background</b>",
            html:
                            "<p>Your application has been successfully run " +
                            "in background.<br>" +
                            "<p><strong>Task ID:</strong>" +
                            data.run_id + "</p>" +
                            "<pre class=\"line-numbers\"><code class=\"language-py\" id=\"export-data\">" +
                            data.py_code +
                            "</code></pre>",
            showCloseButton: true,
            showCancelButton: true,
            confirmButtonText: "Copy Code",
            cancelButtonText: "Close",
            willOpen: (element) => {
              const codeElement = element.querySelector("code");
              Prism.highlightElement(codeElement);
              const copyButton = Swal.getConfirmButton();
              copyButton.addEventListener("click", () => {
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
            title: "Error!",
            html: errorMessage,
            icon: "error",
            customClass: {
              popup: "error-popup"
            },
            confirmButtonText: "Close",
            willOpen: (element) => {
              const codeElement = element.querySelector("code");
              Prism.highlightElement(codeElement);
            }
          });
        }
      })
      .catch(error => {
        console.error("Error:", error);
        Swal.close();
        Swal.fire("Failed!",
          "There was an error running your workflow.",
          "error");
      });
  }
}


function filterOutApiKey(obj) {
  for (const key in obj) {
    if (typeof obj[key] === "object" && obj[key] !== null) {
      filterOutApiKey(obj[key]);
    }
    if (key === "api_key") {
      delete obj[key];
    }
  }
}


function showExportRunMSPopup() {
  if (checkConditions()) {
    Swal.fire({
      title: "Are you sure to run the workflow in ModelScope Studio?",
      text:
                "You are about to navigate to another page. " +
                "Please make sure all the configurations are set " +
                "besides your api-key " +
                "(your api-key should be set in ModelScope Studio page).",
      icon: "warning",
      showCancelButton: true,
      confirmButtonColor: "#3085d6",
      cancelButtonColor: "#d33",
      confirmButtonText: "Yes, create it!",
      cancelButtonText: "Close"
    }).then((result) => {
      if (result.isConfirmed) {
        const rawData = editor.export();
        const hasError = sortElementsByPosition(rawData);
        if (hasError) {
          return;
        }
        const filteredData = reorganizeAndFilterConfigForAgentScope(rawData);
        filterOutApiKey(filteredData);

        Swal.fire({
          title: "Processing...",
          text: "Please wait.",
          allowOutsideClick: false,
          willOpen: () => {
            Swal.showLoading();
          }
        });
        fetch("/upload-to-oss", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            data: JSON.stringify(filteredData, null, 4),
          })
        })
          .then(response => response.json())
          .then(data => {
            const params = {"CONFIG_URL": data.config_url};
            const paramsStr = encodeURIComponent(JSON.stringify(params));
            const org = "agentscope";
            const fork_repo = "agentscope_workstation";
            const url = `https://www.modelscope.cn/studios/fork?target=${org}/${fork_repo}&overwriteEnv=${paramsStr}`;
            window.open(url, "_blank");
            Swal.fire("Success!", "", "success");
          })
          .catch(error => {
            console.error("Error:", error);
            Swal.fire("Failed", data.message || "An error occurred while uploading to oss", "error");
          });
      }
    });
  }
}


function showExportHTMLPopup() {
  const rawData = editor.export();
  const currentZoom = editor.zoom;

  Object.keys(rawData.drawflow.Home.data).forEach((nodeId) => {
    const nodeElement = document.getElementById(`node-${nodeId}`);
    const nodeData = rawData.drawflow.Home.data[nodeId];
    if (nodeElement) {
      const rect = nodeElement.getBoundingClientRect();
      nodeData.width = (rect.width / currentZoom) + "px";
      nodeData.height = (rect.height / currentZoom) + "px";
    }
  });
  const hasError = sortElementsByPosition(rawData);
  if (hasError) {
    return;
  }

  removeHtmlFromUsers(rawData);

  const exportData = JSON.stringify(rawData, null, 4);
  const escapedExportData = exportData
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  Swal.fire({
    title: "<b>Workflow HTML</b>",
    html:
            "<p>This is used for generating HTML code, not for running.<br>" +
            "<pre class=\"line-numbers\"><code class=\"language-javascript\" id=\"export-data\">"
            + escapedExportData +
            "</code></pre>",
    showCloseButton: true,
    showCancelButton: true,
    confirmButtonText: "Copy",
    cancelButtonText: "Close",
    willOpen: (element) => {
      const codeElement = element.querySelector("code");
      Prism.highlightElement(codeElement);

      const copyButton = Swal.getConfirmButton();
      copyButton.addEventListener("click", () => {
        copyToClipboard(codeElement.textContent);
      });
    }
  });
}


function showContributePopup(userLogin) {
  if (userLogin.startsWith("guest_") || userLogin === "local_user") {
    if(getCookie("locale") == "zh"){
      Swal.fire(
        "Error",
        "要分享您的workflow，您需要通过 agentscope.io 登录 GitHub账号。请登录后重试。",
        "error"
      );
      return;
    } else {
      Swal.fire(
        "Error",
        "You need to be logged into GitHub via agentscope.io to contribute. Please log in and try again.",
        "error"
      );
      return;
    }
  }
  let swalObj = {
    title: "Contribute Your Workflow to AgentScope",
    text: `You are about to perform the following actions:
            1. Create a new branch in your forked repository.
            2. Add your workflow file to this branch.
            3. Create a Pull Request (PR) from your branch to the AgentScope Gallery.

            These operations will allow you to share your workflow with the community on AgentScope.
            Please ensure that any API keys or sensitive information are not included in your submission.
            By proceeding, you grant permission for these actions to be executed.`,
    icon: "info",
    showCancelButton: true,
    confirmButtonText: "Yes, I'd like to contribute!",
    cancelButtonText: "No, maybe later"
  };
  let swalisConfirmedHtml = `
    <div style="text-align: left;">
      <label for="swal-input1">Title:</label>
      <input id="swal-input1" class="swal2-input" placeholder="Enter a descriptive title" value="${userLogin}'s workflow">

      <label for="swal-input2">Description:</label>
      <input id="swal-input2" class="swal2-input">

      <label for="swal-input3">Thumbnail URL (Optional):</label>
      <input id="swal-input3" class="swal2-input" placeholder="Enter a URL for the thumbnail">

      <label>Category:</label>
      <div id="category-buttons">
        <button type="button" class="category-button" data-value="tool">Tool</button>
        <button type="button" class="category-button" data-value="game">Game</button>
        <button type="button" class="category-button" data-value="simulation">Simulation</button>
        <button type="button" class="category-button" data-value="robotics">Robotics</button>
        <button type="button" class="category-button" data-value="social">Social</button>
        <button type="button" class="category-button" data-value="economic">Economic</button>
        <button type="button" class="category-button" data-value="educational">Educational</button>
        <button type="button" class="category-button" data-value="healthcare">Healthcare</button>
        <button type="button" class="category-button" data-value="security">Security</button>
        <button type="button" class="category-button" data-value="entertainment">Entertainment</button>
        <button type="button" class="category-button" data-value="manufacturing">Manufacturing</button>
        <button type="button" class="category-button" data-value="communication">Communication</button>
        <button type="button" class="category-button" data-value="logistics">Logistics</button>
        <button type="button" class="category-button" data-value="others">Others</button>
      </div>

      </div>
  `;
  let swalisConfirmedTitle = "Fill the Form to Create PR";
  if(getCookie("locale") == "zh"){
    swalObj = {
      title: "将您的工作流程贡献给 AgentScope",
      text: `您即将执行以下操作：
              1.在您的分叉仓库中创建一个新分支。
              2.将您的工作流程文件添加到此分支。
              3.从您的分支创建一个 Pull Request（PR）到 AgentScope Gallery。
              这些操作将允许您与 AgentScope 上的社区分享您的工作流程。
              请确保您的提交中不包含任何 API 密钥或敏感信息。
              继续操作即表示您授予执行这些操作的权限。`,
      icon: "info",
      showCancelButton: true,
      confirmButtonText: "是的，我想贡献！",
      cancelButtonText: "不，也许以后再说。"
    };
    swalisConfirmedTitle = "填写表单以创建 PR（Pull Request）";
    swalisConfirmedHtml =  `
    <div style="text-align: left;">
      <label for="swal-input1">标题:</label>
      <input id="swal-input1" class="swal2-input" placeholder="输入一个描述性标题。" value="${userLogin}'s workflow">

      <label for="swal-input2">描述:</label>
      <input id="swal-input2" class="swal2-input">

      <label for="swal-input3">缩略图网址（可选）:</label>
      <input id="swal-input3" class="swal2-input" placeholder="输入缩略图的网址">

      <label>类别:</label>
      <div id="category-buttons">
        <button type="button" class="category-button" data-value="tool">工具</button>
        <button type="button" class="category-button" data-value="game">游戏</button>
        <button type="button" class="category-button" data-value="simulation">模拟</button>
        <button type="button" class="category-button" data-value="robotics">机器人技术</button>
        <button type="button" class="category-button" data-value="social">社交</button>
        <button type="button" class="category-button" data-value="economic">经济</button>
        <button type="button" class="category-button" data-value="educational">教育</button>
        <button type="button" class="category-button" data-value="healthcare">医疗保健</button>
        <button type="button" class="category-button" data-value="security">安全</button>
        <button type="button" class="category-button" data-value="entertainment">娱乐</button>
        <button type="button" class="category-button" data-value="manufacturing">制造业</button>
        <button type="button" class="category-button" data-value="communication">通信</button>
        <button type="button" class="category-button" data-value="logistics">运筹</button>
        <button type="button" class="category-button" data-value="others">其他</button>
      </div>

      </div>
  `;
  }

  swal.fire(swalObj).then(async (result) => {
    if (result.isConfirmed) {
      const {value: formValues} = await Swal.fire({
        title: swalisConfirmedTitle,
        html: swalisConfirmedHtml,
        focusConfirm: false,
        showCancelButton: true,
        preConfirm: () => {
          const selectedCategories = Array.from(document.querySelectorAll(".category-button.selected"))
            .map(button => button.getAttribute("data-value"));
          return {
            title: document.getElementById("swal-input1").value,
            author: userLogin,
            description: document.getElementById("swal-input2").value,
            category: selectedCategories,
            thumbnail: document.getElementById("swal-input3").value
          };
        },
        didOpen: () => {
          const buttons = document.querySelectorAll(".category-button");
          buttons.forEach(button => {
            button.addEventListener("click", () => {
              button.classList.toggle("selected");
            });
          });
        }
      });

      if (formValues) {
        try {
          const rawData = editor.export();
          const hasError = sortElementsByPosition(rawData);
          if (hasError) {
            return;
          }
          const filteredData = reorganizeAndFilterConfigForAgentScope(rawData);
          filterOutApiKey(filteredData);

          const response = await fetch("/create-gallery-pr", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              meta: formValues,
              data: JSON.stringify(filteredData, null, 4),
            })
          });

          if (response.ok) {
            if(getCookie("locale") == "zh"){
              swal.fire("Success",
                "谢谢！您的工作流程已提交至图库。我们的维护人员会对其进行审核，一旦获得批准，您将被认可为我们主页上的 AgentScope 开发者！",
                "success");
            } else{
              swal.fire("Success",
                "Thank you! Your workflow has been submitted to the gallery. It will be reviewed by our maintainers and, once approved, you'll be recognized as an AgentScope developer on our homepage!",
                "success");
            }
          } else {
            if(getCookie("locale") == "zh"){
              swal.fire("Error", "提交您的工作流程时出现错误。请稍后再试。", "error");
            }else {
              swal.fire("Error", "There was an error while submitting your workflow. Please try again later.", "error");
            }
          }
        } catch (error) {
          if(getCookie("locale") == "zh"){
            swal.fire("Error", "提交您的工作流程时出现错误。请稍后再试。", "error");
          } else {
            swal.fire("Error", "There was an error while submitting your workflow. Please try again later.", "error");
          }
        }
      }
    }
  });
}

function isValidDataStructure(data) {
  if (
    data.hasOwnProperty("drawflow") &&
        data.drawflow.hasOwnProperty("Home") &&
        data.drawflow.Home.hasOwnProperty("data")
  ) {

    for (const nodeId in data.drawflow.Home.data) {
      const node = data.drawflow.Home.data[nodeId];

      if (
        !node.hasOwnProperty("id") ||
                typeof node.id !== "number" ||
                !node.hasOwnProperty("name") ||
                typeof node.name !== "string" ||
                !node.hasOwnProperty("class") ||
                typeof node.class !== "string"
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
    title: "Import Workflow Data",
    html:
            "<p>Please paste your HTML data below. Ensure that the source of the HTML data is trusted, as importing HTML from unknown or untrusted sources may pose security risks.</p>",
    input: "textarea",
    inputLabel: "Paste your HTML data here:",
    inputPlaceholder:
            "Paste your HTML data generated from `Export HTML` button...",
    inputAttributes: {
      "aria-label": "Paste your HTML data here",
      "class": "code"
    },
    customClass: {
      input: "code"
    },
    showCancelButton: true,
    confirmButtonText: "Import",
    cancelButtonText: "Cancel",
    inputValidator: (value) => {
      if (!value) {
        return "You need to paste code generated from `Export HTML` button!";
      }
      try {
        const parsedData = JSON.parse(value);
        if (isValidDataStructure(parsedData)) {

        } else {
          return "The data is invalid. Please check your data and try again.";
        }
      } catch (e) {
        return "Invalid data! You need to paste code generated from `Export HTML` button!";
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
            Swal.fire("Imported!", "", "success")
              .then(() => {
                setTimeout(() => {
                  updateImportNodes();
                }, 200);
              });
            ;
          });

      } catch (error) {
        Swal.showValidationMessage(`Import error: ${error}`);
      }
    }
  });
}


function showSaveWorkflowPopup() {
  Swal.fire({
    title: "Save Workflow",
    input: "text",
    inputPlaceholder: "Enter filename",
    showCancelButton: true,
    confirmButtonText: "Save",
    cancelButtonText: "Cancel"
  }).then(result => {
    if (result.isConfirmed) {
      const filename = result.value;
      saveWorkflow(filename);
    }
  });
}

function saveWorkflow(fileName) {
  const rawData = editor.export();
  const currentZoom = editor.zoom;
  filterOutApiKey(rawData);
  Object.keys(rawData.drawflow.Home.data).forEach((nodeId) => {
    const nodeElement = document.getElementById(`node-${nodeId}`);
    const nodeData = rawData.drawflow.Home.data[nodeId];
    if (nodeElement) {
      const rect = nodeElement.getBoundingClientRect();
      nodeData.width = (rect.width / currentZoom) + "px";
      nodeData.height = (rect.height / currentZoom) + "px";
    }
  });

  rawData.zoomLevel = currentZoom;
  removeHtmlFromUsers(rawData);
  const exportData = JSON.stringify(rawData, null, 4);
  fetch("/save-workflow", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      filename: fileName,
      workflow: exportData,
      overwrite: false,
    })
  }).then(response => response.json())
    .then(data => {
      if (data.message === "Workflow file saved successfully") {
        Swal.fire("Success", data.message, "success");
      } else {
        Swal.fire("Error", data.message || "An error occurred while saving the workflow.", "error");
      }
    })
    .catch(error => {
      console.error("Error:", error);
      Swal.fire("Error", "An error occurred while saving the workflow.", "error");
    });
}

function showLoadWorkflowPopup() {
  fetch("/list-workflows", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({})
  })
    .then(response => response.json())
    .then(data => {
      if (!Array.isArray(data.files)) {
        throw new TypeError("The return data is not an array");
      }
      const inputOptions = data.files.reduce((options, file) => {
        options[file] = file;
        return options;
      }, {});
      Swal.fire({
        title: "Loading Workflow from Disks",
        input: "select",
        inputOptions: inputOptions,
        inputPlaceholder: "Select",
        showCancelButton: true,
        showDenyButton: true,
        confirmButtonText: "Load",
        cancelButtonText: "Cancel",
        denyButtonText: "Delete",
        didOpen: () => {
          const selectElement = Swal.getInput();
          selectElement.addEventListener("change", (event) => {
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
            icon: "warning",
            showCancelButton: true,
            confirmButtonColor: "#d33",
            cancelButtonColor: "#3085d6",
            confirmButtonText: "Delete",
            cancelButtonText: "Cancel"
          }).then((deleteResult) => {
            if (deleteResult.isConfirmed) {
              deleteWorkflow(selectedFilename);
            }
          });
        }
      });
    })
    .catch(error => {
      console.error("Error:", error);
      Swal.fire("Error", "An error occurred while loading the workflow.", "error");
    });
}


function loadWorkflow(fileName) {
  fetch("/load-workflow", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      filename: fileName,
    })
  })
    .then(response => response.json())
    .then(data => {
      if (data.error) {
        Swal.fire("Error", data.error, "error");
      } else {
        try {
          editor.zoom = data.zoomLevel || 1;
          adjustZoom();

          addHtmlAndReplacePlaceHolderBeforeImport(data)
            .then(() => {
              editor.clear();
              editor.import(data);
              importSetupNodes(data);

              Object.keys(data.drawflow.Home.data).forEach((nodeId) => {
                const nodeElement = document.getElementById(`node-${nodeId}`);
                const nodeData = data.drawflow.Home.data[nodeId];
                if (nodeData.width && nodeElement) {
                  nodeElement.style.width = nodeData.width;
                }
              });

              Swal.fire({
                title: "Imported!",
                icon: "success",
                showConfirmButton: true
              }).then((result) => {
                if (result.isConfirmed) {
                  showEditorTab();
                }
              });
              setTimeout(() => {
                updateImportNodes();
              }, 200);
            });
        } catch (error) {
          Swal.showValidationMessage(`Import error: ${error}`);
        }
      }
    });
}


function adjustZoom() {
  editor.precanvas.style.transform = `scale(${editor.zoom})`;
  editor.zoom_refresh();
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
  const htmlSourceCode = await fetchHtml(nameToHtmlFile[name]);
  htmlCache[name] = htmlSourceCode;
  return htmlSourceCode;
}


async function addHtmlAndReplacePlaceHolderBeforeImport(data) {
  const idPlaceholderRegex = /ID_PLACEHOLDER/g;
  const namePlaceholderRegex = /NAME_PLACEHOLDER/g;
  const readmePlaceholderRegex = /README_PLACEHOLDER/g;
  const boxDivRegex = /<div class="box"(.*?)>/;
  allimportNodeId = [];

  const classToReadmeDescription = {
    "node-DialogAgent": "A dialog agent that can interact with users or other agents",
    "node-UserAgent": "A proxy agent for user",
    "node-DictDialogAgent": "Agent that generates response in a dict format",
    "node-ReActAgent": "Agent for ReAct (reasoning and acting) with tools",
    "node-BroadcastAgent": "A broadcast agent that only broadcasts the messages it receives"
  };

  for (const nodeId of Object.keys(data.drawflow.Home.data)) {
    const node = data.drawflow.Home.data[nodeId];
    if (!node.html) {
      if (node.name === "readme") {
        delete data.drawflow.Home.data[nodeId];
        continue;
      }

      allimportNodeId.push(nodeId);
      node.html = await fetchHtmlSourceCodeByName(node.name);

      if (node.name === "CopyNode") {
        node.html = node.html.replace(idPlaceholderRegex, node.data.elements[0]);
        node.html = node.html.replace(namePlaceholderRegex, node.class.split("-").slice(-1)[0]);

        const readmeDescription = classToReadmeDescription[node.class];
        if (readmeDescription) {
          node.html = node.html.replace(readmePlaceholderRegex, readmeDescription);
        }
      } else {
        node.html = node.html.replace(idPlaceholderRegex, nodeId);
      }
      //TODO: fix height and width
      // Adjust the height of the box div
      let styleString = "";
      if (node.width) {
        const originalWidth = parseInt(node.width, 10);
        if (!isNaN(originalWidth)) {
          const adjustedWidth = originalWidth - 31; // Consistently applying width reduction
          styleString += `width: ${adjustedWidth}px; `;
        }
      }
      if (node.height) {
        const originalHeight = parseInt(node.height, 10);
        if (!isNaN(originalHeight)) {
          const adjustedHeight = originalHeight - 91; // Consistently applying height reduction
          styleString += `height: ${adjustedHeight}px; `;
        }
      }
      if (styleString !== "") {
        node.html = node.html.replace(boxDivRegex, `<div class="box" style="${styleString}"$1>`);
      }
    }
  }
}


function updateImportNodes() {
  allimportNodeId.forEach((nodeId) => {
    editor.updateConnectionNodes(`node-${nodeId}`);
  });
}

function importSetupNodes(dataToImport) {
  imporTempData = dataToImport;
  Object.entries(dataToImport.drawflow.Home.data).forEach(([nodeId, nodeValue]) => {
    disableButtons();
    makeNodeTop(nodeId);
    setupNodeCopyListens(nodeId);
    addEventListenersToNumberInputs(nodeId);
    setupTextInputListeners(nodeId);
    setupNodeServiceDrawer(nodeId);
    reloadi18n();
    setupNodeListeners(nodeId);
    const nodeElement = document.getElementById(`node-${nodeId}`);
    if (nodeElement) {
      const nodeData = dataToImport.drawflow.Home.data[nodeId];
      if (nodeData.width) {
        const originalWidth = parseInt(nodeData.width, 10);
        if (!isNaN(originalWidth)) {
          const adjustedWidth = originalWidth - 31;
          nodeElement.style.width = `${adjustedWidth}px`;
        }
      }
      if (nodeData.height) {
        const originalHeight = parseInt(nodeData.height, 10);
        if (!isNaN(originalHeight)) {
          const adjustedHeight = originalHeight - 31;
          nodeElement.style.height = `${adjustedHeight}px`;
        }
      }
      const copyButton = nodeElement.querySelector(".copy-button");
      if (copyButton) {
        setupNodeCopyListens(nodeId);
      }
    }
    if (nodeValue.name === "ReActAgent") {
      nodeValue.data.elements.forEach((listNode) => {
        dropNodeToDropzone(listNode, nodeElement);
      });
    }
  });
}


function copyToClipboard(contentToCopy) {
  const tempTextarea = document.createElement("textarea");
  tempTextarea.value = contentToCopy;
  document.body.appendChild(tempTextarea);
  tempTextarea.select();
  tempTextarea.setSelectionRange(0, 99999);

  try {
    const successful = document.execCommand("copy");
    if (successful) {
      Swal.fire("Copied!", "", "success");
    } else {
      Swal.fire("Failed to copy", "", "error");
    }
  } catch (err) {
    Swal.fire("Failed to copy", "", "error");
  }
  document.body.removeChild(tempTextarea);
}


function fetchExample(index, processData) {
  fetch("/read-examples", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      data: index,
      // lang: getCookie('locale') || 'en',
      lang: "en",
    })
  }).then(response => {
    if (!response.ok) {
      throw new Error("Network error.");
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
            const copyButton = nodeElement.querySelector(".button.copy-button");
            if (copyButton) {
              setupNodeCopyListens(nodeId);
            }
          }
        });
        reloadi18n();
      });
  });
}


function importExample_step(index) {
  if (!localStorage.getItem("firstGuide")) {
    localStorage.setItem("firstGuide", "true");
    skipGuide();
  }
  fetchExample(index, data => {
    const dataToImportStep = data.json;
    addHtmlAndReplacePlaceHolderBeforeImport(dataToImportStep).then(() => {
      clearModuleSelected();
      descriptionStep = ["Readme", "Model", "UserAgent",
        "DialogAgent"];
      initializeImport(dataToImportStep);
    });
  });
}


function updateImportButtons() {
  document.getElementById("import-prev").disabled = currentImportIndex
        <= 1;
  document.getElementById("import-next").disabled = currentImportIndex >= importQueue.length;
  document.getElementById("import-skip").disabled = currentImportIndex >= importQueue.length;
  reloadi18n();
}


function createElement(tag, id, html = "", parent = document.body) {
  const element = document.getElementById(id) || document.createElement(tag);
  element.id = id;
  element.innerHTML = html;
  if (!element.parentNode) {
    parent.appendChild(element);
  }
  return element;
}


function initializeImport(data) {
  ["menu-btn", "menu-btn-svg"].forEach(cls => {
    const containers = document.getElementsByClassName(cls);
    Array.from(containers).forEach(container => container.style.display = "none");
  });

  createElement("div", "left-sidebar-blur", "", document.body).style.cssText = `
            position: fixed; top: 60px; left: 0; bottom: 0; width: 250px;
            background: rgba(128, 128, 128, 0.7);
            filter: blur(2px); z-index: 1000; cursor: not-allowed;
        `;

  createElement("div", "import-buttons", "", document.body);

  dataToImportStep = data;
  importQueue = Object.keys(dataToImportStep.drawflow.Home.data);

  const importButtonsDiv = document.getElementById("import-buttons");

  createElement("div", "step-info", "", importButtonsDiv);
  createElement("button", "import-prev",
    "<i class=\"fas fa-arrow-left\"></i> <span i18n=\"workstarionjs-import-prev\">Previous</span>",
    importButtonsDiv).onclick = importPreviousComponent;
  createElement("button", "import-next",
    "<i class=\"fas fa-arrow-right\"></i> <span i18n=\"workstarionjs-import-next\">Next</span>",
    importButtonsDiv).onclick = importNextComponent;
  createElement("button", "import-skip",
    "<i class=\"fas fa-forward\"></i> <span i18n=\"workstarionjs-import-skip\">Skip</span>",
    importButtonsDiv).onclick = importSkipComponent;
  createElement("button", "import-quit",
    "<i class=\"fas fa-sign-out-alt\"></i> <span i18n=\"workstarionjs-import-quit\">Quit</span>",
    importButtonsDiv).onclick = importQuitComponent;
  createElement("div", "step-warning",
    "<span i18n=\"workstarionjs-import-caution\">Caution: You are currently in the tutorial mode where modifications are restricted.</span><br><span i18n=\"workstarionjs-import-Caution-click\">Please click</span> <strong i18n=\"workstarionjs-import-Caution-quit\">Quit</strong> <span  i18n=\"workstarionjs-import-Caution-exit\"> to exit and start creating your custom multi-agent applications. </span>", document.body);

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
  ["menu-btn", "menu-btn-svg"].forEach(cls => {
    const containers = document.getElementsByClassName(cls);
    Array.from(containers).forEach(container => container.style.display = "");
  });
}


function updateStepInfo() {
  const stepInfoDiv = document.getElementById("step-info");
  if (stepInfoDiv && currentImportIndex > 0) {
    stepInfoDiv.innerHTML =
            `Current Step (${currentImportIndex}/${importQueue.length}) <br> ${descriptionStep[currentImportIndex - 1]}`;
  } else if (stepInfoDiv) {
    stepInfoDiv.innerHTML = "No steps to display.";
  }
}


function clearModuleSelected() {
  editor.clearModuleSelected();

  const importButtonsDiv = document.getElementById("import-buttons");
  if (importButtonsDiv) {
    importButtonsDiv.remove();
  }

  const stepWarningDiv = document.getElementById("step-warning");
  if (stepWarningDiv) {
    stepWarningDiv.remove();
  }

  const blurDiv = document.getElementById("left-sidebar-blur");
  if (blurDiv) {
    blurDiv.remove();
  }
}


function getCookie(name) {
  const matches = document.cookie.match(new RegExp(
    "(?:^|; )" + name.replace(/([\.$?*|{}\(\)\[\]\\\/\+^])/g, "\\$1") + "=([^;]*)"
  ));
  return matches ? decodeURIComponent(matches[1]) : undefined;
}


function showSurveyModal() {
  document.getElementById("surveyModal").style.display = "block";
}


function hideSurveyModal() {
  document.getElementById("surveyModal").style.display = "none";
}

function reloadi18n() {
  const currentLang = getCookie("locale") || "en";
  $("[i18n]").i18n({
    defaultLang: currentLang,
    filePath: "../static/i18n/",
    filePrefix: "i18n_",
    fileSuffix: "",
    forever: true,
    callback: function () {
    }
  });
}

window.addEventListener("storage", function (event) {
  if (event.key === "locale") {
    reloadi18n();
  }
}, false);

function startGuide() {
  const targetElement = document.querySelector(".guide-Example");
  const element = document.querySelector(".tour-guide");
  positionElementRightOf(element, targetElement);
}

function getElementCoordinates(targetElement) {
  const style = window.getComputedStyle(targetElement);
  const rect = targetElement.getBoundingClientRect();
  return {
    left: rect.left + (parseFloat(style.left) || 0),
    top: rect.top + (parseFloat(style.top) || 0),
    right: rect.right + (parseFloat(style.top) || 0),
    bottom: rect.bottom + (parseFloat(style.top) || 0),
    width: rect.width,
    height: rect.height,
    x: rect.x,
    y: rect.y,
  };
}

function positionElementRightOf(element, targetElement) {
  const targetCoordinates = getElementCoordinates(targetElement);
  const mask = document.querySelector(".overlay");
  mask.style.display = "block";
  element.style.position = "absolute";
  element.style.display = "block";
  element.style.left = `${targetCoordinates.x + targetCoordinates.right}px`;
  element.style.top = `${targetCoordinates.y}px`;
}

function skipGuide() {
  const element = document.querySelector(".tour-guide");
  const mask = document.querySelector(".overlay");
  localStorage.setItem("firstGuide", "true");
  if (element) {
    element.style.display = "none";
    element.remove();
    mask.style.display = "none";
    mask.remove();
  }
}

class Notification {
  static initStatics() {
    this.count = 0;
    this.instances = [];
  }

  static clearInstances() {
    Notification.count = 0;
    Notification.instances = [];
  }

  constructor(props) {
    Notification.count += 1;
    Notification.instances.push(this);
    this.currentIndex = Notification.count;
    this.position = "bottom-right";
    this.title = "Notification Title";
    this.content = "Notification Content";
    this.element = null;
    this.closeBtn = true;
    this.progress = false;
    this.intervalTime = 3000;
    this.confirmBtn = false;
    this.cancelBtn = false;
    this.pause = true;
    this.reduceNumber = 0;

    // 绑定 this
    this.destroyAll = this.destroyAll.bind(this);
    this.onCancelCallback = this.onCancelCallback.bind(this);
    this.onConfirmCallback = this.onConfirmCallback.bind(this);

    this.init(props);
  }

  init(props) {
    this.setDefaultValues(props);
    this.element = document.createElement("div");
    this.element.className = "notification";
    this.title && this.renderTitle(getCookie("locale") == "zh" ? props.i18nTitle : this.title);
    this.closeBtn && this.renderCloseButton();
    this.content && this.renderContent(getCookie("locale") == "zh" ? props.i18nContent : this.content);
    (this.confirmBtn || this.cancelBtn) && this.renderClickButton();
    this.progress && this.renderProgressBar();
    this.setPosition(this.position);
    document.body.appendChild(this.element);
    setTimeout(() => {
      this.show();
    }, 10);
  }

  isHTMLString(string) {
    const doc = new DOMParser().parseFromString(string, "text/html");
    return Array.from(doc.body.childNodes).some(node => node.nodeType === 1);
  }

  renderCloseButton() {
    this.closeBtn = document.createElement("span");
    this.closeBtn.className = "notification-close";
    this.closeBtn.innerText = "X";
    this.closeBtn.onclick = this.destroyAll;
    this.title.appendChild(this.closeBtn);
  }

  renderTitle(component) {
    if (this.isHTMLString(component)) {
      this.title = document.createElement("div");
      this.title.className = "notification-title";
      this.title.innerHTML = component;
    } else {
      this.title = document.createElement("div");
      this.titleText = document.createElement("div");
      this.title.className = "notification-title";
      this.titleText.className = "notification-titleText";
      this.titleText.innerText = component;
      this.title.appendChild(this.titleText);
    }
    this.element.appendChild(this.title);
  }

  renderContent(component) {
    if (this.isHTMLString(component)) {
      this.content = document.createElement("div");
      this.content.className = "notification-content";
      this.content.innerHTML = component;
    } else {
      this.content = document.createElement("div");
      this.content.className = "notification-content";
      this.content.innerText = component;
    }
    this.element.appendChild(this.content);
  }

  renderClickButton() {
    if (this.confirmBtn || this.cancelBtn) {
      this.clickBottonBox = document.createElement("div");
      this.clickBottonBox.className = "notification-clickBotton-box";
    }
    if (this.confirmBtn) {
      this.confirmBotton = document.createElement("button");
      this.confirmBotton.className = "notification-btn confirmBotton";
      this.confirmBotton.innerText = getCookie("locale") == "zh" ? this.i18nConfirmBtn : this.confirmBtn;
      this.confirmBotton.onclick = this.onConfirmCallback;
      this.clickBottonBox.appendChild(this.confirmBotton);
    }
    if (this.cancelBtn) {
      this.cancelBotton = document.createElement("button");
      this.cancelBotton.className = "notification-btn cancelBotton";
      this.cancelBotton.innerText = getCookie("locale") == "zh" ? this.i18nCancelBtn : this.cancelBtn;
      this.cancelBotton.onclick = this.onCancelCallback;
      this.clickBottonBox.appendChild(this.cancelBotton);
    }
    this.element.appendChild(this.clickBottonBox);
  }

  renderProgressBar() {
    this.progressBar = document.createElement("div");
    this.progressBar.className = "notification-progress";
    this.element.appendChild(this.progressBar);
  }

  stepProgressBar(callback) {
    const startTime = performance.now();
    const step = (timestamp) => {
      const progress = Math.min((timestamp + this.reduceNumber - startTime) / this.intervalTime, 1);
      this.progressBar.style.width = (1 - progress) * 100 + "%";
      if (progress < 1 && this.pause === false) {
        requestAnimationFrame(step);
      } else {
        this.reduceNumber = timestamp + this.reduceNumber - startTime;
      }
      if (progress === 1) {
        this.pause = true;
        this.reduceNumber = 0;
        callback();
        this.removeChild();
      }
    };
    requestAnimationFrame(step);
  }

  setDefaultValues(props) {
    for (const key in props) {
      if (props[key] !== undefined) {
        this[key] = props[key];
      }
    }
  }

  setPosition() {
    switch (this.position) {
    case "top-left":
      this.element.style.top = "25px";
      this.element.style.left = "-100%";
      break;
    case "top-right":
      this.element.style.top = "25px";
      this.element.style.right = "-100%";
      break;
    case "bottom-right":
      this.element.style.bottom = "25px";
      this.element.style.right = "-100%";
      break;
    case "bottom-left":
      this.element.style.bottom = "25px";
      this.element.style.left = "-100%";
      break;
    }
  }

  show() {
    this.element.style.display = "flex";
    switch (this.position) {
    case "top-left":
      this.element.style.top = "25px";
      this.element.style.left = "25px";
      break;
    case "top-right":
      this.element.style.top = "25px";
      this.element.style.right = "25px";
      break;
    case "bottom-right":
      this.element.style.bottom = "25px";
      this.element.style.right = "25px";
      break;
    case "bottom-left":
      this.element.style.bottom = "25px";
      this.element.style.left = "25px";
      break;
    }
  }

  destroyAll() {
    for (const instance of Notification.instances) {
      document.body.removeChild(instance.element);
    }
    Notification.clearInstances();
  }

  removeChild() {
    let removeIndex;
    for (let i = 0; i < Notification.instances.length; i++) {
      if (Notification.instances[i].currentIndex === this.currentIndex) {
        removeIndex = i;
        break;
      }
    }
    if (removeIndex !== undefined) {
      Notification.instances.splice(removeIndex, 1);
    }
    this.element.remove();
  }

  addCloseListener() {
    this.closeBtn.addEventListener("click", () => {
      this.removeChild();
    });
  }

  onCancelCallback() {
    if (typeof this.onCancel === "function") {
      this.onCancel();
      this.removeChild();
    }
  }

  onConfirmCallback() {
    if (typeof this.onConfirm === "function") {
      this.pause = !this.pause;
      if (!this.pause) {
        this.stepProgressBar(this.onConfirm);
        this.confirmBotton.innerText = getCookie("locale") === "zh" ? "暂停" : "pause";
      } else {
        this.confirmBotton.innerText = this.confirmBtn;
      }
    }
  }
}

// 初始化静态属性
Notification.initStatics();

function createNotification(props) {
  new Notification(props);
}

function setCookie(name, value, days) {
  let expires = "";
  if (days) {
    const date = new Date();
    date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
    expires = "; expires=" + date.toUTCString();
  }
  document.cookie = name + "=" + (value || "") + expires + "; path=/";
}

document.addEventListener("DOMContentLoaded", function () {
  showTab("tab1");
});


function loadWorkLocalflow(fileName) {
  fetch("/load-workflow", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      filename: fileName,
    })
  })
    .then(response => response.json())
    .then(data => {
      if (data.error) {
        Swal.fire("Error", data.error, "error");
      } else {
        try {
          addHtmlAndReplacePlaceHolderBeforeImport(data)
            .then(() => {
              editor.clear();
              editor.import(data);
              importSetupNodes(data);
              Swal.fire("Imported!", "", "success").then((result) => {
                if (result.isConfirmed) {
                  showEditorTab();
                }
                setTimeout(() => {
                  updateImportNodes();
                }, 200);
              });
            });
        } catch (error) {
          Swal.showValidationMessage(`Import error: ${error}`);
        }
        Swal.fire("Success", "Workflow loaded successfully", "success");
      }
    })
    .catch(error => {
      console.error("Error:", error);
      Swal.fire("Error", "An error occurred while loading the workflow.", "error");
    });
}


function showEditorTab() {
  document.getElementById("col-right").style.display = "block";
  document.getElementById("col-right2").style.display = "none";
  console.log("Show Editor");
}

function importGalleryWorkflow(data) {
  try {
    const parsedData = JSON.parse(data);
    addHtmlAndReplacePlaceHolderBeforeImport(parsedData)
      .then(() => {
        editor.clear();
        editor.import(parsedData);
        importSetupNodes(parsedData);
        Swal.fire({
          title: "Imported!",
          icon: "success",
          showConfirmButton: true
        }).then((result) => {
          if (result.isConfirmed) {
            showEditorTab();
          }
          setTimeout(() => {
            updateImportNodes();
          }, 200);
        });
      });
  } catch (error) {
    Swal.showValidationMessage(`Import error: ${error}`);
  }
}

function deleteWorkflow(fileName) {
  Swal.fire({
    title: "Are you sure?",
    text: "Workflow will be deleted!",
    icon: "warning",
    showCancelButton: true,
    confirmButtonColor: "#3085d6",
    cancelButtonColor: "#d33",
    confirmButtonText: "Yes, delete it!"
  }).then((result) => {
    if (result.isConfirmed) {
      fetch("/delete-workflow", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          filename: fileName,
        })
      }).then(response => response.json())
        .then(data => {
          if (data.error) {
            Swal.fire("Error", data.error, "error");
          } else {
            showLoadWorkflowList("tab2");
            Swal.fire("Deleted!", "Your workflow has been deleted.", "success");
          }
        })
        .catch(error => {
          console.error("Error:", error);
          Swal.fire("Error", "Delete workflow error.", "error");
        });
    }
  });
}


function showTab(tabId) {
  const tabs = document.getElementsByClassName("tab");
  for (let i = 0; i < tabs.length; i++) {
    tabs[i].classList.remove("active");
    tabs[i].style.display = "none";
  }
  const tab = document.getElementById(tabId);
  if (tab) {
    tab.classList.add("active");
    tab.style.display = "block";

    const tabButtons = document.getElementsByClassName("tab-button");
    for (let j = 0; j < tabButtons.length; j++) {
      tabButtons[j].classList.remove("active");
    }
    const activeTabButton = document.querySelector(`.tab-button[onclick*="${tabId}"]`);
    if (activeTabButton) {
      activeTabButton.classList.add("active");
    }

    if (tabId === "tab2") {
      showLoadWorkflowList(tabId);
    } else if (tabId === "tab1") {
      showGalleryWorkflowList(tabId);
    }
  }
}

let galleryWorkflows = [];

function showGalleryWorkflowList(tabId) {
  const container = document.getElementById(tabId).querySelector(".grid-container");
  container.innerHTML = "";
  fetch("/fetch-gallery", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({})
  })
    .then(response => response.json())
    .then(data => {
      galleryWorkflows = data.json || [];
      galleryWorkflows.forEach((workflow, index) => {
        const meta = workflow.meta;
        const title = meta.title;
        const author = meta.author;
        const time = meta.time;
        const thumbnail = meta.thumbnail || generateThumbnailFromContent(meta);
        createGridItem(title, container, thumbnail, author, time, false, index);
      });
    })
    .catch(error => {
      console.error("Error fetching gallery workflows:", error);
    });
}

function createGridItem(workflowName, container, thumbnail, author = "", time = "", showDeleteButton = false, index) {
  var gridItem = document.createElement("div");
  gridItem.className = "grid-item";
  gridItem.style.borderRadius = "15px";
  var gridItem = document.createElement("div");
  gridItem.className = "grid-item";
  gridItem.style.borderRadius = "15px";
  gridItem.style.boxShadow = "0 4px 8px rgba(0, 0, 0, 0.2)";

  const img = document.createElement("div");
  img.className = "thumbnail";
  img.style.backgroundImage = `url('${thumbnail}')`;
  img.style.backgroundSize = "cover";
  img.style.backgroundPosition = "center";
  gridItem.appendChild(img);

  const caption = document.createElement("div");
  caption.className = "caption";
  caption.style.backgroundColor = "white";

  const h6 = document.createElement("h6");
  h6.textContent = workflowName;
  h6.style.margin = "1px 0";

  const pAuthor = document.createElement("p");
  pAuthor.textContent = `Author: ${author}`;
  pAuthor.style.margin = "1px 0";
  pAuthor.style.fontSize = "10px";

  const pTime = document.createElement("p");
  pTime.textContent = `Date: ${time}`;
  pTime.style.margin = "1px 0";
  pTime.style.fontSize = "10px";

  const button = document.createElement("button");
  button.textContent = " Load ";
  button.className = "button";
  button.style.backgroundColor = "#007aff";
  button.style.color = "white";
  button.style.padding = "2px 7px";
  button.style.border = "none";
  button.style.borderRadius = "8px";
  button.style.fontSize = "12px";
  button.style.cursor = "pointer";
  button.style.transition = "background 0.3s";

  button.addEventListener("mouseover", function () {
    button.style.backgroundColor = "#005bb5";
  });

  button.addEventListener("mouseout", function () {
    button.style.backgroundColor = "#007aff";
  });
  button.onclick = function (e) {
    e.preventDefault();
    if (showDeleteButton) {
      loadWorkflow(workflowName);
      showEditorTab();
    } else {
      const workflowData = galleryWorkflows[index];
      importGalleryWorkflow(JSON.stringify(workflowData));
    }
  };

  caption.appendChild(h6);
  if (author) {
    caption.appendChild(pAuthor);
  }
  if (time) {
    caption.appendChild(pTime);
  }
  caption.appendChild(button);

  if (showDeleteButton) {
    const deleteButton = document.createElement("button");
    deleteButton.textContent = "Delete";
    deleteButton.className = "button";
    deleteButton.style.backgroundColor = "#007aff";
    deleteButton.style.color = "white";
    deleteButton.style.padding = "2px 3px";
    deleteButton.style.border = "none";
    deleteButton.style.borderRadius = "8px";
    deleteButton.style.fontSize = "12px";
    deleteButton.style.cursor = "pointer";
    deleteButton.style.transition = "background 0.3s";

    deleteButton.addEventListener("mouseover", function () {
      deleteButton.style.backgroundColor = "#005bb5";
    });
    deleteButton.addEventListener("mouseout", function () {
      deleteButton.style.backgroundColor = "#007aff";
    });

    deleteButton.onclick = function (e) {
      e.preventDefault();
      deleteWorkflow(workflowName);
    };

    caption.appendChild(deleteButton);
  }

  gridItem.appendChild(caption);
  container.appendChild(gridItem);
  console.log("Grid item appended:", gridItem);
}

function showLoadWorkflowList(tabId) {
  fetch("/list-workflows", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({})
  })
    .then(response => response.json())
    .then(data => {
      if (!Array.isArray(data.files)) {
        throw new TypeError("The return data is not an array");
      }
      const container = document.getElementById(tabId).querySelector(".grid-container");
      container.innerHTML = "";
      data.files.forEach(fileName => {
        const thumbnail = generateThumbnailFromContent({title: fileName});
        createGridItem(fileName, container, thumbnail, "", "", true);
      });
    })
    .catch(error => {
      console.error("Error fetching workflow list:", error);
      alert("Fetch workflow list error.");
    });
}


function generateThumbnailFromContent(content) {
  const canvas = document.createElement("canvas");
  canvas.width = 150;
  canvas.height = 150;
  const ctx = canvas.getContext("2d");

  ctx.fillStyle = "#f0f0f0";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  ctx.font = "italic bold 14px \"Helvetica Neue\", sans-serif";
  ctx.textAlign = "center";
  ctx.fillStyle = "#333";

  ctx.fillText(content.title, canvas.width / 2, canvas.height / 2 + 20);

  return canvas.toDataURL();
}

function setupNodeServiceDrawer(nodeId) {
  const newNode = document.getElementById(`node-${nodeId}`);
  const popDrawer = newNode.querySelector(".pop-drawer");
  if (popDrawer) {
    const contain = newNode.querySelector(".serivce-contain");
    const hiddenList = newNode.querySelector(".add-service-list");
    contain.addEventListener("mouseover", function () {
      hiddenList.style.display = "block";
    });
    hiddenList.addEventListener("mouseover", function () {
      hiddenList.style.display = "block";
    });
    contain.addEventListener("mouseout", function () {
      hiddenList.style.display = "none";
    });

    hiddenList.addEventListener("click", function (e) {
      const target = e.target;

      if (target.localName == "li") {
        // createServiceNode(nodeId,target.getAttribute("data-node"),newNode,e.currentTarget.offsetLeft + newNode.offsetWidth  ,e.currentTarget.offsetTop);
        createServiceNode(nodeId, target.getAttribute("data-node"));
      }
    });
  }
}

async function createServiceNode(nodeId, serivceName) {
  const nodeElement = document.getElementById(`node-${nodeId}`);
  const nodeElementRect = nodeElement.getBoundingClientRect();
  const node = editor.getNodeFromId(nodeId);


  const dropzoneRect = nodeElement.querySelector(".tools-placeholder").getBoundingClientRect();

  const createPos_x = Math.ceil(node.pos_x + (dropzoneRect.width * 2 / 3) / (editor.zoom));
  const createPos_y = Math.ceil(node.pos_y + (dropzoneRect.top - nodeElementRect.top) / editor.zoom + 20);

  const dropNodeInfo = editor.getNodeFromId(nodeId);
  const dropNodeInfoData = dropNodeInfo.data;
  const createdId = await selectReActAgent(serivceName, createPos_x, createPos_y);
  dropNodeInfoData.elements.push(`${createdId}`);
  editor.updateNodeDataFromId(nodeId, dropNodeInfoData);

  dropzoneDetection(createdId);
}

async function selectReActAgent(serivceName, pos_x, pos_y) {
  const htmlSourceCode = await fetchHtmlSourceCodeByName(serivceName);
  let createId;
  switch (serivceName) {
  case "BingSearchService":
    createId = editor.addNode("BingSearchService", 0, 0,
      pos_x, pos_y, "BingSearchService", {
        "args": {
          "api_key": "",
          "num_results": 3,
        }
      }, htmlSourceCode);
    break;

  case "GoogleSearchService":
    createId = editor.addNode("GoogleSearchService", 0, 0,
      pos_x, pos_y, "GoogleSearchService", {
        "args": {
          "api_key": "",
          "cse_id": "",
          "num_results": 3,
        }
      }, htmlSourceCode);
    break;

  case "PythonService":
    createId = editor.addNode("PythonService", 0, 0,
      pos_x, pos_y, "PythonService", {}, htmlSourceCode);
    break;

  case "ReadTextService":
    createId = editor.addNode("ReadTextService", 0, 0,
      pos_x, pos_y, "ReadTextService", {}, htmlSourceCode);
    break;

  case "WriteTextService":
    createId = editor.addNode("WriteTextService", 0, 0,
      pos_x, pos_y, "WriteTextService", {}, htmlSourceCode);
    break;

  case "TextToAudioService":
    const TextToAudioServiceID = editor.addNode("TextToAudioService", 0, 0,
      pos_x, pos_y, "TextToAudioService", {
        "args": {
          "model": "",
          "api_key": "",
          "sample_rate": ""
        }
      }, htmlSourceCode);
    createId = TextToAudioServiceID;
    updateSampleRate(TextToAudioServiceID);
    break;
  case "TextToImageService":
    createId = editor.addNode("TextToImageService", 0, 0,
      pos_x, pos_y, "TextToImageService", {
        "args": {
          "model": "",
          "api_key": "",
          "n": 1,
          "size": ""
        }
      }, htmlSourceCode);
    break;
  }
  return createId;
}

// Added for the dropzone
function dropzoneDetection(nodeId) {
  var node = editor.getNodeFromId(nodeId);
  const nodeElement = document.getElementById(`node-${nodeId}`);
  var dropzones = document.querySelectorAll(".dropzone");

  dropzones.forEach(function (dropzone) {
    // Prevent conflicts of drag-and-drop events between drawflow node and dropzone
    if (!dropzone.hasDropEventListeners) {
      dropzone.addEventListener("dragover", function (e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = "move";
      });

      dropzone.hasDropEventListeners = true;
    }

    // Check if the dropzone is not a child of the current node
    if (!nodeElement.contains(dropzone)) {
      if (
        isColliding(nodeElement, dropzone) &&
                node.name !== "dropzoneNode" &&
                !node.data.attachedToDropzone
      ) {
        console.log(
          `Collision detected: Node "${node.name}" (ID: ${nodeId}) collided with ${dropzone.id}`
        );
        dropNodeToDropzone(nodeId, dropzone);
      }
    }
  });
}

function isColliding(element1, element2) {
  var rect1 = element1.getBoundingClientRect();
  var rect2 = element2.getBoundingClientRect();

  return !(
    rect1.right < rect2.left ||
        rect1.left > rect2.right ||
        rect1.bottom < rect2.top ||
        rect1.top > rect2.bottom
  );
}

function dropNodeToDropzone(nodeId, dropzoneElement) {
  var node = editor.getNodeFromId(nodeId);
  var dropzoneNodeId = dropzoneElement
    .closest(".drawflow-node")
    .id.split("-")[1];

  if (nodeId === dropzoneNodeId) {
    console.log(`Prevented node ${nodeId} from being dropped into itself`);
    return;
  }
  var dropzoneNode = editor.getNodeFromId(dropzoneNodeId);
  var stackedList = dropzoneElement.querySelector(".stacked-list");

  if (!dropzoneNode.data.stackedItems) {
    dropzoneNode.data.stackedItems = [];
  }

  var nodeElement = document.getElementById(`node-${nodeId}`);
  var nodeRect = nodeElement.getBoundingClientRect();
  var startX = nodeRect.left;
  var startY = nodeRect.top;

  // Make sure the logic is the same
  nodeElement.classList.add("hidden-node");

  // Should be modified to display the header of the node
  var stackedItem = document.createElement("li");
  stackedItem.className = "stacked-item";
  stackedItem.id = `stacked-item-${nodeId}`;
  stackedItem.innerHTML = `
        <span>${node.name}</span>
        <div  class="stacked-item-actions">
            <button class="expand-btn" title="Expand"><i class="material-icons">open_in_full</i></button>
            <button class="remove-btn" title="Remove"><i class="material-icons">delete</i></button>
        </div>
    `;
  // Keep track of the dropzone Id it attached to
  stackedItem.dataset.attachedDropzoneId = dropzoneNodeId;
  stackedItem.draggable = true;
  stackedList.appendChild(stackedItem);

  // Try Sortable.js
  // Mainly for reordering the stacked items
  // Not necessary, but nice to have some animations
  new Sortable(stackedList, {
    group: "shared",
    animation: 150,
    filter: ".undraggable",
    onEnd: function (evt) {
      console.log("Item dropped");
    },
  });

  // Makesure the stackedList in dropzone is actually a sortableInstance
  stackedItem.addEventListener("mousedown", handleStackedItemMouseDown);
  stackedItem.addEventListener("dragstart", handleStackedItemDragStart);
  stackedItem.addEventListener("drag", handleStackedItemDrag);
  stackedItem.addEventListener("dragend", handleStackedItemDragEnd);

  stackedItem
    .querySelector(".remove-btn")
    .addEventListener("click", function () {
      removeNodeFromDropzone(node, dropzoneNode, stackedItem);
    });
  stackedItem
    .querySelector(".expand-btn")
    .addEventListener("click", function (e) {
      e.stopPropagation();
      expandNodeFromDropzone(node, dropzoneNode, stackedItem);
    });

  var itemRect = stackedItem.getBoundingClientRect();
  var endX = itemRect.left;
  var endY = itemRect.top;

  anime({
    targets: stackedItem,
    translateX: [startX - endX, 0],
    translateY: [startY - endY, 0],
    scale: [1.5, 1],
    opacity: [0, 1],
    duration: 800,
    easing: "easeOutElastic(1, .8)",
    complete: function () {
      stackedItem.style.transform = "none";
    },
  });

  if (node && node.data) {
    node.data.attachedToDropzone = true;
    node.data.attachedDropzoneId = dropzoneNodeId;
    console.log(`Node ${nodeId} attached to the dropzone ${dropzoneNodeId}`);
  }
  dropzoneNode.data.stackedItems.push({
    id: nodeId,
    name: node.name,
  });
  console.log(
    `Node ${nodeId} (${node.name}) added to the stackedItems in the dropzone ${dropzoneNodeId}`
  );
  stackedItem
    .querySelector(".expand-btn").click();
}

function handleStackedItemMouseDown(e) {
  console.log("Mouse down");
  e.stopPropagation();
}

function handleStackedItemDragStart(e) {
  console.log("Drag start");
  e.dataTransfer.setData("text/plain", e.target.id);
  e.target.style.opacity = "0.5";
}

function handleStackedItemDrag(e) {
  console.log("Dragging");
  const attachedDropzoneId = e.target.dataset.attachedDropzoneId;
  const dropzone = document
    .getElementById(`node-${attachedDropzoneId}`)
    .querySelector(".dropzone");
  const nodeId = e.target.id.split("-")[2];
  const originalNode = document.getElementById(`node-${nodeId}`);
  if (
    dropzone &&
        !dropzone.contains(document.elementFromPoint(e.clientX, e.clientY))
  ) {
    console.log("Item dragged outside the dropzone");
    // display forbidden cursor
    e.target.style.cursor = "not-allowed";
  } else {
    console.log("Item dragged inside the dropzone");
    e.target.style.cursor = "grab";
  }
}

function handleStackedItemDragEnd(e) {
  console.log("Drag ended");
  e.target.style.opacity = "";
  e.target.style.cursor = "grab";
}

function detachNodeFromDropzone(node, dropzoneNode, stackedItem) {
  dropzoneElement = document
    .getElementById(`node-${dropzoneNode.id}`)
    .querySelector(".dropzone");
  anime({
    targets: stackedItem,
    translateX: [0, -20],
    opacity: [1, 0],
    duration: 300,
    easing: "easeOutCubic",
    complete: function () {
      stackedItem.remove();
      dropzoneNode.data.stackedItems = dropzoneNode.data.stackedItems.filter(
        (item) => item.id !== node.id
      );
      if (node && node.data) {
        node.data.attachedToDropzone = false;
        node.data.attachedDropzoneId = null;
        console.log(
          `Node ${node.id} detached from the dropzone ${dropzoneNode.id}`
        );
        nodeElement = document.getElementById(`node-${node.id}`);
        nodeElement.classList.remove("hidden-node");
        const pos_x = node.data.pos_x;
        const pos_y = node.data.pos_y;
        anime({
          targets: nodeElement,
          left: pos_x,
          top: pos_y,
          opacity: [0, 1],
          duration: 300,
          easing: "easeOutCubic",
        });
      }
    },
  });
}

function expandNodeFromDropzone(node, dropzoneNode, stackedItem) {
  const nodeElement = document.getElementById(`node-${node.id}`);
  const dropzoneElement = document.getElementById(`node-${dropzoneNode.id}`);

  // Store the original position
  const originalPosition = {
    x: node.pos_x,
    y: node.pos_y,
  };

  // Unhide the node and set its position
  nodeElement.classList.remove("hidden-node");
  nodeElement.style.position = "absolute";
  nodeElement.style.cursor = "unset";
  // Position the node next to the dropzone
  const dropzoneRect = dropzoneElement.getBoundingClientRect();
  const stackedItemRect = stackedItem.getBoundingClientRect();
  const expandedLeft = dropzoneRect.right + 20;
  const expandedTop = stackedItemRect.top;

  node.data.pos_x = expandedLeft;
  node.data.pos_y = expandedTop;

  // Create and position the speech bubble tail
  const tail = document.createElement("div");
  tail.className = "speech-bubble-tail";
  nodeElement.appendChild(tail);

  // Calculate tail position
  const expandedRect = nodeElement.getBoundingClientRect();
  const tailSize = 15; // Size of the tail in pixels
  let tailLeft, tailTop, tailStyle;

  if (
    stackedItemRect.top + stackedItemRect.height / 2 <
        expandedRect.top + expandedRect.height / 2
  ) {
    // Tail should be on the top-left corner
    tailLeft = -tailSize;
    tailTop = 0;
    tailStyle = `
            border-top: ${tailSize}px solid transparent;
            border-bottom: ${tailSize}px solid transparent;
            border-right: ${tailSize}px solid transparent;
        `;
  } else {
    // Tail should be on the bottom-left corner
    tailLeft = -tailSize;
    tailTop = expandedRect.height - 2 * tailSize;
    tailStyle = `
            border-top: ${tailSize}px solid transparent;
            border-bottom: ${tailSize}px solid transparent;
            border-right: ${tailSize}px solid transparent;
        `;
  }

  tail.style.cssText = `
        position: absolute;
        left: ${tailLeft}px;
        top: ${tailTop}px;
        width: 0;
        height: 0;
        ${tailStyle}
    `;

  // Make the node undraggable by overriding Drawflow's drag behavior
  const originalOnMouseDown = nodeElement.onmousedown;
  nodeElement.onmousedown = function (e) {
    if (
      e.target.tagName === "INPUT" ||
            e.target.tagName === "SELECT" ||
            e.target.tagName === "BUTTON"
    ) {
      return;
    }
    e.stopPropagation();
  };

  // Highlight the stacked item
  stackedItem.style.backgroundColor = "#45a049";
  stackedItem.classList.add("undraggable");

  // Function to collapse the expanded node
  function collapseNode() {
    nodeElement.classList.add("hidden-node");
    stackedItem.style.backgroundColor = "";
    stackedItem.classList.remove("undraggable");
    nodeElement.onmousedown = originalOnMouseDown;
    node.pos_x = originalPosition.x;
    node.pos_y = originalPosition.y;
    tail.remove();
    document.removeEventListener("click", handleOutsideClick);
  }

  // Handle clicks outside the node
  function handleOutsideClick(event) {
    if (!nodeElement.contains(event.target) && event.target !== stackedItem) {
      collapseNode();
    }
  }

  nodeElement.querySelector(".toggle-arrow").addEventListener("click", (e) => {
    collapseNode();
  });
  // Add event listener for outside clicks
  setTimeout(() => {
    document.addEventListener("click", handleOutsideClick);
  }, 0);
}

function removeNodeFromDropzone(node, dropzoneNode, stackedItem) {
  anime({
    targets: stackedItem,
    translateX: [0, -20],
    opacity: [1, 0],
    duration: 300,
    easing: "easeOutCubic",
    complete: function () {
      stackedItem.remove();
      node.data.attachedToDropzone = false;
      node.data.attachedDropzoneId = null;
      node.data.stackedItems = dropzoneNode.data.stackedItems.filter(
        (item) => item.id !== node.id
      );
      editor.removeNodeId("node-" + node.id);
      console.log(
        `Node ${node.id} removed from the dropzone ${dropzoneNode.id}`
      );
    },
  });
}
