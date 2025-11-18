// Set today's date as default
document.addEventListener('DOMContentLoaded', function() {
    const dateInput = document.getElementById('comment-date');
    if (dateInput) {
        const today = new Date().toISOString().split('T')[0];
        dateInput.value = today;
    }
});

// Helper function to display results
function displayResult(elementId, data, isError = false) {
    const resultDiv = document.getElementById(elementId);
    resultDiv.textContent = JSON.stringify(data, null, 2);
    resultDiv.style.borderLeft = isError ? '4px solid #dc3545' : '4px solid #28a745';
}

// Run Auto-Triage
function runTriage() {
    const featureSelect = document.getElementById('feature-select');
    const featureName = featureSelect.value;
    const resultDiv = document.getElementById('triage-result');
    
    if (!featureName) {
        displayResult('triage-result', {error: 'Please select a feature'}, true);
        return;
    }
    
    resultDiv.textContent = 'Starting triage process...';
    resultDiv.style.borderLeft = '4px solid #ffc107';
    
    fetch('/api/triage/run', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({feature_name: featureName})
    })
    .then(response => response.json())
    .then(data => {
        displayResult('triage-result', data);
        
        // If task started, poll for status
        if (data.task_id) {
            pollTaskStatus(data.task_id, 'triage-result');
        }
    })
    .catch(error => {
        displayResult('triage-result', {error: error.message}, true);
    });
}

// Poll task status
function pollTaskStatus(taskId, resultElementId, interval = 5000) {
    const statusInterval = setInterval(() => {
        fetch(`/api/triage/status/${taskId}`)
        .then(response => response.json())
        .then(data => {
            displayResult(resultElementId, data.task);
            
            // Stop polling if task is completed or failed
            if (data.task && (data.task.status === 'completed' || data.task.status === 'failed')) {
                clearInterval(statusInterval);
            }
        })
        .catch(error => {
            clearInterval(statusInterval);
            displayResult(resultElementId, {error: error.message}, true);
        });
    }, interval);
}

// Get Triaged Data
function getTriagedData() {
    const resultDiv = document.getElementById('data-result');
    resultDiv.textContent = 'Loading triaged data...';
    
    fetch('/api/triage/triaged-data')
    .then(response => response.json())
    .then(data => {
        displayResult('data-result', data);
    })
    .catch(error => {
        displayResult('data-result', {error: error.message}, true);
    });
}

// Get Untriaged Data
function getUntriagedData() {
    const featureSelect = document.getElementById('feature-select');
    const featureName = featureSelect.value;
    const resultDiv = document.getElementById('data-result');
    
    if (!featureName) {
        displayResult('data-result', {error: 'Please select a feature first'}, true);
        return;
    }
    
    resultDiv.textContent = 'Loading untriaged data...';
    
    fetch(`/api/triage/untriaged-data?feature_name=${featureName}`)
    .then(response => response.json())
    .then(data => {
        displayResult('data-result', data);
    })
    .catch(error => {
        displayResult('data-result', {error: error.message}, true);
    });
}

// Get All Tasks
function getAllTasks() {
    const resultDiv = document.getElementById('data-result');
    resultDiv.textContent = 'Loading all tasks...';
    
    fetch('/api/tasks')
    .then(response => response.json())
    .then(data => {
        displayResult('data-result', data);
    })
    .catch(error => {
        displayResult('data-result', {error: error.message}, true);
    });
}

// Add Comments to JIRA
function addComments() {
    const dateInput = document.getElementById('comment-date');
    const exeDate = dateInput.value;
    const resultDiv = document.getElementById('comment-result');
    
    if (!exeDate) {
        displayResult('comment-result', {error: 'Please select a date'}, true);
        return;
    }
    
    resultDiv.textContent = 'Adding comments to JIRA tickets...';
    resultDiv.style.borderLeft = '4px solid #ffc107';
    
    fetch('/api/comments/add', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            exe_date: exeDate,
            triage_by: 'auto-triage'
        })
    })
    .then(response => response.json())
    .then(data => {
        displayResult('comment-result', data);
        
        // If task started, poll for status
        if (data.task_id) {
            pollTaskStatus(data.task_id, 'comment-result');
        }
    })
    .catch(error => {
        displayResult('comment-result', {error: error.message}, true);
    });
}

// Process Skipped Items
function processSkipped() {
    const resultDiv = document.getElementById('utility-result');
    resultDiv.textContent = 'Processing skipped items...';
    resultDiv.style.borderLeft = '4px solid #ffc107';
    
    fetch('/api/triage/skipped', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        displayResult('utility-result', data);
        
        // If task started, poll for status
        if (data.task_id) {
            pollTaskStatus(data.task_id, 'utility-result');
        }
    })
    .catch(error => {
        displayResult('utility-result', {error: error.message}, true);
    });
}

// Clean Files
function cleanFiles() {
    const resultDiv = document.getElementById('utility-result');
    
    if (!confirm('Are you sure you want to clean temporary files and databases?')) {
        return;
    }
    
    resultDiv.textContent = 'Cleaning files...';
    resultDiv.style.borderLeft = '4px solid #ffc107';
    
    fetch('/api/clean', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        displayResult('utility-result', data);
    })
    .catch(error => {
        displayResult('utility-result', {error: error.message}, true);
    });
}

// Add smooth scrolling
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth'
            });
        }
    });
});
