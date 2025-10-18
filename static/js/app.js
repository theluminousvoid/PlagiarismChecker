// API Base URL - используем относительные пути
const API_URL = '/api';

// State
let currentUser = null;
let allDocuments = [];

// ===== INIT =====
window.addEventListener('DOMContentLoaded', async () => {
    // Проверяем авторизацию
    try {
        const response = await fetch(`${API_URL}/me`, { credentials: 'include' });
        if (response.ok) {
            currentUser = await response.json();
            showMainPage();
        }
    } catch (error) {
        console.log('Не авторизован');
    }
});

// ===== AUTH =====
function showRegisterForm() {
    document.getElementById('loginForm').style.display = 'none';
    document.getElementById('registerForm').style.display = 'block';
}

function showLoginForm() {
    document.getElementById('registerForm').style.display = 'none';
    document.getElementById('loginForm').style.display = 'block';
}

async function register() {
    const username = document.getElementById('regUsername').value.trim();
    const password = document.getElementById('regPassword').value;
    const fullName = document.getElementById('regFullName').value.trim();
    
    if (!username || !password || !fullName) {
        alert('Заполните все поля');
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ username, password, full_name: fullName })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentUser = data.user;
            showMainPage();
        } else {
            alert(data.error || 'Ошибка регистрации');
        }
    } catch (error) {
        alert('Ошибка: ' + error.message);
    }
}

async function login() {
    const username = document.getElementById('loginUsername').value.trim();
    const password = document.getElementById('loginPassword').value;
    
    if (!username || !password) {
        alert('Введите логин и пароль');
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentUser = data.user;
            showMainPage();
        } else {
            alert(data.error || 'Ошибка входа');
        }
    } catch (error) {
        alert('Ошибка: ' + error.message);
    }
}

async function logout() {
    try {
        await fetch(`${API_URL}/logout`, {
            method: 'POST',
            credentials: 'include'
        });
        
        currentUser = null;
        document.getElementById('loginPage').style.display = 'flex';
        document.getElementById('mainPage').classList.remove('active');
        
        // Очистка форм
        document.getElementById('loginUsername').value = '';
        document.getElementById('loginPassword').value = '';
        showLoginForm();
    } catch (error) {
        console.error('Ошибка выхода:', error);
    }
}

function showMainPage() {
    document.getElementById('loginPage').style.display = 'none';
    document.getElementById('mainPage').classList.add('active');
    
    document.getElementById('userName').textContent = currentUser.full_name;
    const roleBadge = document.getElementById('userRole');
    roleBadge.textContent = currentUser.role === 'admin' ? 'Админ' : 'Пользователь';
    roleBadge.className = `badge ${currentUser.role === 'admin' ? 'badge-admin' : 'badge-user'}`;
    
    setupMenuForRole();
    renderDashboard();
}

function setupMenuForRole() {
    const sidebar = document.getElementById('sidebarMenu');
    sidebar.innerHTML = '';
    
    if (currentUser.role === 'user') {
        sidebar.innerHTML = `
            <div class="menu-item active" onclick="showSection('dashboard')">
                <span class="material-icons">dashboard</span>
                <span>Главная</span>
            </div>
            <div class="menu-item" onclick="showSection('upload')">
                <span class="material-icons">upload_file</span>
                <span>Загрузить</span>
            </div>
            <div class="menu-item" onclick="showSection('my-docs')">
                <span class="material-icons">article</span>
                <span>Мои документы</span>
            </div>
        `;
    } else {
        sidebar.innerHTML = `
            <div class="menu-item active" onclick="showSection('dashboard')">
                <span class="material-icons">dashboard</span>
                <span>Главная</span>
            </div>
            <div class="menu-item" onclick="showSection('check')">
                <span class="material-icons">spellcheck</span>
                <span>Проверить</span>
            </div>
            <div class="menu-item" onclick="showSection('database')">
                <span class="material-icons">storage</span>
                <span>Все документы</span>
            </div>
            <div class="menu-item" onclick="showSection('history')">
                <span class="material-icons">history</span>
                <span>История</span>
            </div>
            <div class="menu-item" onclick="showSection('analytics')">
                <span class="material-icons">analytics</span>
                <span>Аналитика</span>
            </div>
        `;
    }
}

// ===== NAVIGATION =====
function showSection(sectionId) {
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    document.getElementById(sectionId).classList.add('active');
    
    document.querySelectorAll('.menu-item').forEach(item => item.classList.remove('active'));
    event.target.closest('.menu-item').classList.add('active');
    
    if (sectionId === 'dashboard') renderDashboard();
    if (sectionId === 'my-docs') renderMyDocuments();
    if (sectionId === 'check') renderCheckPage();
    if (sectionId === 'database') renderAllDocuments();
    if (sectionId === 'history') renderHistory();
    if (sectionId === 'analytics') renderAnalyticsPage();
}

// ===== DASHBOARD =====
async function renderDashboard() {
    try {
        const response = await fetch(`${API_URL}/stats`, { credentials: 'include' });
        const stats = await response.json();
        
        let metricsHTML = '';
        
        if (currentUser.role === 'user') {
            metricsHTML = `
                <div class="metric-card">
                    <div class="metric-value">${stats.my_documents}</div>
                    <div class="metric-label">Мои документы</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${stats.total_documents}</div>
                    <div class="metric-label">Всего в системе</div>
                </div>
            `;
        } else {
            metricsHTML = `
                <div class="metric-card">
                    <div class="metric-value">${stats.total_documents}</div>
                    <div class="metric-label">Документов</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${stats.total_checks}</div>
                    <div class="metric-label">Проверок</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${stats.total_users}</div>
                    <div class="metric-label">Пользователей</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${stats.cache_stats.size}</div>
                    <div class="metric-label">Кэш</div>
                </div>
            `;
        }
        
        document.getElementById('metricsGrid').innerHTML = metricsHTML;
        
        document.getElementById('dashboardStats').innerHTML = `
            <div class="info-box">
                <h4>💾 Кэш (мемоизация - Лаба №3):</h4>
                <p>Размер: ${stats.cache_stats.size} записей</p>
                <p>Попаданий: ${stats.cache_stats.hits}</p>
                <p>Промахов: ${stats.cache_stats.misses}</p>
                <p>Эффективность: ${Math.round(stats.cache_stats.hit_rate * 100)}%</p>
            </div>
        `;
    } catch (error) {
        console.error('Ошибка:', error);
    }
}

// ===== UPLOAD (USER) =====
async function uploadDocument() {
    const title = document.getElementById('docTitle').value.trim();
    const text = document.getElementById('docText').value.trim();
    
    if (!title || !text) {
        alert('Заполните все поля');
        return;
    }
    
    const btn = event.target;
    btn.disabled = true;
    btn.innerHTML = '<div class="loading"></div> Загрузка...';
    
    try {
        const response = await fetch(`${API_URL}/documents`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ title, text })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            const docId = data.document.id;
            
            // Показываем успешную загрузку
            document.getElementById('uploadResult').innerHTML = `
                <div class="info-box" style="margin-top: 20px; background: rgba(16, 185, 129, 0.2); border-color: var(--success);">
                    <p style="color: var(--success); font-weight: 600;">✅ Документ загружен!</p>
                    <p>ID: ${docId}</p>
                    <p>Название: ${data.document.title}</p>
                </div>
                <p style="margin-top: 16px; text-align: center;">
                    <div class="loading"></div> Проверяем на плагиат...
                </p>
            `;
            
            // Автоматическая проверка на плагиат
            const checkResponse = await fetch(`${API_URL}/check-my-document/${docId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ n: 3 })
            });
            
            const checkResult = await checkResponse.json();
            
            // Показываем результат проверки
            displayUploadCheckResult(checkResult, title);
            
            document.getElementById('docTitle').value = '';
            document.getElementById('docText').value = '';
            
            setTimeout(() => showSection('my-docs'), 3000);
        } else {
            alert(data.error);
        }
    } catch (error) {
        alert('Ошибка: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<span class="material-icons">upload</span> Загрузить';
    }
}

function displayUploadCheckResult(result, title) {
    const percentage = Math.round(result.score * 100);
    let statusClass, statusText, statusIcon;
    
    if (percentage < 30) {
        statusClass = 'status-success';
        statusText = 'Оригинально';
        statusIcon = '✅';
    } else if (percentage < 70) {
        statusClass = 'status-warning';
        statusText = 'Подозрительно';
        statusIcon = '⚠️';
    } else {
        statusClass = 'status-error';
        statusText = 'Возможен плагиат';
        statusIcon = '❌';
    }
    
    const matchesHTML = result.matches && result.matches.length > 0
        ? result.matches.slice(0, 3).map(m => `
            <div style="background: rgba(255,255,255,0.1); padding: 12px; border-radius: 8px; margin: 8px 0;">
                <div style="font-weight: 600;">${m.doc_title}</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${Math.round(m.similarity * 100)}%; background: white;"></div>
                </div>
                <div style="text-align: right; font-size: 14px;">
                    ${Math.round(m.similarity * 100)}%
                </div>
            </div>
        `).join('')
        : '<p style="text-align: center; opacity: 0.8;">Похожих документов не найдено</p>';
    
    document.getElementById('uploadResult').innerHTML = `
        <div class="result-card" style="margin-top: 20px;">
            <h4 style="color: white; margin-bottom: 16px; text-align: center;">
                Результат проверки: "${title}"
            </h4>
            
            <div style="text-align: center; margin-bottom: 20px;">
                <div class="status-badge ${statusClass}" style="font-size: 16px;">
                    <span>${statusIcon}</span>
                    <span>${statusText}</span>
                </div>
            </div>
            
            <div style="text-align: center; margin-bottom: 20px;">
                <div class="similarity-circle" style="width: 150px; height: 150px; font-size: 40px;">
                    ${percentage}%
                </div>
                <p style="color: white; font-size: 16px; font-weight: 600;">
                    Максимальная схожесть
                </p>
            </div>
            
            ${result.matches && result.matches.length > 0 ? `
                <h5 style="color: white; margin: 16px 0 8px;">Похожие документы:</h5>
                ${matchesHTML}
            ` : ''}
            
            <div style="margin-top: 16px; padding: 12px; background: rgba(255,255,255,0.1); border-radius: 8px; font-size: 13px; color: white;">
                <p><strong>📊 Статистика:</strong></p>
                <p>• Проверено документов: ${result.stats?.documents_checked || 0}</p>
                <p>• Кэш: ${result.stats?.cache_used ? 'использован' : 'не использован'}</p>
            </div>
        </div>
    `;
}

// ===== MY DOCUMENTS (USER) =====
async function renderMyDocuments() {
    try {
        const response = await fetch(`${API_URL}/documents`, { credentials: 'include' });
        const docs = await response.json();
        
        if (docs.length === 0) {
            document.getElementById('myDocsContent').innerHTML = `
                <p style="text-align: center; color: var(--text-muted); padding: 40px;">
                    У вас пока нет загруженных документов
                </p>
            `;
            return;
        }
        
        const html = docs.map(doc => `
            <div class="doc-item">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div style="flex: 1;">
                        <div class="doc-title">${doc.title}</div>
                        <div class="doc-meta">
                            📅 ${new Date(doc.created_at).toLocaleString('ru-RU')} • 
                            📝 ${doc.text_full.length} символов
                        </div>
                        <div class="doc-text">${doc.text}</div>
                    </div>
                    <button class="btn btn-sm" onclick="checkMyDoc(${doc.id}, '${doc.title.replace(/'/g, "\\'")}')">
                        <span class="material-icons">search</span>
                        Проверить
                    </button>
                </div>
                <div id="my-result-${doc.id}"></div>
            </div>
        `).join('');
        
        document.getElementById('myDocsContent').innerHTML = html;
    } catch (error) {
        console.error('Ошибка:', error);
    }
}

async function checkMyDoc(docId, title) {
    const resultDiv = document.getElementById(`my-result-${docId}`);
    resultDiv.innerHTML = '<div style="text-align: center; padding: 20px;"><div class="loading"></div> Проверка...</div>';
    
    try {
        const response = await fetch(`${API_URL}/check-my-document/${docId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ n: 3 })
        });
        
        const result = await response.json();
        
        const percentage = Math.round(result.score * 100);
        let statusClass, statusText;
        
        if (percentage < 30) {
            statusClass = 'status-success';
            statusText = 'Оригинально ✅';
        } else if (percentage < 70) {
            statusClass = 'status-warning';
            statusText = 'Подозрительно ⚠️';
        } else {
            statusClass = 'status-error';
            statusText = 'Возможен плагиат ❌';
        }
        
        const matchesHTML = result.matches && result.matches.length > 0
            ? result.matches.slice(0, 3).map(m => `
                <div style="background: var(--surface-light); padding: 12px; border-radius: 8px; margin: 8px 0;">
                    <div style="font-weight: 600;">${m.doc_title}</div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${Math.round(m.similarity * 100)}%"></div>
                    </div>
                    <div style="text-align: right; font-size: 14px; font-weight: 600;">
                        ${Math.round(m.similarity * 100)}%
                    </div>
                </div>
            `).join('')
            : '<p style="text-align: center; color: var(--text-muted); padding: 20px;">Похожих документов не найдено</p>';
        
        resultDiv.innerHTML = `
            <div style="margin-top: 16px; padding: 20px; background: var(--surface-light); border-radius: 12px; border: 1px solid var(--border);">
                <div style="text-align: center; margin-bottom: 16px;">
                    <div class="status-badge ${statusClass}" style="font-size: 16px;">
                        ${statusText} • ${percentage}%
                    </div>
                </div>
                ${matchesHTML}
                <div style="margin-top: 12px; font-size: 12px; color: var(--text-muted); text-align: center;">
                    Проверено: ${result.stats?.documents_checked || 0} документов
                </div>
            </div>
        `;
    } catch (error) {
        resultDiv.innerHTML = `<p style="color: var(--error); text-align: center; padding: 20px;">Ошибка: ${error.message}</p>`;
    }
}

// ===== CHECK (ADMIN) =====
async function renderCheckPage() {
    try {
        const response = await fetch(`${API_URL}/documents`, { credentials: 'include' });
        allDocuments = await response.json();
        
        if (allDocuments.length === 0) {
            document.getElementById('checkContent').innerHTML = `
                <p style="text-align: center; color: var(--text-muted);">Нет документов для проверки</p>
            `;
            return;
        }
        
        const html = allDocuments.map(doc => `
            <div class="doc-item">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div style="flex: 1;">
                        <div class="doc-title">${doc.title}</div>
                        <div class="doc-meta">
                            👤 ${doc.author} • 
                            📅 ${new Date(doc.created_at).toLocaleString('ru-RU')} • 
                            📝 ${doc.text_full.length} символов
                        </div>
                        <div class="doc-text">${doc.text}</div>
                    </div>
                    <button class="btn btn-sm" onclick="checkDocument(${doc.id})">
                        <span class="material-icons">search</span>
                        Проверить
                    </button>
                </div>
                <div id="result-${doc.id}"></div>
            </div>
        `).join('');
        
        document.getElementById('checkContent').innerHTML = html;
    } catch (error) {
        console.error('Ошибка:', error);
    }
}

async function checkDocument(docId) {
    const resultDiv = document.getElementById(`result-${docId}`);
    resultDiv.innerHTML = '<div class="loading"></div> Проверка...';
    
    try {
        const response = await fetch(`${API_URL}/check/${docId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ n: 3 })
        });
        
        const result = await response.json();
        
        const percentage = Math.round(result.score * 100);
        let statusClass, statusText;
        
        if (percentage < 30) {
            statusClass = 'status-success';
            statusText = 'Оригинально ✅';
        } else if (percentage < 70) {
            statusClass = 'status-warning';
            statusText = 'Подозрительно ⚠️';
        } else {
            statusClass = 'status-error';
            statusText = 'Плагиат ❌';
        }
        
        const matchesHTML = result.matches.slice(0, 3).map(m => `
            <div style="background: var(--surface-light); padding: 12px; border-radius: 8px; margin: 8px 0;">
                <div style="font-weight: 600;">${m.doc_title}</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${Math.round(m.similarity * 100)}%"></div>
                </div>
                <div style="text-align: right; font-size: 14px; font-weight: 600;">
                    ${Math.round(m.similarity * 100)}%
                </div>
            </div>
        `).join('');
        
        resultDiv.innerHTML = `
            <div style="margin-top: 16px; padding: 16px; background: var(--surface-light); border-radius: 12px;">
                <div style="text-align: center; margin-bottom: 16px;">
                    <div class="status-badge ${statusClass}" style="font-size: 16px;">
                        ${statusText} • ${percentage}%
                    </div>
                </div>
                ${matchesHTML}
                <div style="margin-top: 12px; font-size: 12px; color: var(--text-muted);">
                    Проверено документов: ${result.stats.documents_checked} • 
                    Кэш: ${result.stats.cache_used ? 'использован' : 'не использован'}
                </div>
            </div>
        `;
    } catch (error) {
        resultDiv.innerHTML = `<p style="color: var(--error);">Ошибка: ${error.message}</p>`;
    }
}

// ===== ALL DOCUMENTS (ADMIN) =====
async function renderAllDocuments() {
    try {
        const response = await fetch(`${API_URL}/documents`, { credentials: 'include' });
        allDocuments = await response.json();
        displayDocuments(allDocuments);
    } catch (error) {
        console.error('Ошибка:', error);
    }
}

async function applyFilters() {
    const author = document.getElementById('filterAuthor').value;
    const minLength = parseInt(document.getElementById('filterMinLength').value) || 0;
    
    const params = new URLSearchParams();
    if (author) params.append('author', author);
    if (minLength > 0) params.append('min_length', minLength);
    
    try {
        const response = await fetch(`${API_URL}/documents?${params}`, { credentials: 'include' });
        const docs = await response.json();
        displayDocuments(docs);
    } catch (error) {
        console.error('Ошибка:', error);
    }
}

function clearFilters() {
    document.getElementById('filterAuthor').value = '';
    document.getElementById('filterMinLength').value = '';
    document.getElementById('searchQuery').value = '';
    renderAllDocuments();
}

function searchDocuments() {
    const query = document.getElementById('searchQuery').value.toLowerCase();
    const filtered = allDocuments.filter(doc => 
        doc.title.toLowerCase().includes(query) || 
        doc.author.toLowerCase().includes(query)
    );
    displayDocuments(filtered);
}

function displayDocuments(docs) {
    if (docs.length === 0) {
        document.getElementById('documentsTable').innerHTML = `
            <p style="text-align: center; color: var(--text-muted); padding: 40px;">
                Документы не найдены
            </p>
        `;
        return;
    }
    
    const html = docs.map(doc => `
        <div class="doc-item">
            <div class="doc-title">${doc.title}</div>
            <div class="doc-meta">
                👤 ${doc.author} • 
                📅 ${new Date(doc.created_at).toLocaleString('ru-RU')} • 
                📝 ${doc.text_full.length} символов
            </div>
            <div class="doc-text">${doc.text}</div>
        </div>
    `).join('');
    
    document.getElementById('documentsTable').innerHTML = html;
}

// ===== HISTORY (ADMIN) =====
async function renderHistory() {
    try {
        const response = await fetch(`${API_URL}/checks/history`, { credentials: 'include' });
        const checks = await response.json();
        
        if (checks.length === 0) {
            document.getElementById('historyContent').innerHTML = `
                <p style="text-align: center; color: var(--text-muted);">История пуста</p>
            `;
            return;
        }
        
        const html = checks.map(check => {
            const percentage = check.similarity_score;
            const statusClass = percentage < 30 ? 'status-success' : 
                               percentage < 70 ? 'status-warning' : 'status-error';
            
            return `
                <div class="doc-item">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div class="doc-title">${check.doc_title}</div>
                            <div class="doc-meta">
                                👤 Автор: ${check.doc_author} • 
                                👨‍💼 Проверил: ${check.admin_name} • 
                                📅 ${new Date(check.checked_at).toLocaleString('ru-RU')}
                            </div>
                        </div>
                        <div class="status-badge ${statusClass}">
                            ${percentage}%
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        
        document.getElementById('historyContent').innerHTML = html;
    } catch (error) {
        console.error('Ошибка:', error);
    }
}

// ===== RECURSIVE ANALYSIS (ADMIN) =====
function renderAnalyticsPage() {
    // Страница уже есть в HTML, просто показываем её
    document.getElementById('recursiveResult').innerHTML = '';
}

async function runRecursiveAnalysis() {
    const btn = event.target;
    btn.disabled = true;
    btn.innerHTML = '<div class="loading"></div> Анализ...';
    
    const resultDiv = document.getElementById('recursiveResult');
    resultDiv.innerHTML = '<p style="text-align: center; padding: 40px;"><div class="loading"></div></p>';
    
    try {
        const response = await fetch(`${API_URL}/analytics/recursive`, { 
            credentials: 'include' 
        });
        
        if (!response.ok) {
            throw new Error('Ошибка анализа');
        }
        
        const data = await response.json();
        
        // Визуализация результатов
        const avgSimilarity = data.similarities.length > 0 
            ? data.similarities.reduce((a, b) => a + b, 0) / data.similarities.length 
            : 0;
        
        const highSimilarities = data.similarities.filter(s => s > 0.7).length;
        const mediumSimilarities = data.similarities.filter(s => s >= 0.3 && s <= 0.7).length;
        const lowSimilarities = data.similarities.filter(s => s < 0.3).length;
        
        resultDiv.innerHTML = `
            <div style="margin-top: 24px;">
                <div class="info-box" style="background: rgba(139, 92, 246, 0.1); border-color: var(--primary);">
                    <h4>🔍 Рекурсивный анализ завершён (Лаба №2)</h4>
                    <p style="margin-top: 12px;">Использованы две рекурсивные функции:</p>
                    <p>• <strong>compare_submissions_recursive()</strong> - рекурсивное сравнение документов</p>
                    <p>• <strong>tree_walk_documents()</strong> - рекурсивное построение дерева связей</p>
                </div>
                
                <div class="stats-grid" style="margin-top: 20px;">
                    <div class="stat-item">
                        <div class="stat-value">${data.similarities.length}</div>
                        <div class="stat-label">Проанализировано</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${Math.round(avgSimilarity * 100)}%</div>
                        <div class="stat-label">Средняя схожесть</div>
                    </div>
                    <div class="stat-item" style="background: #FFEBEE;">
                        <div class="stat-value" style="color: var(--error);">${highSimilarities}</div>
                        <div class="stat-label">Высокая схожесть (>70%)</div>
                    </div>
                    <div class="stat-item" style="background: #FFF3E0;">
                        <div class="stat-value" style="color: var(--warning);">${mediumSimilarities}</div>
                        <div class="stat-label">Средняя (30-70%)</div>
                    </div>
                    <div class="stat-item" style="background: #E8F5E9;">
                        <div class="stat-value" style="color: var(--success);">${lowSimilarities}</div>
                        <div class="stat-label">Низкая (<30%)</div>
                    </div>
                </div>
                
                <div class="card" style="margin-top: 20px; background: var(--surface-light);">
                    <h4 style="margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
                        <span class="material-icons">account_tree</span>
                        Дерево связей документов (рекурсивный обход)
                    </h4>
                    <p style="color: var(--text-secondary); margin-bottom: 12px;">
                        Документы связаны по схожести содержания (порог 30%)
                    </p>
                    <div style="background: var(--bg); padding: 16px; border-radius: 8px; font-family: monospace; overflow-x: auto;">
                        ${data.document_tree.map((id, idx) => {
                            const arrow = idx < data.document_tree.length - 1 ? ' → ' : '';
                            return `<span style="color: var(--primary);">${id}</span>${arrow}`;
                        }).join('')}
                    </div>
                    <p style="margin-top: 12px; font-size: 13px; color: var(--text-muted);">
                        Найдено ${data.document_tree.length} связанных документов в цепочке
                    </p>
                </div>
                
                <div class="info-box" style="margin-top: 20px;">
                    <h4>📊 Детальная статистика схожести:</h4>
                    ${data.similarities.slice(0, 10).map((sim, idx) => {
                        const percentage = Math.round(sim * 100);
                        const statusClass = percentage < 30 ? 'status-success' : 
                                           percentage < 70 ? 'status-warning' : 'status-error';
                        return `
                            <div style="display: flex; justify-content: space-between; align-items: center; margin: 8px 0;">
                                <span>Документ ${idx + 1}</span>
                                <div class="progress-bar" style="width: 200px; margin: 0 12px;">
                                    <div class="progress-fill" style="width: ${percentage}%"></div>
                                </div>
                                <span class="status-badge ${statusClass}" style="padding: 4px 12px; font-size: 12px;">
                                    ${percentage}%
                                </span>
                            </div>
                        `;
                    }).join('')}
                    ${data.similarities.length > 10 ? `<p style="margin-top: 8px; text-align: center; color: var(--text-muted);">... и ещё ${data.similarities.length - 10} документов</p>` : ''}
                </div>
            </div>
        `;
    } catch (error) {
        resultDiv.innerHTML = `
            <div class="info-box" style="margin-top: 20px; background: rgba(239, 68, 68, 0.1); border-color: var(--error);">
                <p style="color: var(--error); font-weight: 600;">❌ Ошибка анализа</p>
                <p>${error.message}</p>
            </div>
        `;
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<span class="material-icons">analytics</span> Запустить рекурсивный анализ';
    }
}