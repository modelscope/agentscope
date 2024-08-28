document.addEventListener('DOMContentLoaded', function() {
    showTab('tab1');
});

function sendWorkflow(fileName) {
    if (confirm('Are you sure you want to import this workflow?')) {
        const workstationUrl = '/workstation?filename=' + encodeURIComponent(fileName);
        window.location.href = workstationUrl;
    }
}

function deleteWorkflow(fileName) {
    if (confirm('Workflow has been deleted？')) {
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
                alert(data.error);
            } else {
                showLoadWorkflowList('tab2');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('delete workflow error.');
        });
    }
}

function showGalleryWorkflowList(tabId) {
    const mockData = [
        { name: 'Workflow1', description: 'This is the first workflow', thumbnail: 'path/to/thumbnail1.jpg' },
        { name: 'Workflow2', description: 'This is the second workflow', thumbnail: 'path/to/thumbnail2.jpg' },
        { name: 'Workflow3', description: 'This is the third workflow', thumbnail: 'path/to/thumbnail3.jpg' },
        { name: 'Workflow1', description: 'This is the first workflow', thumbnail: 'path/to/thumbnail1.jpg' },
        { name: 'Workflow2', description: 'This is the second workflow', thumbnail: 'path/to/thumbnail2.jpg' },
        { name: 'Workflow3', description: 'This is the third workflow', thumbnail: 'path/to/thumbnail3.jpg' }
    ];

    const container = document.getElementById(tabId).querySelector('.grid-container');
    container.innerHTML = '';

    mockData.forEach(workflowData => {
        const workflowName = workflowData.name;
        createGridItem(workflowName, container, workflowData.thumbnail);
    });
}

function createGridItem(name, container) {
    const gridItem = document.createElement('div');
    gridItem.className = 'grid-item';
    gridItem.textContent = name;
    container.appendChild(gridItem);
}

function showTab(tabId) {
    var tabs = document.getElementsByClassName("tab");
    for (var i = 0; i < tabs.length; i++) {
        tabs[i].classList.remove("active");
        tabs[i].style.display = "none";
    }
    var tab = document.getElementById(tabId);
    if (tab) {
        tab.classList.add("active");
        tab.style.display = "block";
        if (tabId === "tab2") {
            showLoadWorkflowList(tabId);
        } else if (tabId === "tab1") {
            showGalleryWorkflowList(tabId);
        }
    }
}

function createGridItem(workflowName, container) {
    var gridItem = document.createElement('div');
    gridItem.className = 'grid-item';
    gridItem.style.backgroundImage = `url('')`;
    gridItem.style.backgroundSize = 'cover';
    gridItem.style.backgroundPosition = 'center';
    gridItem.style.backgroundRepeat = 'no-repeat';

    var caption = document.createElement('div');
    caption.className = 'caption';

    var h3 = document.createElement('h3');
    h3.textContent = workflowName;

    var p = document.createElement('p');
    // p.textContent = '5.0 stars - 244 reviews';

    var link = document.createElement('a');
    link.href = '#';
    link.textContent = 'Load';
    link.onclick = function(e) {
        e.preventDefault();
        sendWorkflow(workflowName);
    };

    var deleteButton = document.createElement('button');
    deleteButton.textContent = 'Delete';
    deleteButton.onclick = function(e) {
        e.preventDefault();
        deleteWorkflow(workflowName);
    };

    caption.appendChild(h3);
    caption.appendChild(p);
    caption.appendChild(link);
    caption.appendChild(deleteButton);

    gridItem.appendChild(caption);

    container.appendChild(gridItem);
}

function showLoadWorkflowList(tabId) {
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

            const container = document.getElementById(tabId).querySelector('.grid-container');
            container.innerHTML = '';

            data.files.forEach(workflowName => {
                createGridItem(workflowName, container);
            });
        })
        .catch(error => {
            console.error('Error:', error);
            alert('fetch WorkflowList err。');
        });
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