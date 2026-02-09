const API_BASE = "http://localhost:8000/api/v1";

const elements = {
    inputSection: document.getElementById('input-section'),
    progressSection: document.getElementById('progress-section'),
    generateBtn: document.getElementById('generate-btn'),
    userPrompt: document.getElementById('user-prompt'),
    refUrl: document.getElementById('ref-url'),
    logsContainer: document.getElementById('logs-container'),
    steps: document.querySelectorAll('.step'),
    tabs: document.querySelectorAll('.tab'),
    resetBtn: document.getElementById('reset-btn'),
    downloadBtn: document.getElementById('download-btn'),
    outputIcon: document.getElementById('output-icon'),
    outputTitle: document.getElementById('output-title'),
    outputMessage: document.getElementById('output-message'),
    downloadSection: document.getElementById('download-section'),
    outputTabBtn: document.getElementById('output-tab-btn'),
    // Approval elements
    featureApprovalBanner: document.getElementById('feature-approval-banner'),
    techstackApprovalBanner: document.getElementById('techstack-approval-banner'),
    featureApprovalActions: document.getElementById('feature-approval-actions'),
    techstackApprovalActions: document.getElementById('techstack-approval-actions'),
    approveFeaturesBtn: document.getElementById('approve-features-btn'),
    approveTechstackBtn: document.getElementById('approve-techstack-btn'),
    editFeaturesBtn: document.getElementById('edit-features-btn'),
    addFeatureBtn: document.getElementById('add-feature-btn'),
    userRequirementsSection: document.getElementById('user-requirements-section'),
    userRequirementsInput: document.getElementById('user-requirements-input'),
    techStackOptions: document.getElementById('tech-stack-options'),
    featuresEditableBadge: document.getElementById('features-editable-badge'),
    designEditableBadge: document.getElementById('design-editable-badge'),
    generateStructureBtn: document.getElementById('generate-structure-btn'),
};

// Store blueprint data globally
let blueprintData = {
    tech_stack: null,
    file_structure: [],
    asset_manifest: [],
    reasoning: null,
    classification: null,
    project_features: [],
    design_specs: null
};

// Store current task and approval state
let currentTaskId = null;
let currentEventSource = null; // Track SSE connection
let isEditMode = false;
let approvalState = {
    features_approved: false,
    techstack_approved: false
};

// Track what has been rendered to prevent blinking
let renderedState = {
    features: false,
    designSpecs: false,
    techStack: false,
    fileStructure: false,
    assets: false,
    lastFeatureCount: 0,
    lastNode: null
};

// Tech stack descriptions for richer display
const techStackDescriptions = {
    'html_single': 'Single HTML file with embedded CSS/JS',
    'html_multi': 'Multiple HTML pages with shared stylesheets',
    'react_cdn': 'React application (CDN-based)',
    'vue_cdn': 'Vue.js application (CDN-based)'
};

// Event Listeners
elements.generateBtn.addEventListener('click', startBuild);
elements.resetBtn.addEventListener('click', resetUI);
elements.approveFeaturesBtn?.addEventListener('click', approveFeatures);
elements.approveTechstackBtn?.addEventListener('click', approveTechstack);
elements.editFeaturesBtn?.addEventListener('click', toggleEditMode);
elements.addFeatureBtn?.addEventListener('click', addNewFeature);
elements.generateStructureBtn?.addEventListener('click', generateStructure);

// Tab switching
elements.tabs.forEach(tab => {
    tab.addEventListener('click', () => switchTab(tab.dataset.tab));
});

function switchTab(tabName) {
    // Update tab buttons
    elements.tabs.forEach(t => t.classList.remove('active'));
    document.querySelector(`[data-tab="${tabName}"]`)?.classList.add('active');

    // Update tab content - properly hide all and show selected
    document.querySelectorAll('.tab-content').forEach(c => {
        c.classList.remove('active');
        c.classList.add('hidden');
    });

    const targetTab = document.getElementById(`${tabName}-tab`);
    if (targetTab) {
        targetTab.classList.remove('hidden');
        targetTab.classList.add('active');
    }
}

function autoNavigateToTab(node, approvalStage) {
    // Auto-navigate based on approval stage
    if (approvalStage === 'feature_approval') {
        switchTab('planning');
    } else if (approvalStage === 'techstack_approval') {
        switchTab('technical');
    } else if (node === 'builder' || node === 'syntax_guard' || node === 'auditor') {
        switchTab('logs');
    } else if (node === 'packager') {
        switchTab('output');
    }
}

async function startBuild() {
    const userQuery = elements.userPrompt.value.trim();
    if (!userQuery) {
        alert('Please describe your app first!');
        return;
    }

    // Reset approval state
    approvalState = { features_approved: false, techstack_approved: false };
    isEditMode = false;

    // Reset rendered state
    renderedState = {
        features: false,
        designSpecs: false,
        techStack: false,
        fileStructure: false,
        assets: false,
        lastFeatureCount: 0,
        lastNode: null
    };

    elements.inputSection.classList.add('hidden');
    elements.progressSection.classList.remove('hidden');
    resetTabContent();
    addLog('Initializing HITL build pipeline...', 'system');

    try {
        const response = await fetch(`${API_BASE}/build`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_query: userQuery,
                reference_url: elements.refUrl.value.trim() || null
            })
        });

        const data = await response.json();
        currentTaskId = data.task_id;
        addLog(`Task created: ${data.task_id}`, 'success');
        addLog('Pipeline will pause for your approval at each stage.', 'info');

        // Connect to SSE stream
        connectToStream(data.task_id);
    } catch (error) {
        addLog(`Error: ${error.message}`, 'error');
        updateOutputError(error.message);
    }
}

function connectToStream(taskId) {
    // Close any existing connection first
    if (currentEventSource) {
        currentEventSource.close();
        currentEventSource = null;
    }

    const eventSource = new EventSource(`${API_BASE}/build/${taskId}/stream`);
    currentEventSource = eventSource;

    eventSource.onmessage = function (event) {
        const data = JSON.parse(event.data);

        if (data.error) {
            addLog(`Error: ${data.error}`, 'error');
            eventSource.close();
            currentEventSource = null;
            return;
        }

        // Update progress UI
        updateProgress(data.node);

        // Store blueprint data
        if (data.tech_stack) blueprintData.tech_stack = data.tech_stack;
        if (data.file_structure) blueprintData.file_structure = data.file_structure;
        if (data.asset_manifest) blueprintData.asset_manifest = data.asset_manifest;
        if (data.reasoning) blueprintData.reasoning = data.reasoning;
        if (data.classification) blueprintData.classification = data.classification;
        if (data.project_features) blueprintData.project_features = data.project_features;
        if (data.design_specs) blueprintData.design_specs = data.design_specs;

        // Update tabs
        updatePlanningTab();
        updateTechnicalTab();

        // Log progress (only log new nodes)
        if (data.node && data.node !== 'start' && data.node !== renderedState.lastNode) {
            addLog(`Processing: ${formatNodeName(data.node)}`, 'info');
            renderedState.lastNode = data.node;
        }

        // Handle approval checkpoints - CLOSE STREAM and show UI
        if (data.waiting_for_approval) {
            eventSource.close();
            currentEventSource = null;
            handleApprovalCheckpoint(data.approval_stage);
            return; // Stop processing this stream
        }

        // Check completion
        if (data.is_complete) {
            eventSource.close();
            currentEventSource = null;
            if (data.status === 'completed') {
                showResult(taskId);
            } else if (data.error_message) {
                updateOutputError(data.error_message);
            }
        }
    };

    eventSource.onerror = function () {
        eventSource.close();
        currentEventSource = null;
        checkFinalStatus(taskId);
    };
}

function handleApprovalCheckpoint(stage) {
    if (stage === 'feature_approval') {
        addLog('⏸️ Waiting for your feature approval...', 'warning');
        showFeatureApprovalUI();
    } else if (stage === 'techstack_approval') {
        addLog('⏸️ Waiting for your tech stack approval...', 'warning');
        showTechstackApprovalUI();
    }
}

function showFeatureApprovalUI() {
    elements.featureApprovalBanner?.classList.remove('hidden');
    elements.featureApprovalActions?.classList.remove('hidden');
    elements.userRequirementsSection?.classList.remove('hidden');
    elements.featuresEditableBadge?.classList.remove('hidden');
    elements.designEditableBadge?.classList.remove('hidden');
    elements.addFeatureBtn?.classList.remove('hidden');

    // Update step indicator
    updateProgress('feature_approval_checkpoint');

    switchTab('planning');
}

function showTechstackApprovalUI() {
    elements.techstackApprovalBanner?.classList.remove('hidden');
    elements.techstackApprovalActions?.classList.remove('hidden');

    // Show editable section
    const techStackEdit = document.getElementById('tech-stack-edit');
    const techStackInput = document.getElementById('tech-stack-input');
    const techStackBadge = document.getElementById('techstack-editable-badge');
    const filesEditableBadge = document.getElementById('files-editable-badge');
    const addFileBtn = document.getElementById('add-file-btn');

    techStackEdit?.classList.remove('hidden');
    techStackBadge?.classList.remove('hidden');
    filesEditableBadge?.classList.remove('hidden');
    addFileBtn?.classList.remove('hidden');

    // Pre-fill with current tech stack
    if (techStackInput && blueprintData.tech_stack) {
        techStackInput.value = blueprintData.tech_stack;
    }

    // Make file structure editable
    renderEditableFileStructure();

    // Setup add file button handler
    addFileBtn?.addEventListener('click', addNewFile);

    updateProgress('techstack_approval_checkpoint');
    switchTab('technical');
}

function renderEditableFileStructure() {
    const fileTree = document.getElementById('file-tree');
    if (!fileTree || !blueprintData.file_structure) return;

    fileTree.innerHTML = '';
    blueprintData.file_structure.forEach((file, index) => {
        const li = document.createElement('li');
        li.className = 'editable-file-item';
        li.dataset.index = index;
        li.innerHTML = `
            <i class="fa-solid ${getFileIcon(file.type)}"></i>
            <input type="text" class="file-name-input" value="${file.name}" placeholder="filename.ext">
            <input type="text" class="file-purpose-input" value="${file.purpose || ''}" placeholder="File purpose...">
            <button type="button" class="remove-file-btn" onclick="removeFile(${index})">
                <i class="fa-solid fa-trash"></i>
            </button>
        `;
        fileTree.appendChild(li);
    });
}

function addNewFile() {
    const fileTree = document.getElementById('file-tree');
    if (!fileTree) return;

    const index = fileTree.children.length;
    const li = document.createElement('li');
    li.className = 'editable-file-item';
    li.dataset.index = index;
    li.innerHTML = `
        <i class="fa-solid fa-file-code"></i>
        <input type="text" class="file-name-input" value="" placeholder="filename.ext">
        <input type="text" class="file-purpose-input" value="" placeholder="File purpose...">
        <button type="button" class="remove-file-btn" onclick="removeFile(${index})">
            <i class="fa-solid fa-trash"></i>
        </button>
    `;
    fileTree.appendChild(li);

    // Focus on the name input
    li.querySelector('.file-name-input')?.focus();
    addLog('📄 New file added - enter name and purpose', 'info');
}

function removeFile(index) {
    const fileTree = document.getElementById('file-tree');
    const items = fileTree?.querySelectorAll('.editable-file-item');
    if (items && items[index]) {
        items[index].remove();
        addLog('🗑️ File removed', 'info');
    }
}

function collectApprovedFileStructure() {
    const items = document.querySelectorAll('.editable-file-item');
    if (items.length === 0) {
        return blueprintData.file_structure || [];
    }

    const files = [];
    items.forEach(item => {
        const nameInput = item.querySelector('.file-name-input');
        const purposeInput = item.querySelector('.file-purpose-input');

        if (nameInput && nameInput.value.trim()) {
            files.push({
                name: nameInput.value.trim(),
                purpose: purposeInput?.value.trim() || '',
                type: getFileTypeFromName(nameInput.value.trim())
            });
        }
    });
    return files.length > 0 ? files : blueprintData.file_structure || [];
}

function getFileTypeFromName(filename) {
    const ext = filename.split('.').pop()?.toLowerCase();
    const typeMap = {
        'html': 'page', 'htm': 'page',
        'css': 'stylesheet',
        'js': 'script',
        'py': 'script',
        'json': 'data',
        'md': 'documentation'
    };
    return typeMap[ext] || 'file';
}

async function approveFeatures() {
    if (!currentTaskId) return;

    addLog('Submitting feature approval...', 'info');

    // Collect approved features (including any edits)
    const approvedFeatures = collectApprovedFeatures();
    const approvedDesignSpecs = collectApprovedDesignSpecs();
    const userRequirements = elements.userRequirementsInput?.value.trim() || null;

    try {
        const response = await fetch(`${API_BASE}/build/${currentTaskId}/approve-features`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                approved_features: approvedFeatures,
                approved_design_specs: approvedDesignSpecs,
                user_requirements: userRequirements
            })
        });

        const data = await response.json();

        if (response.ok) {
            addLog('✅ Features approved! Moving to tech stack review...', 'success');
            approvalState.features_approved = true;

            // Hide feature approval UI
            elements.featureApprovalBanner?.classList.add('hidden');
            elements.featureApprovalActions?.classList.add('hidden');

            // Reconnect to stream for phase 2
            connectToStream(currentTaskId);
        } else {
            addLog(`Error: ${data.detail}`, 'error');
        }
    } catch (error) {
        addLog(`Error: ${error.message}`, 'error');
    }
}


async function generateStructure() {
    if (!currentTaskId) return;

    const techStackInput = document.getElementById('tech-stack-input');
    const newTechStack = techStackInput.value.trim();

    if (!newTechStack) {
        addLog('⚠️ Please enter a tech stack first.', 'warning');
        return;
    }

    const btn = elements.generateStructureBtn;
    const originalContent = btn.innerHTML;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Generating...';
    btn.disabled = true;

    addLog(`Generating file structure for: ${newTechStack}...`, 'info');

    try {
        const response = await fetch(`${API_BASE}/build/${currentTaskId}/generate-structure`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                tech_stack: newTechStack
            })
        });

        const data = await response.json();

        if (response.ok) {
            blueprintData.file_structure = data.file_structure;
            renderEditableFileStructure();
            addLog('✅ File structure updated successfully!', 'success');
        } else {
            addLog(`Error: ${data.detail}`, 'error');
        }
    } catch (error) {
        addLog(`Error: ${error.message}`, 'error');
    } finally {
        btn.innerHTML = originalContent;
        btn.disabled = false;
    }
}

async function approveTechstack() {
    if (!currentTaskId) return;

    addLog('Submitting tech stack approval...', 'info');

    // Collect approved tech stack from input field
    const techStackInput = document.getElementById('tech-stack-input');
    const selectedStack = techStackInput?.value.trim() || blueprintData.tech_stack;
    const approvedFileStructure = collectApprovedFileStructure();
    const approvedAssetManifest = blueprintData.asset_manifest;
    const userRequirements = elements.userRequirementsInput?.value.trim() || null;

    try {
        const response = await fetch(`${API_BASE}/build/${currentTaskId}/approve-techstack`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                approved_tech_stack: selectedStack,
                approved_file_structure: approvedFileStructure,
                approved_asset_manifest: approvedAssetManifest,
                user_requirements: userRequirements
            })
        });

        const data = await response.json();

        if (response.ok) {
            addLog('✅ Tech stack approved! Starting code generation...', 'success');
            addLog('🚀 Building with YOUR approved specifications...', 'info');
            approvalState.techstack_approved = true;

            // Hide tech stack approval UI
            elements.techstackApprovalBanner?.classList.add('hidden');
            elements.techstackApprovalActions?.classList.add('hidden');
            elements.techStackOptions?.classList.add('hidden');

            // Switch to logs tab for build progress
            switchTab('logs');

            // Reconnect to stream for phase 3
            connectToStream(currentTaskId);
        } else {
            addLog(`Error: ${data.detail}`, 'error');
        }
    } catch (error) {
        addLog(`Error: ${error.message}`, 'error');
    }
}

function collectApprovedFeatures() {
    // Check for editable cards first (whether in edit mode or not)
    const editableCards = document.querySelectorAll('.feature-card[data-editable="true"]');

    if (editableCards.length > 0) {
        const features = [];
        editableCards.forEach(card => {
            const nameInput = card.querySelector('.feature-name-input');
            const descInput = card.querySelector('.feature-desc-input');
            
            // If in edit mode (has inputs), read from inputs
            if (nameInput && nameInput.value.trim()) {
                const priority = card.dataset.priority || 'core';
                features.push({
                    name: nameInput.value.trim(),
                    description: descInput?.value.trim() || '',
                    priority: priority,
                    user_benefit: ''
                });
            } else {
                // Not in edit mode, read from rendered card content
                const nameSpan = card.querySelector('.feature-name');
                const descPara = card.querySelector('.feature-description');
                const priority = card.dataset.priority || 'core';
                
                if (nameSpan && nameSpan.textContent.trim()) {
                    features.push({
                        name: nameSpan.textContent.trim(),
                        description: descPara?.textContent.trim() || '',
                        priority: priority,
                        user_benefit: ''
                    });
                }
            }
        });
        if (features.length > 0) {
            return features;
        }
    }

    // If no editable cards or edit mode, return blueprint features
    return blueprintData.project_features || [];
}

function collectApprovedDesignSpecs() {
    // Check if design inputs are visible and have values
    const colorInput = document.getElementById('spec-color-input');
    const typographyInput = document.getElementById('spec-typography-input');
    const layoutInput = document.getElementById('spec-layout-input');
    const animationsInput = document.getElementById('spec-animations-input');

    // Collect from inputs if they exist and are visible (not just in edit mode)
    if (colorInput && !colorInput.classList.contains('hidden')) {
        return {
            color_scheme: colorInput.value.trim() || blueprintData.design_specs?.color_scheme || '',
            typography: typographyInput?.value.trim() || blueprintData.design_specs?.typography || '',
            layout: layoutInput?.value.trim() || blueprintData.design_specs?.layout || '',
            animations: animationsInput?.value.trim() || blueprintData.design_specs?.animations || ''
        };
    }
    return blueprintData.design_specs || {};
}

function toggleEditMode() {
    isEditMode = !isEditMode;

    const editBtn = elements.editFeaturesBtn;
    if (isEditMode) {
        editBtn.innerHTML = '<i class="fa-solid fa-check"></i> Done Editing';
        enableEditMode();
    } else {
        editBtn.innerHTML = '<i class="fa-solid fa-pen"></i> Edit Features';
        disableEditMode();
    }
}

function enableEditMode() {
    // Make design spec inputs visible
    document.querySelectorAll('.spec-input').forEach(input => {
        input.classList.remove('hidden');
        const valueSpan = input.parentElement.querySelector('.spec-value');
        if (valueSpan) {
            input.value = valueSpan.textContent;
            valueSpan.classList.add('hidden');
        }
    });

    // Make feature cards editable
    const container = document.getElementById('features-container');
    const features = blueprintData.project_features || [];

    container.innerHTML = '';

    features.forEach((feature, index) => {
        const card = createEditableFeatureCard(feature, index);
        container.appendChild(card);
    });
}

function disableEditMode() {
    // Hide design spec inputs
    document.querySelectorAll('.spec-input').forEach(input => {
        const valueSpan = input.parentElement.querySelector('.spec-value');
        if (valueSpan) {
            valueSpan.textContent = input.value || valueSpan.textContent;
            valueSpan.classList.remove('hidden');
        }
        input.classList.add('hidden');
    });

    // Collect edited features and update blueprintData to persist changes
    const updatedFeatures = collectApprovedFeatures();
    blueprintData.project_features = updatedFeatures;

    // Re-render features as cards
    renderProjectFeatures(updatedFeatures);
}

function createEditableFeatureCard(feature, index) {
    const card = document.createElement('div');
    card.className = `feature-card ${feature.priority || 'core'}`;
    card.dataset.editable = 'true';
    card.dataset.priority = feature.priority || 'core';

    card.innerHTML = `
        <div class="feature-header">
            <input type="text" class="feature-name-input" value="${feature.name || ''}" placeholder="Feature name">
            <button class="remove-feature-btn" onclick="this.closest('.feature-card').remove()">
                <i class="fa-solid fa-times"></i>
            </button>
        </div>
        <textarea class="feature-desc-input" placeholder="Feature description">${feature.description || ''}</textarea>
        <div class="priority-toggle">
            <label>
                <input type="radio" name="priority-${index}" value="core" ${feature.priority === 'core' ? 'checked' : ''}>
                Core
            </label>
            <label>
                <input type="radio" name="priority-${index}" value="enhancement" ${feature.priority === 'enhancement' ? 'checked' : ''}>
                Enhancement
            </label>
        </div>
    `;

    // Update priority on change
    card.querySelectorAll('input[type="radio"]').forEach(radio => {
        radio.addEventListener('change', () => {
            card.dataset.priority = radio.value;
            card.className = `feature-card ${radio.value}`;
        });
    });

    return card;
}

function addNewFeature() {
    // Auto-enable edit mode if not already enabled
    if (!isEditMode) {
        toggleEditMode();
    }

    const container = document.getElementById('features-container');
    const index = container.children.length;
    const newFeature = { name: '', description: '', priority: 'enhancement' };
    const card = createEditableFeatureCard(newFeature, index);
    container.appendChild(card);

    // Focus on the name input
    card.querySelector('.feature-name-input')?.focus();

    addLog('✏️ New feature added - fill in the details', 'info');
}

async function checkFinalStatus(taskId) {
    try {
        const response = await fetch(`${API_BASE}/build/${taskId}/status`);
        const data = await response.json();

        if (data.is_complete) {
            if (data.zip_file_path) {
                showResult(taskId);
            } else if (data.error_message) {
                updateOutputError(data.error_message);
            }
        } else if (data.waiting_for_approval) {
            handleApprovalCheckpoint(data.approval_stage);
        }
    } catch (error) {
        addLog(`Status check failed: ${error.message}`, 'error');
    }
}

function showResult(taskId) {
    switchTab('output');
    elements.outputIcon.classList.remove('pending');
    elements.outputIcon.classList.add('success');
    elements.outputIcon.innerHTML = '<i class="fa-solid fa-check"></i>';
    elements.outputTitle.textContent = 'Build Complete!';
    elements.outputMessage.textContent = 'Your project was built with YOUR approved specifications.';
    elements.downloadSection.classList.remove('hidden');
    elements.downloadBtn.href = `${API_BASE}/build/${taskId}/download`;
    addLog('✅ Build complete! Download ready.', 'success');
}

function updateOutputError(errorMessage) {
    switchTab('output');
    elements.outputIcon.classList.remove('pending');
    elements.outputIcon.classList.add('error');
    elements.outputIcon.innerHTML = '<i class="fa-solid fa-xmark"></i>';
    elements.outputTitle.textContent = 'Build Failed';
    elements.outputMessage.textContent = errorMessage || 'An error occurred during the build process.';
}

function updatePlanningTab() {
    // Classification
    if (blueprintData.classification) {
        const classValue = document.getElementById('classification-value');
        if (classValue.textContent !== blueprintData.classification) {
            classValue.textContent = blueprintData.classification;
            classValue.className = `value ${blueprintData.classification.toLowerCase()}`;
        }
    }

    // Design specs - only render once
    if (blueprintData.design_specs && !renderedState.designSpecs) {
        renderDesignSpecs(blueprintData.design_specs);
        renderedState.designSpecs = true;
    }

    // Project features - only render once or if count changes
    if (blueprintData.project_features && blueprintData.project_features.length > 0) {
        const featureCount = blueprintData.project_features.length;
        if (!renderedState.features || renderedState.lastFeatureCount !== featureCount) {
            renderProjectFeatures(blueprintData.project_features);
            renderedState.features = true;
            renderedState.lastFeatureCount = featureCount;
        }
    }

    // Reasoning
    if (blueprintData.reasoning) {
        const reasoningEl = document.getElementById('reasoning-value');
        if (reasoningEl.textContent !== blueprintData.reasoning) {
            reasoningEl.textContent = blueprintData.reasoning;
        }
    }
}

function renderDesignSpecs(specs) {
    if (specs.color_scheme) {
        document.getElementById('spec-color-value').textContent = specs.color_scheme;
        document.getElementById('spec-color-input').value = specs.color_scheme;
    }
    if (specs.typography) {
        document.getElementById('spec-typography-value').textContent = specs.typography;
        document.getElementById('spec-typography-input').value = specs.typography;
    }
    if (specs.layout) {
        document.getElementById('spec-layout-value').textContent = specs.layout;
        document.getElementById('spec-layout-input').value = specs.layout;
    }
    if (specs.animations) {
        document.getElementById('spec-animations-value').textContent = specs.animations;
        document.getElementById('spec-animations-input').value = specs.animations;
    }
}

function renderProjectFeatures(features) {
    const container = document.getElementById('features-container');
    container.innerHTML = '';

    const coreFeatures = features.filter(f => f.priority === 'core');
    const enhancementFeatures = features.filter(f => f.priority === 'enhancement');

    if (coreFeatures.length > 0) {
        const coreSection = document.createElement('div');
        coreSection.className = 'feature-group';
        coreSection.innerHTML = '<h5 class="feature-group-title core"><i class="fa-solid fa-star"></i> Core Features</h5>';
        coreFeatures.forEach(f => coreSection.appendChild(createFeatureCard(f, 'core')));
        container.appendChild(coreSection);
    }

    if (enhancementFeatures.length > 0) {
        const enhSection = document.createElement('div');
        enhSection.className = 'feature-group';
        enhSection.innerHTML = '<h5 class="feature-group-title enhancement"><i class="fa-solid fa-sparkles"></i> Enhancements</h5>';
        enhancementFeatures.forEach(f => enhSection.appendChild(createFeatureCard(f, 'enhancement')));
        container.appendChild(enhSection);
    }
}

function createFeatureCard(feature, priority) {
    const card = document.createElement('div');
    card.className = `feature-card ${priority}`;
    card.dataset.priority = priority;
    card.dataset.editable = 'true'; // Mark so collectApprovedFeatures can read it
    card.innerHTML = `
        <div class="feature-header">
            <span class="feature-name">${feature.name}</span>
        </div>
        <p class="feature-description">${feature.description}</p>
        ${feature.user_benefit ? `<p class="feature-benefit"><i class="fa-solid fa-heart"></i> ${feature.user_benefit}</p>` : ''}
    `;
    return card;
}

function updateTechnicalTab() {
    // Tech stack - only update if changed
    if (blueprintData.tech_stack && !renderedState.techStack) {
        const techValue = document.getElementById('tech-stack-value');
        techValue.textContent = formatTechStack(blueprintData.tech_stack);
        techValue.className = 'tech-badge active';
        renderedState.techStack = true;
    }

    // File structure - only render once
    if (blueprintData.file_structure && blueprintData.file_structure.length > 0 && !renderedState.fileStructure) {
        const fileTree = document.getElementById('file-tree');
        fileTree.innerHTML = '';
        blueprintData.file_structure.forEach(file => {
            const li = document.createElement('li');
            li.innerHTML = `
                <i class="fa-solid ${getFileIcon(file.type)}"></i>
                <span class="file-name">${file.name}</span>
                <span class="file-purpose">${file.purpose || ''}</span>
            `;
            fileTree.appendChild(li);
        });
        renderedState.fileStructure = true;
    }

    // Assets - only render once
    if (blueprintData.asset_manifest && blueprintData.asset_manifest.length > 0 && !renderedState.assets) {
        const assetsList = document.getElementById('assets-list');
        assetsList.innerHTML = '';
        blueprintData.asset_manifest.forEach(asset => {
            const div = document.createElement('div');
            div.className = 'asset-item';
            div.innerHTML = `
                <i class="fa-solid fa-cube"></i>
                <span class="asset-name">${asset.name}</span>
                <a href="${asset.url}" target="_blank" class="asset-link">
                    <i class="fa-solid fa-external-link"></i>
                </a>
            `;
            assetsList.appendChild(div);
        });
        renderedState.assets = true;
    }
}

function formatTechStack(stack) {
    return techStackDescriptions[stack] || stack;
}

function formatNodeName(node) {
    const names = {
        'gatekeeper': 'Scope Analysis',
        'scope_gatekeeper': 'Scope Analysis',
        'architect': 'Blueprint Design',
        'feature_approval_checkpoint': 'Awaiting Feature Approval',
        'techstack_approval_checkpoint': 'Awaiting Tech Stack Approval',
        'builder': 'Code Generation',
        'syntax_guard': 'Syntax Validation',
        'auditor': 'Semantic Audit',
        'packager': 'Packaging'
    };
    return names[node] || node;
}

function getFileIcon(fileType) {
    const icons = {
        'html': 'fa-file-code',
        'css': 'fa-file-code',
        'js': 'fa-file-code',
        'json': 'fa-file-code',
        'default': 'fa-file'
    };
    return icons[fileType] || icons.default;
}

function updateProgress(activeNode) {
    // Map nodes to step data-attributes
    const nodeToStep = {
        'gatekeeper': 'gatekeeper',
        'scope_gatekeeper': 'gatekeeper',
        'architect': 'architect',
        'feature_approval_checkpoint': 'feature_approval',
        'feature_approved': 'feature_approval',
        'techstack_approval_checkpoint': 'techstack_approval',
        'techstack_approved': 'techstack_approval',
        'builder': 'builder',
        'syntax_guard': 'builder',
        'auditor': 'builder',
        'packager': 'packager'
    };

    const targetStep = nodeToStep[activeNode] || activeNode;

    elements.steps.forEach(step => {
        step.classList.remove('active', 'completed', 'waiting');
        const stepName = step.dataset.step;

        if (stepName === targetStep) {
            if (activeNode.includes('checkpoint')) {
                step.classList.add('waiting');
            } else {
                step.classList.add('active');
            }
        }
    });
}

function addLog(message, type = "info") {
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    entry.textContent = `> ${message}`;
    elements.logsContainer.appendChild(entry);
    elements.logsContainer.scrollTop = elements.logsContainer.scrollHeight;
}

function resetTabContent() {
    // Reset blueprint data
    blueprintData = {
        tech_stack: null,
        file_structure: [],
        asset_manifest: [],
        reasoning: null,
        classification: null,
        project_features: [],
        design_specs: null
    };

    // Reset approval state
    approvalState = { features_approved: false, techstack_approved: false };
    isEditMode = false;
    currentTaskId = null;

    // Reset Planning Tab
    document.getElementById('classification-value').textContent = 'Analyzing...';
    document.getElementById('classification-value').className = 'value';
    document.getElementById('spec-color-value').textContent = 'Analyzing palette...';
    document.getElementById('spec-typography-value').textContent = 'Selecting fonts...';
    document.getElementById('spec-layout-value').textContent = 'Planning structure...';
    document.getElementById('spec-animations-value').textContent = 'Designing interactions...';
    document.getElementById('features-container').innerHTML = `
        <div class="feature-placeholder">
            <i class="fa-solid fa-spinner fa-spin"></i>
            Features will appear after analysis...
        </div>
    `;
    document.getElementById('reasoning-value').textContent = 'Waiting for blueprint...';

    // Reset Technical Tab
    document.getElementById('tech-stack-value').textContent = '—';
    document.getElementById('tech-stack-value').className = 'tech-badge';
    document.getElementById('file-tree').innerHTML = '';
    document.getElementById('assets-list').innerHTML = '<span class="no-assets">No external dependencies</span>';

    // Reset Logs
    elements.logsContainer.innerHTML = `
        <div class="log-entry system">> System initialized with HITL workflow...</div>
        <div class="log-entry system">> Waiting for your approvals at each stage...</div>
    `;

    // Reset Output
    elements.outputIcon.className = 'icon-circle pending';
    elements.outputIcon.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
    elements.outputTitle.textContent = 'Waiting for Approvals...';
    elements.outputMessage.textContent = 'Complete the approval steps to start code generation.';
    elements.downloadSection.classList.add('hidden');

    // Hide approval UI elements
    elements.featureApprovalBanner?.classList.add('hidden');
    elements.techstackApprovalBanner?.classList.add('hidden');
    elements.featureApprovalActions?.classList.add('hidden');
    elements.techstackApprovalActions?.classList.add('hidden');
    elements.userRequirementsSection?.classList.add('hidden');
    elements.techStackOptions?.classList.add('hidden');
    elements.featuresEditableBadge?.classList.add('hidden');
    elements.designEditableBadge?.classList.add('hidden');
    elements.addFeatureBtn?.classList.add('hidden');

    // Reset steps
    elements.steps.forEach(step => {
        step.classList.remove('active', 'completed', 'waiting');
    });
    elements.steps[0].classList.add('active');

    // Reset tabs
    switchTab('planning');
}

function resetUI() {
    resetTabContent();
    elements.progressSection.classList.add('hidden');
    elements.inputSection.classList.remove('hidden');
    elements.userPrompt.value = '';
    elements.refUrl.value = '';
    if (elements.userRequirementsInput) {
        elements.userRequirementsInput.value = '';
    }
}