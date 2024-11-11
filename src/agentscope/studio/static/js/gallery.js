showTab("tab1");

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
    console.log(`Activated tab with ID: ${tab.id}`);

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
      console.log("Loading Gallery Workflow List");
      showGalleryWorkflowList(tabId);
    }
  }
}

function sendWorkflow(fileName) {
  if (confirm("Are you sure you want to import this workflow?")) {
    const workstationUrl = "/workstation?filename=" + encodeURIComponent(fileName);
    window.location.href = workstationUrl;
  }
}

function importGalleryWorkflow(data) {
  try {
    const parsedData = JSON.parse(data);
    addHtmlAndReplacePlaceHolderBeforeImport(parsedData)
      .then(() => {
        editor.clear();
        editor.import(parsedData);
        importSetupNodes(parsedData);

        if (confirm("Imported!")) {
          const workstationUrl = "/workstation";
          window.location.href = workstationUrl;
        }
      })
      .catch(error => {
        alert(`Import error: ${error}`);
      });
  } catch (error) {
    alert(`Import error: ${error}`);
  }
}

function deleteWorkflow(fileName) {
  if (confirm("Workflow has been deleted？")) {
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
          alert(data.error);
        } else {
          showLoadWorkflowList("tab2");
        }
      })
      .catch(error => {
        console.error("Error:", error);
        alert("delete workflow error.");
      });
  }
}

function createGridItem(workflowName, container, thumbnail, author = "", time = "", showDeleteButton = false, index) {
  const gridItem = document.createElement("div");
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
  button.textContent = "Load";
  button.className = "button";
  button.style.marginRight = "5px";
  button.style.backgroundColor = "#007aff";
  button.style.backgroundImage = "linear-gradient(to right, #6e48aa, #9d50bb)";
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
      sendWorkflow(workflowName);
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
    deleteButton.style.backgroundImage = "linear-gradient(to right, #6e48aa, #9d50bb)";
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

// let galleryWorkflows = [];

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
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      console.log("Fetched gallery data:", data);

      const workflows = data.json || [];

      if (!Array.isArray(workflows)) {
        console.error("The server did not return an array as expected.", data);
        workflows = [workflows];
      }

      workflows.forEach(workflow => {
        const meta = workflow.meta;
        const title = meta.title;
        const author = meta.author;
        const time = meta.time;
        const thumbnail = meta.thumbnail || generateThumbnailFromContent(meta);
        createGridItem(title, container, thumbnail, author, time, false);
      });
    })
    .catch(error => {
      console.error("Error fetching gallery workflows:", error);
      alert("Failed to load gallery workflows.");
    });
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
