// ==========================================================================
// MarkItDown Studio - Frontend Application Logic
// ==========================================================================

let appState = {
    mode: 'folder', // 'folder' | 'upload'
    localFiles: [],
    uploadedFiles: [],
    selectedExtensions: ['all'],
    outputFolder: '',
    results: {}, // filename -> result object
    isConverting: false,
    currentPreviewName: null,
    previewMode: 'rendered' // 'rendered' | 'raw'
};

// --- Inicialización ---
document.addEventListener('DOMContentLoaded', () => {
    setupDragAndDrop();
});

// --- Pestañas ---
function switchTab(mode) {
    appState.mode = mode;
    document.getElementById('tabFolderBtn').classList.toggle('active', mode === 'folder');
    document.getElementById('tabUploadBtn').classList.toggle('active', mode === 'upload');
    document.getElementById('tabUrlBtn').classList.toggle('active', mode === 'url');
    document.getElementById('panelFolder').classList.toggle('active', mode === 'folder');
    document.getElementById('panelUpload').classList.toggle('active', mode === 'upload');
    document.getElementById('panelUrl').classList.toggle('active', mode === 'url');
    updateTableAndStats();
}

// --- Filtros de Extensión ---
function toggleExtensionPill(btn, ext) {
    const pills = document.querySelectorAll('#filterPills .pill');
    if (ext === 'all') {
        pills.forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        appState.selectedExtensions = ['all'];
    } else {
        // Deseleccionar "Todos"
        document.querySelector('#filterPills .pill[data-ext="all"]').classList.remove('active');
        btn.classList.toggle('active');

        const activePills = Array.from(document.querySelectorAll('#filterPills .pill.active'))
            .map(p => p.getAttribute('data-ext'))
            .filter(e => e !== 'all');

        if (activePills.length === 0) {
            document.querySelector('#filterPills .pill[data-ext="all"]').classList.add('active');
            appState.selectedExtensions = ['all'];
        } else {
            appState.selectedExtensions = activePills;
        }
    }

    // Si ya hay una carpeta escaneada, re-escanear con el nuevo filtro
    const folderPath = document.getElementById('inputFolderPath').value.trim();
    if (folderPath && appState.mode === 'folder') {
        scanFolder(folderPath);
    }
}

// --- Explorador Nativo (Local) ---
async function browseInputFolder() {
    try {
        const res = await fetch('/api/dialog/select-folder', { method: 'POST' });
        const data = await res.json();
        if (data.path) {
            document.getElementById('inputFolderPath').value = data.path;
            await scanFolder(data.path);
        } else {
            showToast("Para seleccionar archivos en la versión web, usa 'Arrastrar y Soltar' o la pestaña Drag & Drop.", true);
        }
    } catch (err) {
        showToast("Para seleccionar archivos en la versión web, usa 'Arrastrar y Soltar'.", true);
    }
}

async function browseInputFiles() {
    try {
        const res = await fetch('/api/dialog/select-files', { method: 'POST' });
        const data = await res.json();
        if (data.files && data.files.length > 0) {
            appState.localFiles = data.files.map(filePath => {
                const name = filePath.split(/[\\/]/).pop();
                const ext = '.' + name.split('.').pop().toLowerCase();
                return {
                    name: name,
                    path: filePath,
                    rel_path: name,
                    size_bytes: 0,
                    size_formatted: 'Local',
                    extension: ext
                };
            });
            updateTableAndStats();
            showToast(`${data.files.length} archivo(s) seleccionado(s)`);
        } else {
            document.getElementById('browserFileInput').click();
        }
    } catch (err) {
        document.getElementById('browserFileInput').click();
    }
}

async function browseOutputFolder() {
    try {
        showToast("Abriendo selector de carpeta de destino...");
        const res = await fetch('/api/dialog/select-folder', { method: 'POST' });
        const data = await res.json();
        if (data.path) {
            document.getElementById('outputFolderPath').value = data.path;
            appState.outputFolder = data.path;
            showToast("Carpeta destino seleccionada con éxito");
        }
    } catch (err) {
        showToast("Error al abrir diálogo de destino", true);
    }
}

// --- Escanear Carpeta Local ---
async function scanFolder(folderPath) {
    const isRecursive = document.getElementById('chkRecursive').checked;
    const exts = appState.selectedExtensions.includes('all') ? null : appState.selectedExtensions;

    try {
        showToast("Escaneando archivos en la carpeta...");
        const res = await fetch('/api/scan-folder', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                folder_path: folderPath,
                recursive: isRecursive,
                extensions: exts
            })
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Error al escanear la carpeta');
        }

        const data = await res.json();
        appState.localFiles = data.files || [];
        updateTableAndStats();
        showToast(`Se encontraron ${data.total_files} archivo(s) compatibles`);
    } catch (err) {
        showToast(err.message, true);
    }
}

// Detectar Enter en el campo de texto de ruta
document.getElementById('inputFolderPath')?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        const val = e.target.value.trim();
        if (val) scanFolder(val);
    }
});

document.getElementById('chkRecursive')?.addEventListener('change', () => {
    const val = document.getElementById('inputFolderPath').value.trim();
    if (val && appState.mode === 'folder') scanFolder(val);
});

// --- Drag & Drop y Subida de Archivos ---
function setupDragAndDrop() {
    const dropzone = document.getElementById('dropzone');
    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove('dragover');
        }, false);
    });

    dropzone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFilesList(files);
    });
}

function handleDragOver(e) {
    e.preventDefault();
}

function handleDragLeave(e) {
    e.preventDefault();
}

function handleDrop(e) {
    e.preventDefault();
}

function handleBrowserFiles(e) {
    const files = e.target.files;
    handleFilesList(files);
}

function handleFilesList(fileList) {
    if (!fileList || fileList.length === 0) return;
    
    for (let i = 0; i < fileList.length; i++) {
        const file = fileList[i];
        // Evitar duplicados por nombre
        if (!appState.uploadedFiles.some(f => f.name === file.name)) {
            appState.uploadedFiles.push(file);
        }
    }
    updateTableAndStats();
    showToast(`${fileList.length} archivo(s) agregado(s) a la cola`);
}

// --- Renderizado de Tabla y Métricas ---
function updateTableAndStats() {
    const tbody = document.getElementById('filesTableBody');
    const emptyRow = document.getElementById('emptyRow');
    const countSelected = document.getElementById('countSelected');
    const totalSizeOriginal = document.getElementById('totalSizeOriginal');
    const tableCounter = document.getElementById('tableCounter');
    const btnConvert = document.getElementById('btnConvert');
    const btnClear = document.getElementById('btnClear');

    const files = appState.mode === 'folder' ? appState.localFiles : appState.uploadedFiles;
    const totalCount = files.length;

    countSelected.textContent = totalCount;
    tableCounter.textContent = `${totalCount} archivo${totalCount === 1 ? '' : 's'}`;
    btnConvert.disabled = totalCount === 0 || appState.isConverting;
    btnClear.disabled = totalCount === 0 || appState.isConverting;

    if (totalCount === 0) {
        tbody.innerHTML = `
            <tr class="empty-row" id="emptyRow">
                <td colspan="8">
                    <div class="empty-state">
                        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                            <circle cx="12" cy="12" r="10"></circle>
                            <line x1="12" y1="8" x2="12" y2="12"></line>
                            <line x1="12" y1="16" x2="12.01" y2="16"></line>
                        </svg>
                        <p>No hay archivos seleccionados aún. Elige una carpeta o arrastra documentos.</p>
                    </div>
                </td>
            </tr>`;
        totalSizeOriginal.textContent = '0 KB';
        document.getElementById('statSavingsBox').style.display = 'none';
        document.getElementById('statTokensBox').style.display = 'none';
        return;
    }

    let totalBytes = 0;
    let html = '';

    files.forEach((f, idx) => {
        const name = f.name;
        const sizeBytes = f.size || f.size_bytes || 0;
        totalBytes += sizeBytes;
        const sizeStr = f.size_formatted || formatBytesJS(sizeBytes);
        const ext = (name.split('.').pop() || '').toLowerCase();
        const badgeClass = getExtensionBadgeClass(ext);

        const res = appState.results[name];
        let statusHtml = '<span class="status-pill status-pending">Pendiente</span>';
        let mdSizeHtml = '-';
        let savingsHtml = '-';
        let tokensHtml = '-';
        let actionsHtml = '-';

        if (res) {
            if (res.success) {
                statusHtml = '<span class="status-pill status-success">✅ Listo</span>';
                mdSizeHtml = res.md_size_formatted || formatBytesJS(res.md_size_bytes);
                savingsHtml = `<span class="savings-badge">-${res.savings_pct}%</span>`;
                tokensHtml = `~${res.estimated_tokens.toLocaleString()}`;
                actionsHtml = `
                    <div class="table-actions">
                        <button onclick="openPreview('${encodeURIComponent(name)}')" title="Ver Vista Previa">👁️</button>
                        <button onclick="copyMarkdownDirect('${encodeURIComponent(name)}')" title="Copiar Markdown">📋</button>
                        <button onclick="downloadMarkdownDirect('${encodeURIComponent(name)}')" title="Descargar .md">⬇️</button>
                    </div>
                `;
            } else {
                statusHtml = `<span class="status-pill status-error" title="${res.error || 'Error'}">❌ Error</span>`;
                actionsHtml = `<small style="color:#f87171;">${res.error || 'Fallo'}</small>`;
            }
        }

        html += `
            <tr id="row-${idx}">
                <td class="file-name-cell" title="${name}"><strong>${name}</strong></td>
                <td><span class="ext-badge ${badgeClass}">.${ext}</span></td>
                <td>${sizeStr}</td>
                <td>${statusHtml}</td>
                <td>${mdSizeHtml}</td>
                <td>${savingsHtml}</td>
                <td>${tokensHtml}</td>
                <td>${actionsHtml}</td>
            </tr>
        `;
    });

    tbody.innerHTML = html;
    totalSizeOriginal.textContent = formatBytesJS(totalBytes);
}

function getExtensionBadgeClass(ext) {
    if (ext === 'pdf') return 'ext-pdf';
    if (['docx', 'doc'].includes(ext)) return 'ext-docx';
    if (['xlsx', 'xls', 'csv'].includes(ext)) return 'ext-xlsx';
    if (['pptx', 'ppt'].includes(ext)) return 'ext-pptx';
    if (['html', 'htm'].includes(ext)) return 'ext-html';
    return 'ext-default';
}

function formatBytesJS(bytes) {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function clearFileList() {
    appState.localFiles = [];
    appState.uploadedFiles = [];
    appState.results = {};
    document.getElementById('inputFolderPath').value = '';
    document.getElementById('statSavingsBox').style.display = 'none';
    document.getElementById('statTokensBox').style.display = 'none';
    document.getElementById('btnZip').style.display = 'none';
    document.getElementById('progressContainer').style.display = 'none';
    updateTableAndStats();
    showToast("Lista de archivos reiniciada");
}

// --- Iniciar Conversión ---
async function startConversion() {
    const files = appState.mode === 'folder' ? appState.localFiles : appState.uploadedFiles;
    if (files.length === 0) return;

    appState.isConverting = true;
    appState.outputFolder = document.getElementById('outputFolderPath').value.trim();
    
    const progressContainer = document.getElementById('progressContainer');
    const progressBarFill = document.getElementById('progressBarFill');
    const progressText = document.getElementById('progressText');
    const btnConvert = document.getElementById('btnConvert');

    progressContainer.style.display = 'block';
    progressBarFill.style.width = '10%';
    progressText.textContent = `Procesando ${files.length} archivo(s)...`;
    btnConvert.disabled = true;

    try {
        let resultsData = [];

        if (appState.mode === 'folder') {
            const filePaths = files.map(f => f.path);
            const res = await fetch('/api/convert/local', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    file_paths: filePaths,
                    output_folder: appState.outputFolder || null
                })
            });
            if (!res.ok) throw new Error('Error al procesar archivos locales');
            const data = await res.json();
            resultsData = data.results || [];
        } else {
            // Modo Upload (Drag & Drop)
            const formData = new FormData();
            files.forEach(f => formData.append('files', f));
            if (appState.outputFolder) {
                formData.append('output_folder', appState.outputFolder);
            }

            const res = await fetch('/api/convert/upload', {
                method: 'POST',
                body: formData
            });
            if (!res.ok) throw new Error('Error al procesar archivos subidos');
            const data = await res.json();
            resultsData = data.results || [];
        }

        // Mapear resultados al estado
        resultsData.forEach(r => {
            appState.results[r.name] = r;
        });

        progressBarFill.style.width = '100%';
        progressText.textContent = `¡Conversión completada! (${resultsData.filter(r => r.success).length}/${resultsData.length} exitosos)`;
        
        // Calcular estadísticas globales
        let totalOriginalBytes = 0;
        let totalMdBytes = 0;
        let totalTokens = 0;
        let successCount = 0;

        resultsData.forEach(r => {
            if (r.success) {
                totalOriginalBytes += r.original_size || 0;
                totalMdBytes += r.md_size_bytes || 0;
                totalTokens += r.estimated_tokens || 0;
                successCount++;
            }
        });

        if (successCount > 0) {
            const savingsPct = totalOriginalBytes > 0 
                ? Math.max(0, ((1 - (totalMdBytes / totalOriginalBytes)) * 100).toFixed(1))
                : 0;

            document.getElementById('statSavingsBox').style.display = 'flex';
            document.getElementById('totalSavingsPct').textContent = `-${savingsPct}%`;

            document.getElementById('statTokensBox').style.display = 'flex';
            document.getElementById('totalEstimatedTokens').textContent = totalTokens.toLocaleString();

            document.getElementById('btnZip').style.display = 'inline-flex';
        }

        updateTableAndStats();
        showToast(`Conversión finalizada con éxito.`);
    } catch (err) {
        showToast(err.message, true);
        progressText.textContent = "Ocurrió un error durante la conversión.";
    } finally {
        appState.isConverting = false;
        btnConvert.disabled = false;
    }
}

// --- Conversión Directa de URL (YouTube / Web) ---
async function convertUrlDirect() {
    const url = document.getElementById('inputUrl').value.trim();
    if (!url) {
        showToast("Ingresa una URL válida de YouTube o sitio web", true);
        return;
    }

    const progressContainer = document.getElementById('progressContainer');
    const progressBarFill = document.getElementById('progressBarFill');
    const progressText = document.getElementById('progressText');

    progressContainer.style.display = 'block';
    progressBarFill.style.width = '30%';
    progressText.textContent = `Descargando y convirtiendo: ${url}...`;

    try {
        const outFolder = document.getElementById('outputFolderPath').value.trim();
        const res = await fetch('/api/convert/url', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                url: url,
                output_folder: outFolder || null
            })
        });

        if (!res.ok) throw new Error('Error al procesar la URL');
        const data = await res.json();
        const result = data.results && data.results[0];

        if (!result || !result.success) {
            throw new Error(result?.error || 'No se pudo convertir el enlace');
        }

        appState.results[result.name] = result;
        if (!appState.uploadedFiles.some(f => f.name === result.name)) {
            appState.uploadedFiles.push({
                name: result.name,
                size: result.md_size_bytes,
                size_formatted: 'Video/Web'
            });
        }

        progressBarFill.style.width = '100%';
        progressText.textContent = `¡Conversión completada con éxito!`;

        document.getElementById('statSavingsBox').style.display = 'flex';
        document.getElementById('totalSavingsPct').textContent = `-90%`;
        document.getElementById('statTokensBox').style.display = 'flex';
        document.getElementById('totalEstimatedTokens').textContent = result.estimated_tokens.toLocaleString();
        document.getElementById('btnZip').style.display = 'inline-flex';

        updateTableAndStats();
        showToast("¡Contenido convertido exitosamente!");
        openPreview(encodeURIComponent(result.name));
    } catch (err) {
        showToast(err.message, true);
        progressText.textContent = "Error al procesar la URL.";
    }
}

// --- Vista Previa en Vivo (Live Preview Modal) ---
function openPreview(encodedName) {
    const name = decodeURIComponent(encodedName);
    const res = appState.results[name];
    if (!res || !res.markdown) {
        showToast("No hay contenido Markdown disponible para este archivo", true);
        return;
    }

    appState.currentPreviewName = name;
    document.getElementById('modalFileName').textContent = name;
    
    // Chips de metadatos
    const chipsContainer = document.getElementById('modalMetaChips');
    chipsContainer.innerHTML = `
        <span class="badge badge-muted">Original: ${res.original_size_formatted || formatBytesJS(res.original_size)}</span>
        <span class="badge badge-muted">Markdown: ${res.md_size_formatted || formatBytesJS(res.md_size_bytes)}</span>
        <span class="badge badge-online">Ahorro: -${res.savings_pct}%</span>
        <span class="badge badge-muted">Tokens: ~${res.estimated_tokens.toLocaleString()}</span>
    `;

    // Cargar contenido
    document.getElementById('rawMarkdownPreview').value = res.markdown;
    
    // Renderizado con marked
    const renderedContainer = document.getElementById('renderedPreview');
    if (window.marked) {
        renderedContainer.innerHTML = marked.parse(res.markdown);
    } else {
        renderedContainer.textContent = res.markdown;
    }

    setPreviewMode(appState.previewMode);
    document.getElementById('previewModal').style.display = 'flex';
}

function closePreviewModal() {
    document.getElementById('previewModal').style.display = 'none';
}

function setPreviewMode(mode) {
    appState.previewMode = mode;
    const btnRendered = document.getElementById('btnViewRendered');
    const btnRaw = document.getElementById('btnViewRaw');
    const renderedDiv = document.getElementById('renderedPreview');
    const rawTextarea = document.getElementById('rawMarkdownPreview');

    if (mode === 'rendered') {
        btnRendered.classList.add('active');
        btnRaw.classList.remove('active');
        renderedDiv.style.display = 'block';
        rawTextarea.style.display = 'none';
    } else {
        btnRaw.classList.add('active');
        btnRendered.classList.remove('active');
        renderedDiv.style.display = 'none';
        rawTextarea.style.display = 'block';
    }
}

// --- Copiar y Descargar Markdown ---
function copyModalMarkdown() {
    if (!appState.currentPreviewName) return;
    const res = appState.results[appState.currentPreviewName];
    if (res && res.markdown) {
        navigator.clipboard.writeText(res.markdown).then(() => {
            showToast("¡Markdown copiado al portapapeles!");
        }).catch(() => {
            showToast("Error al copiar al portapapeles", true);
        });
    }
}

function copyMarkdownDirect(encodedName) {
    const name = decodeURIComponent(encodedName);
    const res = appState.results[name];
    if (res && res.markdown) {
        navigator.clipboard.writeText(res.markdown).then(() => {
            showToast(`¡Markdown de "${name}" copiado!`);
        });
    }
}

function downloadModalMarkdown() {
    if (!appState.currentPreviewName) return;
    downloadMarkdownDirect(encodeURIComponent(appState.currentPreviewName));
}

function downloadMarkdownDirect(encodedName) {
    const name = decodeURIComponent(encodedName);
    const res = appState.results[name];
    if (res && res.markdown) {
        const stem = name.substring(0, name.lastIndexOf('.')) || name;
        const blob = new Blob([res.markdown], { type: 'text/markdown;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${stem}.md`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showToast(`Descargando ${stem}.md...`);
    }
}

function downloadAllZip() {
    window.location.href = '/api/download-zip';
    showToast("Generando y descargando paquete ZIP...");
}

// --- Sistema de Notificación Toast ---
let toastTimer = null;
function showToast(message, isError = false) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.style.borderColor = isError ? 'rgba(239, 68, 68, 0.4)' : 'rgba(56, 189, 248, 0.4)';
    toast.style.color = isError ? '#fca5a5' : '#f8fafc';
    toast.style.display = 'block';

    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
        toast.style.display = 'none';
    }, 3200);
}
