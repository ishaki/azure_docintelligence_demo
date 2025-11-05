// File management
let selectedFiles = [];

const fileInput = document.getElementById('fileInput');
const selectFilesBtn = document.getElementById('selectFilesBtn');
const uploadArea = document.getElementById('uploadArea');
const filesList = document.getElementById('filesList');
const uploadBtn = document.getElementById('uploadBtn');
const clearBtn = document.getElementById('clearBtn');
const resultsSection = document.getElementById('resultsSection');
const resultsContainer = document.getElementById('resultsContainer');
const loadingOverlay = document.getElementById('loadingOverlay');

// Event listeners
selectFilesBtn.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', handleFileSelect);

uploadArea.addEventListener('dragover', handleDragOver);
uploadArea.addEventListener('dragleave', handleDragLeave);
uploadArea.addEventListener('drop', handleDrop);
uploadArea.addEventListener('click', () => fileInput.click());

uploadBtn.addEventListener('click', handleUpload);
clearBtn.addEventListener('click', clearAll);

function handleFileSelect(event) {
    const files = Array.from(event.target.files);
    addFiles(files);
}

function handleDragOver(event) {
    event.preventDefault();
    event.stopPropagation();
    uploadArea.classList.add('dragover');
}

function handleDragLeave(event) {
    event.preventDefault();
    event.stopPropagation();
    uploadArea.classList.remove('dragover');
}

function handleDrop(event) {
    event.preventDefault();
    event.stopPropagation();
    uploadArea.classList.remove('dragover');
    
    const files = Array.from(event.dataTransfer.files).filter(file => 
        file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')
    );
    
    if (files.length === 0) {
        alert('Please drop only PDF files.');
        return;
    }
    
    addFiles(files);
}

function addFiles(files) {
    files.forEach(file => {
        if (!selectedFiles.some(f => f.name === file.name && f.size === file.size)) {
            selectedFiles.push(file);
        }
    });
    
    updateFilesList();
    updateButtons();
}

function removeFile(index) {
    selectedFiles.splice(index, 1);
    updateFilesList();
    updateButtons();
}

function updateFilesList() {
    filesList.innerHTML = '';
    
    selectedFiles.forEach((file, index) => {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        
        const fileInfo = document.createElement('div');
        fileInfo.className = 'file-info';
        
        const fileIcon = document.createElement('span');
        fileIcon.className = 'file-icon';
        fileIcon.textContent = '📄';
        
        const fileName = document.createElement('span');
        fileName.className = 'file-name';
        fileName.textContent = file.name;
        
        const fileSize = document.createElement('span');
        fileSize.className = 'file-size';
        fileSize.textContent = formatFileSize(file.size);
        
        const removeBtn = document.createElement('button');
        removeBtn.className = 'remove-file';
        removeBtn.textContent = '×';
        removeBtn.addEventListener('click', () => removeFile(index));
        
        fileInfo.appendChild(fileIcon);
        fileInfo.appendChild(fileName);
        fileInfo.appendChild(fileSize);
        
        fileItem.appendChild(fileInfo);
        fileItem.appendChild(removeBtn);
        
        filesList.appendChild(fileItem);
    });
}

function updateButtons() {
    uploadBtn.disabled = selectedFiles.length === 0;
    clearBtn.style.display = selectedFiles.length > 0 ? 'block' : 'none';
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function clearAll() {
    selectedFiles = [];
    fileInput.value = '';
    updateFilesList();
    updateButtons();
    resultsSection.style.display = 'none';
    resultsContainer.innerHTML = '';
}

async function handleUpload() {
    if (selectedFiles.length === 0) return;
    
    // Show progress overlay
    showProgressOverlay(selectedFiles.length);
    resultsSection.style.display = 'none';
    
    try {
        const formData = new FormData();
        selectedFiles.forEach(file => {
            formData.append('files', file);
        });
        
        // Start async processing
        const response = await fetch('/api/analyze', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to analyze documents');
        }
        
        const data = await response.json();
        const jobId = data.job_id;
        
        // Poll for status updates
        await pollJobStatus(jobId);
        
    } catch (error) {
        console.error('Error:', error);
        alert('Error analyzing documents: ' + error.message);
        loadingOverlay.style.display = 'none';
    }
}

function showProgressOverlay(totalFiles) {
    const overlay = document.getElementById('loadingOverlay');
    overlay.innerHTML = `
        <div class="progress-container">
            <h3>Processing Documents...</h3>
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill"></div>
            </div>
            <p id="progressText">Initializing...</p>
            <div class="files-progress" id="filesProgress"></div>
        </div>
    `;
    overlay.style.display = 'flex';
}

async function pollJobStatus(jobId) {
    const maxAttempts = 300; // 5 minutes max
    const pollInterval = 1000; // 1 second
    
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
        try {
            const response = await fetch(`/api/status/${jobId}`);
            const status = await response.json();
            
            // Update progress UI
            updateProgress(status);
            
            if (status.status === 'completed') {
                // Fetch final results
                const resultsResponse = await fetch(`/api/results/${jobId}`);
                const results = await resultsResponse.json();
                displayResults(results.results);
                loadingOverlay.style.display = 'none';
                return;
            }
            
            // Wait before next poll
            await new Promise(resolve => setTimeout(resolve, pollInterval));
            
        } catch (error) {
            console.error('Error polling status:', error);
            // Continue polling on error
        }
    }
    
    throw new Error('Processing timeout');
}

function updateProgress(status) {
    const totalFiles = status.total_files;
    const completedFiles = status.files.filter(f => 
        f.status === 'completed' || f.status === 'error'
    ).length;
    
    const progressPercent = (completedFiles / totalFiles) * 100;
    
    // Update progress bar
    const progressFill = document.getElementById('progressFill');
    if (progressFill) {
        progressFill.style.width = `${progressPercent}%`;
    }
    
    // Update text
    const progressText = document.getElementById('progressText');
    if (progressText) {
        progressText.textContent = `Processing ${completedFiles} of ${totalFiles} documents...`;
    }
    
    // Update individual file status
    const filesProgress = document.getElementById('filesProgress');
    if (filesProgress) {
        filesProgress.innerHTML = status.files.map(file => `
            <div class="file-progress-item ${file.status}">
                <span class="file-icon">${getStatusIcon(file.status)}</span>
                <span class="file-name">${file.filename}</span>
                <span class="file-status">${file.message}</span>
            </div>
        `).join('');
    }
}

function getStatusIcon(status) {
    switch(status) {
        case 'completed': return '✓';
        case 'processing': return '⏳';
        case 'error': return '✗';
        default: return '⋯';
    }
}

function displayResults(results) {
    resultsContainer.innerHTML = '';
    resultsSection.style.display = 'block';
    
    results.forEach(result => {
        const documentResult = document.createElement('div');
        documentResult.className = 'document-result';
        
        const header = document.createElement('div');
        header.className = 'document-header';
        
        const name = document.createElement('div');
        name.className = 'document-name';
        name.textContent = result.filename;
        
        const status = document.createElement('span');
        status.className = `document-status status-${result.status}`;
        status.textContent = result.status === 'success' ? 'Success' : 'Error';
        
        header.appendChild(name);
        header.appendChild(status);
        documentResult.appendChild(header);
        
        if (result.status === 'success' && result.fields && result.fields.length > 0) {
            const table = document.createElement('table');
            table.className = 'fields-table';
            
            const thead = document.createElement('thead');
            const headerRow = document.createElement('tr');
            ['Field Name', 'Field Value', 'Confidence'].forEach(text => {
                const th = document.createElement('th');
                th.textContent = text;
                headerRow.appendChild(th);
            });
            thead.appendChild(headerRow);
            table.appendChild(thead);
            
            const tbody = document.createElement('tbody');
            result.fields.forEach(field => {
                const row = document.createElement('tr');
                
                const nameCell = document.createElement('td');
                nameCell.className = 'field-name';
                nameCell.textContent = field.field_name || '-';
                
                const valueCell = document.createElement('td');
                valueCell.className = 'field-value';
                // Handle newlines and formatting
                if (field.field_value && field.field_value !== '-' && field.field_value !== '(not found)' && field.field_value !== '(empty)') {
                    const valueText = String(field.field_value).trim();
                    // Replace newlines with line breaks for better display
                    if (valueText.includes('\n')) {
                        valueCell.innerHTML = valueText.replace(/\n/g, '<br>');
                    } else {
                        valueCell.textContent = valueText;
                    }
                } else if (field.field_value === '(not found)' || field.field_value === '(empty)') {
                    valueCell.textContent = field.field_value;
                    valueCell.style.fontStyle = 'italic';
                    valueCell.style.color = 'var(--text-secondary)';
                } else {
                    valueCell.textContent = '-';
                }
                
                const confidenceCell = document.createElement('td');
                if (field.confidence !== null && field.confidence !== undefined) {
                    const badge = document.createElement('span');
                    badge.className = 'confidence-badge';
                    
                    if (field.confidence >= 80) {
                        badge.className += ' confidence-high';
                    } else if (field.confidence >= 50) {
                        badge.className += ' confidence-medium';
                    } else {
                        badge.className += ' confidence-low';
                    }
                    
                    badge.textContent = `${field.confidence}%`;
                    confidenceCell.appendChild(badge);
                } else {
                    confidenceCell.textContent = 'N/A';
                }
                
                row.appendChild(nameCell);
                row.appendChild(valueCell);
                row.appendChild(confidenceCell);
                tbody.appendChild(row);
            });
            
            table.appendChild(tbody);
            documentResult.appendChild(table);
            
        } else if (result.status === 'error') {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-message';
            errorDiv.textContent = `Error: ${result.error || 'Unknown error occurred'}`;
            documentResult.appendChild(errorDiv);
        } else {
            const emptyDiv = document.createElement('div');
            emptyDiv.className = 'empty-state';
            emptyDiv.textContent = 'No fields extracted from this document.';
            documentResult.appendChild(emptyDiv);
        }
        
        resultsContainer.appendChild(documentResult);
    });
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

