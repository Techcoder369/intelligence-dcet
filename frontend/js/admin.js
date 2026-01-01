/**
 * Admin Dashboard JavaScript
 * Handles admin analytics, subject management, and PDF upload
 */

let currentTab = 'dashboard';

document.addEventListener('DOMContentLoaded', async function() {
    if (!requireAdmin()) return;

    setupNavigation();
    await loadDashboard();
});

function setupNavigation() {
    document.querySelectorAll('.admin-nav-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const tab = this.dataset.tab;
            switchTab(tab);
        });
    });
}

function switchTab(tab) {
    currentTab = tab;
    
    document.querySelectorAll('.admin-nav-link').forEach(link => {
        link.classList.toggle('active', link.dataset.tab === tab);
    });
    
    document.querySelectorAll('.admin-section').forEach(section => {
        section.classList.toggle('hidden', section.id !== `${tab}Section`);
    });
    
    switch(tab) {
        case 'dashboard':
            loadDashboard();
            break;
        case 'subjects':
            loadSubjects();
            break;
        case 'upload':
            loadUploadSection();
            break;
        case 'documents':
            loadDocuments();
            break;
    }
}

async function loadDashboard() {
    const result = await AdminAPI.getAnalytics();

    if (result.success) {
        const analytics = result.analytics;
        
        document.getElementById('totalStudents').textContent = analytics.total_students;
        document.getElementById('totalQuizzes').textContent = analytics.total_quizzes;
        document.getElementById('totalFlashcards').textContent = analytics.total_flashcard_sessions;
        document.getElementById('totalDocuments').textContent = analytics.total_documents;
        
        const subjectStatsContainer = document.getElementById('subjectStatsTable');
        subjectStatsContainer.innerHTML = analytics.subjects.map(subject => `
            <tr>
                <td>${subject.subject_name}</td>
                <td>${subject.quiz_count}</td>
                <td>${subject.flashcard_count}</td>
                <td>${subject.units.reduce((sum, u) => sum + u.document_count, 0)}</td>
            </tr>
        `).join('');
    }
}

async function loadSubjects() {
    const result = await AdminAPI.getSubjects();

    if (result.success) {
        const container = document.getElementById('subjectsList');
        
        container.innerHTML = result.subjects.map(subject => `
            <div class="card" style="margin-bottom: 1rem;">
                <h3>${subject.name} (${subject.short_name})</h3>
                <p style="color: var(--gray-500);">${subject.description}</p>
                <div style="margin-top: 1rem;">
                    <strong>Units:</strong>
                    <div style="display: flex; gap: 0.5rem; flex-wrap: wrap; margin-top: 0.5rem;">
                        ${subject.units.map(unit => `
                            <span style="padding: 0.25rem 0.75rem; background: var(--gray-100); border-radius: var(--radius); font-size: 0.9rem;">
                                ${unit.name} (${unit.document_count} docs)
                            </span>
                        `).join('')}
                    </div>
                </div>
            </div>
        `).join('');
    }
}

async function loadUploadSection() {
    const result = await AdminAPI.getSubjects();

    if (result.success) {
        const subjectSelect = document.getElementById('uploadSubject');
        subjectSelect.innerHTML = '<option value="">Select Subject</option>' + 
            result.subjects.map(s => `<option value="${s.id}">${s.name}</option>`).join('');
        
        subjectSelect.addEventListener('change', function() {
            const subjectId = this.value;
            const subject = result.subjects.find(s => s.id == subjectId);
            const unitSelect = document.getElementById('uploadUnit');
            
            if (subject) {
                unitSelect.innerHTML = '<option value="">Select Unit</option>' + 
                    subject.units.map(u => `<option value="${u.id}">${u.name}</option>`).join('');
                unitSelect.disabled = false;
            } else {
                unitSelect.innerHTML = '<option value="">Select Unit</option>';
                unitSelect.disabled = true;
            }
        });
    }
}

async function loadDocuments() {
    const result = await AdminAPI.getDocuments();

    if (result.success) {
        const container = document.getElementById('documentsList');
        
        if (result.documents.length === 0) {
            container.innerHTML = '<tr><td colspan="5" style="text-align: center;">No documents uploaded yet</td></tr>';
            return;
        }
        
        container.innerHTML = result.documents.map(doc => `
            <tr>
                <td>${doc.filename}</td>
                <td>${doc.subject_name}</td>
                <td>${doc.unit_name}</td>
                <td>${doc.chunk_count} chunks</td>
                <td>
                    <button class="btn btn-danger btn-sm" onclick="deleteDocument(${doc.id})">Delete</button>
                </td>
            </tr>
        `).join('');
    }
}

const uploadZone = document.getElementById('uploadZone');
const fileInput = document.getElementById('fileInput');

uploadZone.addEventListener('click', () => fileInput.click());

uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadZone.classList.add('dragover');
});

uploadZone.addEventListener('dragleave', () => {
    uploadZone.classList.remove('dragover');
});

uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('dragover');
    handleFiles(e.dataTransfer.files);
});

fileInput.addEventListener('change', () => {
    handleFiles(fileInput.files);
});

async function handleFiles(files) {
    const subjectId = document.getElementById('uploadSubject').value;
    const unitId = document.getElementById('uploadUnit').value;

    if (!subjectId || !unitId) {
        alert('Please select a subject and unit first');
        return;
    }

    for (const file of files) {
        if (!file.name.endsWith('.pdf')) {
            alert(`${file.name} is not a PDF file`);
            continue;
        }

        const formData = new FormData();
        formData.append('file', file);
        formData.append('subject_id', subjectId);
        formData.append('unit_id', unitId);

        uploadZone.innerHTML = `<div class="spinner"></div><p>Uploading ${file.name}...</p>`;

        const result = await AdminAPI.uploadDocument(formData);

        if (result.success) {
            uploadZone.innerHTML = `
                <div style="color: var(--success-color);">\u2713</div>
                <p>${result.message}</p>
            `;
            setTimeout(() => {
                uploadZone.innerHTML = `
                    <div class="upload-icon">\u{1F4C4}</div>
                    <p>Drag & drop PDF files here or click to browse</p>
                `;
            }, 3000);
        } else {
            uploadZone.innerHTML = `
                <div style="color: var(--danger-color);">\u2717</div>
                <p>${result.message}</p>
            `;
        }
    }
}

async function deleteDocument(docId) {
    if (!confirm('Are you sure you want to delete this document?')) return;
    
    const result = await AdminAPI.deleteDocument(docId);
    
    if (result.success) {
        loadDocuments();
    } else {
        alert(result.message || 'Failed to delete document');
    }
}

document.getElementById('adminLogout').addEventListener('click', function() {
    if (confirm('Are you sure you want to logout?')) {
        logout();
    }
});
