/**
 * STAC-CAPS Web Application
 * Main JavaScript for video upload, calibration, and processing
 */

// State
const state = {
    sessionId: null,
    calibration: {
        leftRail: [],
        rightRail: [],
        clickMode: 'left' // 'left' | 'right' | 'done'
    },
    ws: null,
    processing: false
};

// DOM Elements
const elements = {
    videoInput: document.getElementById('video-input'),
    uploadZone: document.getElementById('upload-zone'),
    uploadStatus: document.getElementById('upload-status'),
    calibrationSection: document.getElementById('calibration-section'),
    calibrationCanvas: document.getElementById('calibration-canvas'),
    calibrationInstruction: document.getElementById('calibration-instruction'),
    leftRailStatus: document.getElementById('left-rail-status'),
    rightRailStatus: document.getElementById('right-rail-status'),
    gaugeInput: document.getElementById('gauge-input'),
    calibrateBtn: document.getElementById('calibrate-btn'),
    processSection: document.getElementById('process-section'),
    processBtn: document.getElementById('process-btn'),
    progressContainer: document.getElementById('progress-container'),
    progressFill: document.getElementById('progress-fill'),
    progressText: document.getElementById('progress-text'),
    fpsText: document.getElementById('fps-text'),
    resultsSection: document.getElementById('results-section'),
    downloadVideoBtn: document.getElementById('download-video-btn'),
    downloadJsonBtn: document.getElementById('download-json-btn'),
    previewCanvas: document.getElementById('preview-canvas'),
    statusBadge: document.getElementById('status-badge'),
    ttcValue: document.getElementById('ttc-value'),
    objectsValue: document.getElementById('objects-value'),
    riskValue: document.getElementById('risk-value'),
    logContainer: document.getElementById('log-container'),
    connectionStatus: document.getElementById('connection-status')
};

// Initialize
document.addEventListener('DOMContentLoaded', init);

function init() {
    setupUploadHandlers();
    setupCalibrationHandlers();
    setupProcessingHandlers();
    checkModels();
}

// =============================================================================
// UPLOAD HANDLERS
// =============================================================================

function setupUploadHandlers() {
    // File input change
    elements.videoInput.addEventListener('change', handleFileSelect);

    // Drag and drop
    elements.uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        elements.uploadZone.classList.add('dragover');
    });

    elements.uploadZone.addEventListener('dragleave', () => {
        elements.uploadZone.classList.remove('dragover');
    });

    elements.uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        elements.uploadZone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            handleFileUpload(e.dataTransfer.files[0]);
        }
    });
}

function handleFileSelect(e) {
    if (e.target.files.length > 0) {
        handleFileUpload(e.target.files[0]);
    }
}

async function handleFileUpload(file) {
    elements.uploadStatus.textContent = `Subiendo ${file.name}...`;
    addLog(`Subiendo video: ${file.name}`);

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Error: ${response.status}`);
        }

        const data = await response.json();
        state.sessionId = data.session_id;

        elements.uploadStatus.textContent = `✓ Video cargado (${data.total_frames} frames, ${data.fps.toFixed(1)} FPS)`;
        addLog(`Video cargado: ${data.total_frames} frames`);

        // Load first frame for calibration
        await loadFirstFrame(data.first_frame_url);

        // Show calibration section
        elements.calibrationSection.style.display = 'block';

    } catch (error) {
        elements.uploadStatus.textContent = `✗ Error: ${error.message}`;
        addLog(`Error: ${error.message}`, 'alert');
    }
}

async function loadFirstFrame(url) {
    const img = new Image();
    img.crossOrigin = 'anonymous';

    return new Promise((resolve, reject) => {
        img.onload = () => {
            const canvas = elements.calibrationCanvas;
            canvas.width = img.width;
            canvas.height = img.height;

            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0);

            // Store image for redrawing
            canvas.dataset.imageUrl = url;
            state.firstFrameImage = img;

            resolve();
        };
        img.onerror = reject;
        img.src = url;
    });
}

// =============================================================================
// CALIBRATION HANDLERS
// =============================================================================

function setupCalibrationHandlers() {
    elements.calibrationCanvas.addEventListener('click', handleCalibrationClick);
    elements.calibrateBtn.addEventListener('click', submitCalibration);
}

function handleCalibrationClick(e) {
    const canvas = elements.calibrationCanvas;
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;

    const x = Math.round((e.clientX - rect.left) * scaleX);
    const y = Math.round((e.clientY - rect.top) * scaleY);

    if (state.calibration.clickMode === 'left') {
        state.calibration.leftRail.push([x, y]);

        if (state.calibration.leftRail.length >= 2) {
            elements.leftRailStatus.textContent = '🟢 Riel Izquierdo';
            state.calibration.clickMode = 'right';
            elements.calibrationInstruction.textContent = 'Ahora haz clic en 2 puntos del riel DERECHO';
        } else {
            elements.calibrationInstruction.textContent = 'Clic en otro punto del riel izquierdo';
        }
    } else if (state.calibration.clickMode === 'right') {
        state.calibration.rightRail.push([x, y]);

        if (state.calibration.rightRail.length >= 2) {
            elements.rightRailStatus.textContent = '🟢 Riel Derecho';
            state.calibration.clickMode = 'done';
            elements.calibrationInstruction.textContent = '✓ Calibración lista';
            elements.calibrateBtn.disabled = false;
        } else {
            elements.calibrationInstruction.textContent = 'Clic en otro punto del riel derecho';
        }
    }

    // Redraw with markers
    redrawCalibration();
}

function redrawCalibration() {
    const canvas = elements.calibrationCanvas;
    const ctx = canvas.getContext('2d');

    // Redraw image
    if (state.firstFrameImage) {
        ctx.drawImage(state.firstFrameImage, 0, 0);
    }

    // Draw left rail points (red)
    ctx.fillStyle = '#ef4444';
    ctx.strokeStyle = '#ef4444';
    ctx.lineWidth = 2;

    state.calibration.leftRail.forEach((point, i) => {
        ctx.beginPath();
        ctx.arc(point[0], point[1], 8, 0, Math.PI * 2);
        ctx.fill();

        if (i > 0) {
            ctx.beginPath();
            ctx.moveTo(state.calibration.leftRail[i - 1][0], state.calibration.leftRail[i - 1][1]);
            ctx.lineTo(point[0], point[1]);
            ctx.stroke();
        }
    });

    // Draw right rail points (green)
    ctx.fillStyle = '#22c55e';
    ctx.strokeStyle = '#22c55e';

    state.calibration.rightRail.forEach((point, i) => {
        ctx.beginPath();
        ctx.arc(point[0], point[1], 8, 0, Math.PI * 2);
        ctx.fill();

        if (i > 0) {
            ctx.beginPath();
            ctx.moveTo(state.calibration.rightRail[i - 1][0], state.calibration.rightRail[i - 1][1]);
            ctx.lineTo(point[0], point[1]);
            ctx.stroke();
        }
    });

    // Draw gauge line between rails
    if (state.calibration.leftRail.length > 0 && state.calibration.rightRail.length > 0) {
        ctx.strokeStyle = '#3b82f6';
        ctx.setLineDash([5, 5]);
        ctx.beginPath();
        ctx.moveTo(state.calibration.leftRail[0][0], state.calibration.leftRail[0][1]);
        ctx.lineTo(state.calibration.rightRail[0][0], state.calibration.rightRail[0][1]);
        ctx.stroke();
        ctx.setLineDash([]);
    }
}

async function submitCalibration() {
    const gauge = parseFloat(elements.gaugeInput.value) || 1435;

    try {
        const response = await fetch(`/api/session/${state.sessionId}/calibrate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                left_rail: state.calibration.leftRail,
                right_rail: state.calibration.rightRail,
                track_gauge_mm: gauge
            })
        });

        if (!response.ok) {
            throw new Error(`Error: ${response.status}`);
        }

        addLog(`Calibración guardada (trocha: ${gauge}mm)`);

        // Show processing section
        elements.processSection.style.display = 'block';

    } catch (error) {
        addLog(`Error de calibración: ${error.message}`, 'alert');
    }
}

// =============================================================================
// PROCESSING HANDLERS
// =============================================================================

function setupProcessingHandlers() {
    elements.processBtn.addEventListener('click', startProcessing);
}

async function startProcessing() {
    elements.processBtn.disabled = true;
    elements.progressContainer.style.display = 'block';
    state.processing = true;

    addLog('Iniciando procesamiento...');

    try {
        // Start processing
        const response = await fetch(`/api/session/${state.sessionId}/process`, {
            method: 'POST'
        });

        if (!response.ok) {
            throw new Error(`Error: ${response.status}`);
        }

        const data = await response.json();

        // Connect WebSocket
        connectWebSocket();

    } catch (error) {
        addLog(`Error: ${error.message}`, 'alert');
        elements.processBtn.disabled = false;
    }
}

function connectWebSocket() {
    const wsUrl = `ws://${window.location.host}/ws/session/${state.sessionId}`;
    state.ws = new WebSocket(wsUrl);

    state.ws.onopen = () => {
        elements.connectionStatus.textContent = '🟢 Conectado';
        addLog('WebSocket conectado');
    };

    state.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
    };

    state.ws.onclose = () => {
        elements.connectionStatus.textContent = '🔴 Desconectado';
    };

    state.ws.onerror = (error) => {
        addLog('Error de WebSocket', 'alert');
    };
}

function handleWebSocketMessage(data) {
    switch (data.type) {
        case 'status':
            updateProgress(data);
            break;
        case 'frame':
            updatePreview(data);
            break;
        case 'alert':
            handleAlert(data);
            break;
        case 'complete':
            handleComplete(data);
            break;
        case 'error':
            addLog(`Error: ${data.message}`, 'alert');
            break;
    }
}

function updateProgress(data) {
    const percent = Math.round(data.progress * 100);
    elements.progressFill.style.width = `${percent}%`;
    elements.progressText.textContent = `${percent}%`;
    elements.fpsText.textContent = `${(data.fps || 0).toFixed(1)} FPS`;
}

function updatePreview(data) {
    // Update stats
    elements.ttcValue.textContent = data.ttc !== Infinity ? `${data.ttc.toFixed(1)}s` : '--';
    elements.objectsValue.textContent = data.objects_count || 0;
    elements.riskValue.textContent = `${Math.round((data.max_risk || 0) * 100)}%`;

    // Update status badge
    const action = data.action || 'CLEAR';
    elements.statusBadge.textContent = action;
    elements.statusBadge.className = `status-badge ${action.toLowerCase()}`;

    // Update 3D view
    if (window.updateThreeScene && data.objects_3d) {
        window.updateThreeScene(data.objects_3d);
    }
}

function handleAlert(data) {
    addLog(`⚠️ ALERTA: TTC=${data.ttc.toFixed(1)}s, Acción: ${data.action}`, 'warning');
}

function handleComplete(data) {
    state.processing = false;
    elements.progressFill.style.width = '100%';
    elements.progressText.textContent = '100%';

    addLog('✓ Procesamiento completado');

    // Show results section
    elements.resultsSection.style.display = 'block';
    elements.downloadVideoBtn.href = data.output_url;
    elements.downloadJsonBtn.href = data.results_url;
}

// =============================================================================
// UTILITIES
// =============================================================================

function addLog(message, type = 'info') {
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    elements.logContainer.insertBefore(entry, elements.logContainer.firstChild);

    // Limit to 50 entries
    while (elements.logContainer.children.length > 50) {
        elements.logContainer.removeChild(elements.logContainer.lastChild);
    }
}

async function checkModels() {
    try {
        const response = await fetch('/api/models/status');
        const data = await response.json();

        const missing = Object.entries(data)
            .filter(([_, info]) => !info.downloaded)
            .map(([name, _]) => name);

        if (missing.length > 0) {
            addLog(`Modelos faltantes: ${missing.join(', ')}`, 'warning');
            addLog('Descargando modelos automáticamente...');
            await fetch('/api/models/download', { method: 'POST' });
        } else {
            addLog('Todos los modelos disponibles');
        }
    } catch (error) {
        addLog(`Error verificando modelos: ${error.message}`);
    }
}
