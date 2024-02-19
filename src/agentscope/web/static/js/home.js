const projectList = document.getElementById('project-list');

// Global variable to store original data
var originalData = [];

$(document).ready(function () {
    // Initialize table without loading data
    initTable();

    // Add search listener
    $('#customSearch').on('keyup', function () {
        var searchText = $(this).val().toLowerCase();
        filterTable(searchText);
    });

    // Load data for the first time
    loadTableData();

    // Add refresh button listener
    $('#refreshButton').click(function () {
        loadTableData();
    });

    // Initialize dropdown menu
    initDropdownMenu();
});

// Function to filter table data
function filterTable(searchText) {
    // Filter original data by search text
    var filteredData = originalData.filter(function (item) {
        return item.name.toLowerCase().includes(searchText) ||
            item.id.toString().includes(searchText) ||
            item.project.toLowerCase().includes(searchText) ||
            item.timestamp.toLowerCase().includes(searchText);
    });
    // Load filtered data into table
    $('#run-table').bootstrapTable('load', filteredData);
}

function initDropdownMenu() {
    // Add listener to dropdown menu
    $('.dropdown-menu li input[type="checkbox"]').on('change', function () {
        // Obtain column to be changed
        var columnField = $(this).data('column');
        console.log(columnField)
        if (columnField === "all") {
            if ($(this).prop('checked')) {
                // Show all columns if "all" is checked
                $('#run-table').bootstrapTable('showAllColumns');
                // Change all checkboxes to checked
                $('.dropdown-menu li input[type="checkbox"]').prop('checked', true);
            } else {
                $(this).prop('checked', false);
            }
        } else {
            if ($(this).prop('checked')) {
                // Show this column
                $('#run-table').bootstrapTable('showColumn', columnField);
                // If all columns are checked, then check "all" checkbox
                if ($('.dropdown-menu li input[type="checkbox"]:checked').length === $('.dropdown-menu li input[type="checkbox"]').length - 1) {
                    $('.dropdown-menu li input[type="checkbox"][data-column="all"]').prop('checked', true);
                }
            } else {
                // Hide this column
                $('#run-table').bootstrapTable('hideColumn', columnField);
                // Change "all" checkbox to unchecked
                $('.dropdown-menu li input[type="checkbox"][data-column="all"]').prop('checked', false);
            }
        }
        // Refresh table view
        $('#run-table').bootstrapTable('resetView');
    });
}

// Function to filter table data by project
function filterTableByProject(searchText) {
    if (searchText.toLowerCase() === 'all') {
        $('#run-table').bootstrapTable('load', originalData);
    } else {
        var filteredData = originalData.filter(function (item) {
            return item.project.toLowerCase().includes(searchText.toLowerCase());
        });
        // Load filtered data into table
        $('#run-table').bootstrapTable('load', filteredData);
    }
}

// Function to initialize table
function initTable() {
    $('#run-table').bootstrapTable({
        // toolbar: "#custom-toolbar",
        search: false,
        showRefresh: false,
        sortable: true,
        showColumns: false,
        columns: [
            {field: 'id', title: 'ID', sortable: true},
            {field: 'name', title: 'NAME', sortable: true},
            {field: 'project', title: 'PROJECT', sortable: true},
            {field: 'timestamp', title: 'TIMESTAMP', sortable: true},
        ],
        // Click event
        onClickRow: function (row, $element, field) {
            // Jump to the detail page
            window.location.href = `/run/${row.id}`;
        }
    });
}

function loadTableData() {
    fetch('/getProjects')
        .then(response => response.json())
        .then(projects => {
            update_projects(projects.names);
            originalData = projects.runs; // 存储原始数据
            $('#run-table').bootstrapTable('load', projects.runs);
        })
        .catch(error => {
            console.error('Error loading table data:', error);
        });
}

function update_projects(projects) {
    // Clear project list
    while (projectList.firstChild) {
        projectList.removeChild(projectList.firstChild);
    }

    // Add all projects
    const allElement = document.createElement('div')
    allElement.classList.add("project-list-item")

    allElement.innerHTML = `
    <svg class="proj-icon" viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg">
        <path d="M128 64h288a64 64 0 0 1 64 64v288a64 64 0 0 1-64 64H128a64 64 0 0 1-64-64V128a64 64 0 0 1 64-64z m32 64a32 32 0 0 0-32 32v224a32 32 0 0 0 32 32h224a32 32 0 0 0 32-32V160a32 32 0 0 0-32-32H160z m448-64h288a64 64 0 0 1 64 64v288a64 64 0 0 1-64 64h-288a64 64 0 0 1-64-64V128a64 64 0 0 1 64-64z m32 64a32 32 0 0 0-32 32v224a32 32 0 0 0 32 32h224a32 32 0 0 0 32-32V160a32 32 0 0 0-32-32h-224z m-32 416h288a64 64 0 0 1 64 64v288a64 64 0 0 1-64 64h-288a64 64 0 0 1-64-64v-288a64 64 0 0 1 64-64z m32 64a32 32 0 0 0-32 32v224a32 32 0 0 0 32 32h224a32 32 0 0 0 32-32v-224a32 32 0 0 0-32-32h-224zM128 544h288a64 64 0 0 1 64 64v288a64 64 0 0 1-64 64H128a64 64 0 0 1-64-64v-288a64 64 0 0 1 64-64z m32 64a32 32 0 0 0-32 32v224a32 32 0 0 0 32 32h224a32 32 0 0 0 32-32v-224a32 32 0 0 0-32-32H160z">
        </path>
    </svg>All Projects`

    allElement.addEventListener('click', function (e) {
        // Prevent default behavior, because these are links <a>
        e.preventDefault();
        // Update table
        filterTableByProject('all')
    });

    projectList.appendChild(allElement);

    projects.forEach((project, index) => {
        // Generate icon by the first two chars of project name (upper case)
        let chars = project.slice(0, 2).toUpperCase()

        // Append new project
        const projElement = document.createElement('div');
        projElement.classList.add("project-list-item")

        projElement.innerHTML = `
        <div class="proj-icon">
            ${chars}
        </div>${project}`

        projElement.addEventListener('click', function (e) {
            // Prevent default behavior, because these are links <a>
            e.preventDefault();
            // Update table
            filterTableByProject(project);
        });

        projectList.appendChild(projElement);
    });

    // Default choice
    allElement.classList.add('selected');

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