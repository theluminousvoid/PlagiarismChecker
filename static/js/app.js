// API Base URL - используем относительные пути
const API_URL = '/api';

// State
let currentUser = null;
let allDocuments = [];
let currentEventSource = null;

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
                <h4>💾 Кэш (мемоизация):</h4>
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

// ===== CHECK PAGE (ADMIN) - с ленивой прогрессивной проверкой =====
async function renderCheckPage() {
    document.getElementById('checkContent').innerHTML = `
        <div class="card">
            <h3 class="card-title">
                <span class="material-icons">search</span>
                Проверка текста на плагиат
            </h3>
            
            <div class="form-group">
                <label class="input-label">Текст для проверки</label>
                <textarea class="textarea" id="checkText" placeholder="Вставьте текст для проверки на плагиат..." rows="6"></textarea>
            </div>
            
            <div class="form-grid">
                <div class="form-group">
                    <label class="input-label">Размер n-грамм</label>
                    <input type="number" class="input" id="checkN" value="3" min="2" max="5">
                </div>
                <div class="form-group">
                    <label class="input-label">Порог схожести (0-1)</label>
                    <input type="number" class="input" id="checkThreshold" value="0" min="0" max="1" step="0.1" 
                        placeholder="0 = все результаты">
                </div>
            </div>
            
            <div style="display: flex; gap: 12px; flex-wrap: wrap;">
                <button class="btn" onclick="startProgressiveCheck()">
                    <span class="material-icons">search</span>
                    Полная проверка с прогрессом
                </button>
                <button class="btn btn-secondary" onclick="quickCheck()">
                    <span class="material-icons">flash_on</span>
                    Быстрая проверка
                </button>
                <button class="btn btn-secondary" onclick="searchInDocuments()">
                    <span class="material-icons">find_in_page</span>
                    Поиск по документам
                </button>
            </div>
            
            <div id="checkResults" style="margin-top: 20px;"></div>
        </div>
    `;
}

// Прогрессивная проверка с ленивыми вычислениями
async function startProgressiveCheck() {
    const text = document.getElementById('checkText').value.trim();
    const n = parseInt(document.getElementById('checkN').value) || 3;
    const threshold = parseFloat(document.getElementById('checkThreshold').value) || 0.0;
    
    if (!text) {
        alert('Введите текст для проверки');
        return;
    }
    
    // Закрываем предыдущее соединение, если есть
    if (currentEventSource) {
        currentEventSource.close();
    }
    
    const resultsDiv = document.getElementById('checkResults');
    resultsDiv.innerHTML = `
        <div class="progress-section">
            <div class="progress-bar">
                <div class="progress-fill" id="plagiarismProgress" style="width: 0%"></div>
            </div>
            <div class="progress-text" id="progressText">Подготовка к проверке...</div>
            <div id="plagiarismResults" class="results-container" style="margin-top: 20px;"></div>
        </div>
    `;
    
    try {
        const response = await fetch(`${API_URL}/plagiarism/progressive-check`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ text, n, threshold })
        });
        
        if (!response.ok) {
            throw new Error('Ошибка запуска проверки');
        }
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || ''; // Последняя неполная строка
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = JSON.parse(line.slice(6));
                    
                    if (data.status === 'started') {
                        document.getElementById('progressText').textContent = `Начинаем проверку ${data.total} документов...`;
                    } 
                    else if (data.progress !== undefined) {
                        document.getElementById('plagiarismProgress').style.width = `${data.progress}%`;
                        document.getElementById('progressText').textContent = `Проверено: ${data.progress}%`;
                        
                        if (data.similarity > 0) {
                            addProgressiveResult(data);
                        }
                    }
                    else if (data.status === 'completed') {
                        document.getElementById('progressText').textContent = 
                            `✅ Проверка завершена! Найдено ${data.total_results} совпадений`;
                    }
                }
            }
        }
        
    } catch (error) {
        console.error('Progressive check error:', error);
        document.getElementById('checkResults').innerHTML = `
            <div class="info-box" style="background: rgba(239, 68, 68, 0.1); border-color: var(--error);">
                <p style="color: var(--error);"><strong>❌ Ошибка проверки:</strong> ${error.message}</p>
            </div>
        `;
    }
}

function addProgressiveResult(result) {
    const container = document.getElementById('plagiarismResults');
    const element = document.createElement('div');
    element.className = 'plagiarism-result';
    
    const similarityPercent = (result.similarity * 100).toFixed(1);
    const color = similarityPercent > 50 ? '#f44336' : similarityPercent > 20 ? '#ff9800' : '#4caf50';
    
    element.innerHTML = `
        <div class="similarity-badge" style="background: ${color}">
            ${similarityPercent}%
        </div>
        <div class="result-content">
            <h4>📄 ${escapeHtml(result.doc_title)}</h4>
            <p>👤 Автор: ${escapeHtml(result.doc_author)}</p>
            <p>🆔 ID: ${result.doc_id}</p>
            <p>📈 Прогресс: ${result.progress}%</p>
        </div>
    `;
    
    container.appendChild(element);
}

// Быстрая проверка с пакетной обработкой
async function quickCheck() {
    const text = document.getElementById('checkText').value.trim();
    
    if (!text) {
        alert('Введите текст для проверки');
        return;
    }
    
    const resultsDiv = document.getElementById('checkResults');
    resultsDiv.innerHTML = '<div class="loading"></div> Быстрая проверка...';
    
    try {
        const response = await fetch(`${API_URL}/plagiarism/quick-check`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ text })
        });
        
        const data = await response.json();
        
        if (data.quick_results.length === 0) {
            resultsDiv.innerHTML = `
                <div class="info-box" style="background: rgba(16, 185, 129, 0.1); border-color: var(--success);">
                    <p style="color: var(--success);"><strong>✅ Быстрая проверка завершена</strong></p>
                    <p>Похожих документов не найдено</p>
                    <p><small>Проверено: ${data.total_checked} документов</small></p>
                </div>
            `;
            return;
        }
        
        let html = `
            <div class="info-box">
                <p><strong>⚡ Быстрая проверка завершена</strong></p>
                <p>Найдено ${data.quick_results.length} возможных совпадений</p>
                <p><small>Проверено: ${data.total_checked} документов</small></p>
            </div>
        `;
        
        data.quick_results.forEach(result => {
            const similarityPercent = (result.similarity * 100).toFixed(1);
            html += `
                <div class="doc-item" style="margin-top: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="flex: 1;">
                            <div class="doc-title">${result.doc_title}</div>
                            <div class="doc-meta">👤 ${result.doc_author}</div>
                            <div class="doc-meta">${result.reason}</div>
                        </div>
                        <span class="status-badge ${similarityPercent > 50 ? 'status-error' : 'status-warning'}">
                            ${similarityPercent}%
                        </span>
                    </div>
                </div>
            `;
        });
        
        resultsDiv.innerHTML = html;
        
    } catch (error) {
        resultsDiv.innerHTML = `
            <div class="info-box" style="background: rgba(239, 68, 68, 0.1); border-color: var(--error);">
                <p style="color: var(--error);"><strong>❌ Ошибка быстрой проверки:</strong> ${error.message}</p>
            </div>
        `;
    }
}

// Поиск по документам с ленивыми результатами
async function searchInDocuments() {
    const text = document.getElementById('checkText').value.trim();
    
    if (!text) {
        alert('Введите текст для поиска');
        return;
    }
    
    const resultsDiv = document.getElementById('checkResults');
    resultsDiv.innerHTML = '<div class="loading"></div> Ищем совпадения...';
    
    try {
        const response = await fetch(`${API_URL}/search/documents?q=${encodeURIComponent(text)}`, {
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.results.length === 0) {
            resultsDiv.innerHTML = `
                <div class="info-box">
                    <p>По запросу "${text}" ничего не найдено</p>
                </div>
            `;
            return;
        }
        
        let html = `
            <div class="info-box">
                <p><strong>🔍 Результаты поиска</strong></p>
                <p>Найдено документов: ${data.results.length}</p>
            </div>
        `;
        
        data.results.forEach(result => {
            const relevancePercent = (result.relevance * 100).toFixed(0);
            html += `
                <div class="doc-item" style="margin-top: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div style="flex: 1;">
                            <div class="doc-title">${result.document.title}</div>
                            <div class="doc-meta">👤 ${result.document.author}</div>
                            <div class="doc-text">${result.document.text}</div>
                        </div>
                        <span class="status-badge status-success" style="flex-shrink: 0;">
                            Релевантность: ${relevancePercent}%
                        </span>
                    </div>
                </div>
            `;
        });
        
        resultsDiv.innerHTML = html;
        
    } catch (error) {
        resultsDiv.innerHTML = `
            <div class="info-box" style="background: rgba(239, 68, 68, 0.1); border-color: var(--error);">
                <p style="color: var(--error);"><strong>❌ Ошибка поиска:</strong> ${error.message}</p>
            </div>
        `;
    }
}

// ===== ALL DOCUMENTS (ADMIN) - с ленивой пагинацией =====
let currentPage = 0;
const pageSize = 20;
let currentFilters = {};

async function renderAllDocuments() {
    await loadDocumentsLazy();
}

async function loadDocumentsLazy(page = 0) {
    currentPage = page;
    
    try {
        const params = new URLSearchParams({
            page: currentPage,
            page_size: pageSize,
            ...currentFilters
        });
        
        const response = await fetch(`${API_URL}/documents?${params}`, { credentials: 'include' });
        const data = await response.json();
        
        displayDocumentsWithPagination(data.documents, data.total, currentPage);
        
    } catch (error) {
        console.error('Ошибка загрузки документов:', error);
        document.getElementById('documentsTable').innerHTML = `
            <p style="text-align: center; color: var(--error); padding: 40px;">
                Ошибка загрузки документов
            </p>
        `;
    }
}

function displayDocumentsWithPagination(docs, total, page) {
    const container = document.getElementById('documentsTable');
    
    if (docs.length === 0) {
        container.innerHTML = `
            <p style="text-align: center; color: var(--text-muted); padding: 40px;">
                Документы не найдены
            </p>
        `;
        return;
    }
    
    const totalPages = Math.ceil(total / pageSize);
    
    let html = `
        <div class="table-header">
            <span>📊 Всего документов: ${total}</span>
            <div class="pagination">
                <button class="btn btn-sm" onclick="loadDocumentsLazy(${page - 1})" ${page === 0 ? 'disabled' : ''}>
                    ← Назад
                </button>
                <span>Страница ${page + 1} из ${totalPages}</span>
                <button class="btn btn-sm" onclick="loadDocumentsLazy(${page + 1})" ${(page + 1) >= totalPages ? 'disabled' : ''}>
                    Вперед →
                </button>
            </div>
        </div>
    `;
    
    docs.forEach(doc => {
        html += `
            <div class="doc-item">
                <div class="doc-title">${doc.title}</div>
                <div class="doc-meta">
                    👤 ${doc.author} • 
                    📅 ${new Date(doc.created_at).toLocaleString('ru-RU')} • 
                    📝 ${doc.length} символов
                </div>
                <div class="doc-text">${doc.text}</div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

async function applyFilters() {
    const author = document.getElementById('filterAuthor').value.trim();
    const title = document.getElementById('filterTitle').value.trim();
    const minLength = document.getElementById('filterMinLength').value;
    const dateFrom = document.getElementById('filterDateFrom').value;
    const dateTo = document.getElementById('filterDateTo').value;
    
    currentFilters = {};
    if (author) currentFilters.author = author;
    if (title) currentFilters.title = title;
    if (minLength) currentFilters.min_length = minLength;
    if (dateFrom) currentFilters.date_from = dateFrom;
    if (dateTo) currentFilters.date_to = dateTo;
    
    await loadDocumentsLazy(0);
}

function clearFilters() {
    document.getElementById('filterAuthor').value = '';
    document.getElementById('filterTitle').value = '';
    document.getElementById('filterMinLength').value = '';
    document.getElementById('filterDateFrom').value = '';
    document.getElementById('filterDateTo').value = '';
    
    currentFilters = {};
    loadDocumentsLazy(0);
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

// ===== ANALYTICS (ADMIN) - с пакетной обработкой =====
function renderAnalyticsPage() {
    document.getElementById('recursiveResult').innerHTML = '';
    document.getElementById('authorStatsResult').innerHTML = '';
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
                <div class="card" style="background: linear-gradient(135deg, var(--primary), var(--secondary)); color: white; margin-bottom: 20px;">
                    <h3 style="margin: 0 0 16px 0; display: flex; align-items: center; gap: 8px;">
                        <span class="material-icons">analytics</span>
                        Результаты рекурсивного анализа
                    </h3>
                    
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 16px;">
                        <div>
                            <div style="font-size: 32px; font-weight: 800; margin-bottom: 4px;">
                                ${data.similarities.length}
                            </div>
                            <div style="font-size: 13px; opacity: 0.9;">
                                Документов проанализировано
                            </div>
                        </div>
                        <div>
                            <div style="font-size: 32px; font-weight: 800; margin-bottom: 4px;">
                                ${data.document_tree.length}
                            </div>
                            <div style="font-size: 13px; opacity: 0.9;">
                                Документов в цепочке
                            </div>
                        </div>
                        <div>
                            <div style="font-size: 32px; font-weight: 800; margin-bottom: 4px;">
                                ${Math.round(Math.max(...data.similarities) * 100)}%
                            </div>
                            <div style="font-size: 13px; opacity: 0.9;">
                                Максимальная схожесть
                            </div>
                        </div>
                        <div>
                            <div style="font-size: 32px; font-weight: 800; margin-bottom: 4px;">
                                ${highSimilarities}
                            </div>
                            <div style="font-size: 13px; opacity: 0.9;">
                                Возможных плагиатов
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Дерево связей и статистика остаются без изменений -->
                ${renderDocumentTree(data)}
                ${renderSimilarityStats(data, highSimilarities, mediumSimilarities, lowSimilarities)}
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

// Новая функция: пакетная статистика
async function showBatchStats() {
    const resultDiv = document.getElementById('authorStatsResult');
    const btn = event.target;
    btn.disabled = true;
    btn.innerHTML = '<div class="loading"></div> Загрузка...';
    
    resultDiv.innerHTML = '<p style="text-align: center; padding: 20px;"><div class="loading"></div></p>';
    
    try {
        const response = await fetch(`${API_URL}/analytics/batch-stats`, {
            credentials: 'include'
        });
        
        const data = await response.json();
        
        let html = `
            <div style="margin-top: 24px;">
                <div class="card" style="background: linear-gradient(135deg, var(--primary), var(--secondary)); color: white; margin-bottom: 20px;">
                    <h3 style="margin: 0 0 16px 0; display: flex; align-items: center; gap: 8px;">
                        <span class="material-icons">table_chart</span>
                        Пакетная статистика документов
                    </h3>
                    
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 16px;">
                        <div>
                            <div style="font-size: 32px; font-weight: 800; margin-bottom: 4px;">
                                ${data.total_documents}
                            </div>
                            <div style="font-size: 13px; opacity: 0.9;">
                                Всего документов
                            </div>
                        </div>
                        <div>
                            <div style="font-size: 32px; font-weight: 800; margin-bottom: 4px;">
                                ${data.total_characters}
                            </div>
                            <div style="font-size: 13px; opacity: 0.9;">
                                Всего символов
                            </div>
                        </div>
                        <div>
                            <div style="font-size: 32px; font-weight: 800; margin-bottom: 4px;">
                                ${data.average_length}
                            </div>
                            <div style="font-size: 13px; opacity: 0.9;">
                                Средняя длина
                            </div>
                        </div>
                        <div>
                            <div style="font-size: 32px; font-weight: 800; margin-bottom: 4px;">
                                ${data.batches.length}
                            </div>
                            <div style="font-size: 13px; opacity: 0.9;">
                                Пакетов обработано
                            </div>
                        </div>
                    </div>
                </div>
        `;
        
        // Отображаем статистику по пакетам
        data.batches.forEach((batch, index) => {
            html += `
                <div class="card" style="margin-bottom: 16px; background: var(--surface-light);">
                    <h4 style="margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
                        <span class="material-icons">layers</span>
                        Пакет ${batch.batch}
                    </h4>
                    
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 12px; margin-bottom: 12px;">
                        <div style="text-align: center;">
                            <div style="font-size: 24px; font-weight: 700; color: var(--primary);">
                                ${batch.documents}
                            </div>
                            <div style="font-size: 12px; color: var(--text-muted);">
                                Документов
                            </div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 24px; font-weight: 700; color: var(--secondary);">
                                ${batch.total_chars}
                            </div>
                            <div style="font-size: 12px; color: var(--text-muted);">
                                Символов
                            </div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 24px; font-weight: 700; color: var(--success);">
                                ${batch.avg_chars}
                            </div>
                            <div style="font-size: 12px; color: var(--text-muted);">
                                Средняя длина
                            </div>
                        </div>
                    </div>
                    
                    <div style="font-size: 13px; color: var(--text-muted);">
                        <strong>Авторы в пакете:</strong> ${batch.authors.join(', ')}
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        resultDiv.innerHTML = html;
        
    } catch (error) {
        resultDiv.innerHTML = `
            <div class="info-box" style="margin-top: 20px; background: rgba(239, 68, 68, 0.1); border-color: var(--error);">
                <p style="color: var(--error); font-weight: 600; margin: 0;">❌ Ошибка загрузки статистики</p>
                <p style="color: var(--error); margin: 8px 0 0 0;">${error.message}</p>
            </div>
        `;
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<span class="material-icons">table_chart</span> Показать пакетную статистику';
    }
}

// Обновляем HTML для аналитики - добавляем новую кнопку
// В разделе аналитики добавьте эту кнопку после существующих:
/*
<button class="btn" onclick="showBatchStats()">
    <span class="material-icons">table_chart</span>
    Показать пакетную статистику
</button>
*/

// ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====
function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Функции renderDocumentTree и renderSimilarityStats остаются без изменений
function renderDocumentTree(data) {
    return `
        <div class="card" style="background: var(--surface-light); margin-bottom: 20px;">
            <h4 style="margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
                <span class="material-icons">account_tree</span>
                Дерево связей документов
            </h4>
            <p style="color: var(--text-secondary); font-size: 13px; margin-bottom: 16px;">
                Самая длинная цепочка связанных документов (${data.document_tree.length} документов)
            </p>
            
            ${data.tree_with_titles.map((item, idx) => {
                const arrow = idx < data.tree_with_titles.length - 1 
                    ? `<div style="text-align: center; margin: 8px 0;">
                         <span class="material-icons" style="color: var(--primary); font-size: 28px;">arrow_downward</span>
                       </div>` 
                    : '';
                return `
                    <div>
                        <div style="
                            background: linear-gradient(135deg, var(--primary), var(--secondary));
                            color: white;
                            padding: 14px 18px;
                            border-radius: 10px;
                            font-weight: 600;
                            box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
                        ">
                            <div style="font-size: 11px; opacity: 0.8; margin-bottom: 4px;">
                                Шаг ${idx + 1} • ID: ${item.id}
                            </div>
                            <div style="font-size: 14px;">
                                ${item.title}
                            </div>
                        </div>
                        ${arrow}
                    </div>
                `;
            }).join('')}
        </div>
    `;
}

function renderSimilarityStats(data, high, medium, low) {
    return `
        <div class="card" style="background: var(--surface-light);">
            <h4 style="margin-bottom: 16px; display: flex; align-items: center; gap: 8px;">
                <span class="material-icons">pie_chart</span>
                Распределение по категориям схожести
            </h4>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px;">
                <div style="padding: 16px; background: var(--surface); border-radius: 10px; border-top: 4px solid #ef4444;">
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                        <span style="font-size: 24px;">🚨</span>
                        <span style="font-weight: 600; color: var(--text);">Плагиат (≥70%)</span>
                    </div>
                    <div style="font-size: 36px; font-weight: 800; color: #ef4444; margin-bottom: 4px;">
                        ${high}
                    </div>
                    <div style="font-size: 13px; color: var(--text-muted);">
                        ${Math.round(high / data.similarities.length * 100)}% от всех документов
                    </div>
                </div>
                
                <div style="padding: 16px; background: var(--surface); border-radius: 10px; border-top: 4px solid #f59e0b;">
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                        <span style="font-size: 24px;">⚠️</span>
                        <span style="font-weight: 600; color: var(--text);">Похожие (30-70%)</span>
                    </div>
                    <div style="font-size: 36px; font-weight: 800; color: #f59e0b; margin-bottom: 4px;">
                        ${medium}
                    </div>
                    <div style="font-size: 13px; color: var(--text-muted);">
                        ${Math.round(medium / data.similarities.length * 100)}% от всех документов
                    </div>
                </div>
                
                <div style="padding: 16px; background: var(--surface); border-radius: 10px; border-top: 4px solid #10b981;">
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                        <span style="font-size: 24px;">✅</span>
                        <span style="font-weight: 600; color: var(--text);">Оригиналы (<30%)</span>
                    </div>
                    <div style="font-size: 36px; font-weight: 800; color: #10b981; margin-bottom: 4px;">
                        ${low}
                    </div>
                    <div style="font-size: 13px; color: var(--text-muted);">
                        ${Math.round(low / data.similarities.length * 100)}% от всех документов
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Обновляем функцию showAuthorStats для использования ленивых вычислений
async function showAuthorStats() {
    const resultDiv = document.getElementById('authorStatsResult');
    if (!resultDiv) {
        console.error('Элемент authorStatsResult не найден!');
        alert('Ошибка: не найден контейнер для результатов');
        return;
    }
    
    const btn = event.target;
    btn.disabled = true;
    btn.innerHTML = '<div class="loading"></div> Загрузка...';
    
    resultDiv.innerHTML = '<p style="text-align: center; padding: 20px;"><div class="loading"></div></p>';
    
    try {
        const response = await fetch(`${API_URL}/stats/authors`, {
            credentials: 'include'
        });
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Ошибка загрузки');
        }
        
        // Остальная часть функции showAuthorStats остается без изменений
        // ... (существующий код отображения статистики авторов)
        
    } catch (error) {
        resultDiv.innerHTML = `
            <div class="info-box" style="margin-top: 20px; background: rgba(239, 68, 68, 0.1); border-color: var(--error);">
                <p style="color: var(--error); font-weight: 600; margin: 0;">❌ Ошибка загрузки статистики</p>
                <p style="color: var(--error); margin: 8px 0 0 0;">${error.message}</p>
            </div>
        `;
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<span class="material-icons">bar_chart</span> Показать статистику';
    }
}
