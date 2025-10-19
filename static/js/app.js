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

// ===== CHECK PAGE (ADMIN) =====
async function renderCheckPage() {
    try {
        const response = await fetch(`${API_URL}/documents`, { credentials: 'include' });
        allDocuments = await response.json();
        
        if (allDocuments.length === 0) {
            document.getElementById('checkContent').innerHTML = `
                <div class="card">
                    <p style="text-align: center; color: var(--text-secondary);">Нет документов для проверки</p>
                </div>
            `;
            return;
        }
        
        const html = allDocuments.map(doc => `
            <div class="card" style="margin-top: 16px;">
                <div style="display: flex; gap: 20px; align-items: start;">
                    <div style="flex: 1;">
                        <div class="doc-title">${doc.title}</div>
                        <div class="doc-meta">
                            👤 ${doc.author} • 
                            📅 ${new Date(doc.created_at).toLocaleString('ru-RU')} • 
                            📝 ${doc.text_full.length} символов
                        </div>
                        <div class="doc-text">${doc.text}</div>
                    </div>
                    <button class="btn btn-sm" onclick="checkDocument(${doc.id})" style="flex-shrink: 0;">
                        <span class="material-icons">search</span>
                        Проверить
                    </button>
                </div>
                <div id="result-${doc.id}" style="margin-top: 16px;"></div>
            </div>
        `).join('');
        
        document.getElementById('checkContent').innerHTML = html;
        
    } catch (error) {
        console.error('Ошибка:', error);
    }
}
async function checkDocument(docId) {
    const n = parseInt(document.getElementById('checkN').value) || 3;
    const threshold = parseFloat(document.getElementById('checkThreshold').value) || 0;
    const resultDiv = document.getElementById(`result-${docId}`);
    
    const btn = event.target.closest('button');
    btn.disabled = true;
    btn.innerHTML = '<span class="material-icons rotating">sync</span> Проверка...';
    
    try {
        const response = await fetch(`${API_URL}/check/${docId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ n, threshold })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error);
        }
        
        const percentage = Math.round(data.score * 100);
        const statusClass = percentage < 30 ? 'status-success' : 
                           percentage < 70 ? 'status-warning' : 'status-error';
        const statusText = percentage < 30 ? 'Оригинальный' : 
                          percentage < 70 ? 'Подозрительный' : 'Плагиат!';
        
        let html = `
            <div class="result-card">
                <div class="similarity-circle">${percentage}%</div>
                <h3 style="text-align: center; margin-bottom: 8px;">Результат проверки</h3>
                <div class="status-badge ${statusClass}" style="display: flex; justify-content: center; margin: 0 auto; width: fit-content;">
                    ${statusText}
                </div>
            </div>
            
            ${data.filtered_by_threshold ? `
                <div class="info-box">
                    <p><strong>🎯 Применен порог:</strong> показаны только результаты ≥ ${Math.round(data.filtered_by_threshold * 100)}%</p>
                    <p><strong>🔧 Техника:</strong> Лаба №2 (замыкание create_similarity_threshold)</p>
                </div>
            ` : ''}
            
            <div class="info-box">
                <h4>📊 Статистика</h4>
                <p>• Токенов: ${data.stats.tokens}</p>
                <p>• N-грамм: ${data.stats.ngrams}</p>
                <p>• Проверено документов: ${data.stats.documents_checked}</p>
                <p>• Кэш используется: ${data.stats.cache_used ? '✅ Да' : '❌ Нет'}</p>
            </div>
        `;
        
        if (data.matches && data.matches.length > 0) {
            html += '<div class="info-box"><h4>Похожие документы</h4>';
            data.matches.forEach((match, i) => {
                const matchPercent = Math.round(match.similarity * 100);
                const matchStatus = matchPercent < 30 ? 'status-success' : 
                                   matchPercent < 70 ? 'status-warning' : 'status-error';
                html += `
                    <div class="doc-item" style="margin-top: 12px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div style="flex: 1;">
                                <div class="doc-title">${i+1}. ${match.doc_title}</div>
                                <div class="doc-meta">
                                    ${match.doc_author ? `👤 ${match.doc_author}` : '👤 Автор не указан'}
                                </div>
                            </div>
                            <span class="status-badge ${matchStatus}">${matchPercent}%</span>
                        </div>
                    </div>
                `;
            });
            html += '</div>';
        } else if (data.filtered_by_threshold) {
            html += `
                <div class="info-box">
                    <p>⚠️ Нет документов, соответствующих порогу схожести</p>
                </div>
            `;
        }
        
        resultDiv.innerHTML = html;
        
    } catch (error) {
        resultDiv.innerHTML = `
            <div class="info-box" style="border-left: 4px solid var(--error);">
                <p style="color: var(--error);"><strong>❌ Ошибка проверки:</strong> ${error.message}</p>
            </div>
        `;
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<span class="material-icons">search</span> Проверить';
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
    // Очищаем все поля фильтров
    const filterAuthor = document.getElementById('filterAuthor');
    const filterTitle = document.getElementById('filterTitle');
    const filterMinLength = document.getElementById('filterMinLength');
    const filterDateFrom = document.getElementById('filterDateFrom');
    const filterDateTo = document.getElementById('filterDateTo');
    
    if (filterAuthor) filterAuthor.value = '';
    if (filterTitle) filterTitle.value = '';
    if (filterMinLength) filterMinLength.value = '';
    if (filterDateFrom) filterDateFrom.value = '';
    if (filterDateTo) filterDateTo.value = '';
    
    // Очищаем поле поиска, если оно есть
    const searchQuery = document.getElementById('searchQuery');
    if (searchQuery) searchQuery.value = '';
    
    // Перезагружаем список документов
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
                
                <!-- КРАТКАЯ СВОДКА -->
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
                    
                    <div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid rgba(255,255,255,0.2); font-size: 13px; opacity: 0.9;">
                        <p style="margin: 0;">💡 Использованы рекурсивные функции: <strong>compare_submissions_recursive()</strong> и <strong>tree_walk_documents()</strong></p>
                    </div>
                </div>

                <!-- ДЕРЕВО СВЯЗЕЙ -->
                <div class="card" style="background: var(--surface-light); margin-bottom: 20px;">
                    <h4 style="margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
                        <span class="material-icons">account_tree</span>
                        Дерево связей документов
                    </h4>
                    <p style="color: var(--text-secondary); font-size: 13px; margin-bottom: 16px;">
                        Самая длинная цепочка связанных документов (${data.document_tree.length} документов)
                    </p>
                    
                    ${data.document_tree.length <= 8 ? `
                        <!-- Полное отображение для коротких цепочек -->
                        <div style="background: var(--background); padding: 20px; border-radius: 12px;">
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
                    ` : `
                        <!-- Компактное отображение для длинных цепочек -->
                        <div style="
                            background: var(--background); 
                            padding: 16px; 
                            border-radius: 10px;
                            font-family: monospace;
                            font-size: 13px;
                            line-height: 1.8;
                            overflow-x: auto;
                        ">
                            ${data.tree_with_titles.map((item, idx) => {
                                const arrow = idx < data.tree_with_titles.length - 1 ? ' → ' : '';
                                return `<span style="
                                    background: linear-gradient(135deg, var(--primary), var(--secondary));
                                    color: white;
                                    padding: 4px 10px;
                                    border-radius: 6px;
                                    white-space: nowrap;
                                ">${item.id}: ${item.title.substring(0, 20)}${item.title.length > 20 ? '...' : ''}</span>${arrow}`;
                            }).join('')}
                        </div>
                        
                        <!-- Кнопка для показа деталей -->
                        <button 
                            class="btn btn-secondary" 
                            style="margin-top: 12px; width: 100%;"
                            onclick="this.nextElementSibling.style.display = this.nextElementSibling.style.display === 'none' ? 'block' : 'none'; this.innerHTML = this.innerHTML.includes('Показать') ? '<span class=\\"material-icons\\">expand_less</span> Скрыть детали' : '<span class=\\"material-icons\\">expand_more</span> Показать детали'">
                            <span class="material-icons">expand_more</span>
                            Показать детали
                        </button>
                        <div style="display: none; margin-top: 16px;">
                            ${data.tree_with_titles.map((item, idx) => `
                                <div style="
                                    padding: 12px;
                                    margin: 8px 0;
                                    background: var(--surface);
                                    border-radius: 8px;
                                    border-left: 3px solid var(--primary);
                                ">
                                    <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 4px;">
                                        Шаг ${idx + 1} / ${data.tree_with_titles.length}
                                    </div>
                                    <div style="font-weight: 600;">
                                        ID ${item.id}: ${item.title}
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    `}
                </div>

                <!-- ТОП-10 ДОКУМЕНТОВ -->
                <div class="card" style="background: var(--surface-light); margin-bottom: 20px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                        <h4 style="margin: 0; display: flex; align-items: center; gap: 8px;">
                            <span class="material-icons">emoji_events</span>
                            Топ-10 документов по схожести
                        </h4>
                        <button 
                            class="btn btn-sm btn-secondary"
                            onclick="
                                const content = this.parentElement.nextElementSibling;
                                const isHidden = content.style.display === 'none';
                                content.style.display = isHidden ? 'block' : 'none';
                                this.innerHTML = isHidden 
                                    ? '<span class=\\'material-icons\\'>expand_less</span> Свернуть'
                                    : '<span class=\\'material-icons\\'>expand_more</span> Развернуть';
                            ">
                            <span class="material-icons">expand_more</span>
                            Развернуть
                        </button>
                    </div>
                    
                    <div style="display: none;">
                        <p style="color: var(--text-secondary); font-size: 13px; margin-bottom: 16px;">
                            Документы с наибольшей схожестью с другими текстами
                        </p>
                        
                        ${(() => {
                            // Создаем массив документов с их названиями
                            const docs = data.all_documents 
                                ? data.similarities.map((sim, idx) => ({
                                    id: data.all_documents[idx]?.id || (idx + 1),
                                    title: data.all_documents[idx]?.title || `Документ ${idx + 1}`,
                                    similarity: sim
                                  }))
                                : data.similarities.map((sim, idx) => ({
                                    id: idx + 1,
                                    title: `Документ ${idx + 1}`,
                                    similarity: sim
                                  }));
                            
                            // Сортируем по убыванию схожести
                            docs.sort((a, b) => b.similarity - a.similarity);
                            
                            // Берем топ-10
                            return docs.slice(0, 10).map((doc, rank) => {
                                const percentage = Math.round(doc.similarity * 100);
                                
                                let barColor, statusText, statusIcon;
                                if (percentage >= 70) {
                                    barColor = '#ef4444';
                                    statusText = 'Плагиат';
                                    statusIcon = '🚨';
                                } else if (percentage >= 30) {
                                    barColor = '#f59e0b';
                                    statusText = 'Похожий';
                                    statusIcon = '⚠️';
                                } else {
                                    barColor = '#10b981';
                                    statusText = 'Оригинал';
                                    statusIcon = '✅';
                                }
                                
                                let medal = '';
                                if (rank === 0) medal = '🥇';
                                else if (rank === 1) medal = '🥈';
                                else if (rank === 2) medal = '🥉';
                                
                                return `
                                    <div style="
                                        display: flex;
                                        align-items: center;
                                        gap: 12px;
                                        padding: 12px;
                                        margin-bottom: 8px;
                                        background: var(--surface);
                                        border-radius: 8px;
                                        border-left: 3px solid ${barColor};
                                        transition: all 0.3s ease;
                                    " onmouseover="this.style.transform='translateX(4px)'" 
                                       onmouseout="this.style.transform='translateX(0)'">
                                        
                                        <div style="
                                            width: 36px;
                                            height: 36px;
                                            border-radius: 50%;
                                            background: linear-gradient(135deg, var(--primary), var(--secondary));
                                            display: flex;
                                            align-items: center;
                                            justify-content: center;
                                            font-size: 16px;
                                            font-weight: 800;
                                            color: white;
                                            flex-shrink: 0;
                                        ">
                                            ${medal || (rank + 1)}
                                        </div>
                                        
                                        <div style="flex: 1; min-width: 0;">
                                            <div style="font-weight: 600; font-size: 14px; margin-bottom: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                                                ${doc.title}
                                            </div>
                                            <div style="font-size: 11px; color: var(--text-muted);">
                                                ID: ${doc.id}
                                            </div>
                                            <div style="
                                                width: 100%;
                                                height: 6px;
                                                background: rgba(148, 163, 184, 0.2);
                                                border-radius: 3px;
                                                overflow: hidden;
                                                margin-top: 6px;
                                            ">
                                                <div style="
                                                    width: ${percentage}%;
                                                    height: 100%;
                                                    background: ${barColor};
                                                    border-radius: 3px;
                                                    transition: width 0.6s ease;
                                                "></div>
                                            </div>
                                        </div>
                                        
                                        <div style="
                                            display: flex;
                                            flex-direction: column;
                                            align-items: flex-end;
                                            gap: 2px;
                                            flex-shrink: 0;
                                        ">
                                            <div style="
                                                font-size: 20px;
                                                font-weight: 800;
                                                color: ${barColor};
                                                line-height: 1;
                                            ">
                                                ${percentage}%
                                            </div>
                                            <div style="
                                                font-size: 10px;
                                                color: var(--text-muted);
                                                display: flex;
                                                align-items: center;
                                                gap: 2px;
                                            ">
                                                <span>${statusIcon}</span>
                                                <span>${statusText}</span>
                                            </div>
                                        </div>
                                    </div>
                                `;
                            }).join('');
                        })()}
                        
                        ${data.similarities.length > 10 ? `
                            <div style="
                                text-align: center;
                                padding: 12px;
                                margin-top: 8px;
                                background: var(--surface);
                                border-radius: 8px;
                                color: var(--text-muted);
                                font-size: 13px;
                            ">
                                <span class="material-icons" style="vertical-align: middle; font-size: 16px;">more_horiz</span>
                                ещё ${data.similarities.length - 10} документов
                            </div>
                        ` : ''}
                    </div>
                </div>

                <!-- СТАТИСТИКА РАСПРЕДЕЛЕНИЯ -->
                <div class="card" style="background: var(--surface-light);">
                    <h4 style="margin-bottom: 16px; display: flex; align-items: center; gap: 8px;">
                        <span class="material-icons">pie_chart</span>
                        Распределение по категориям схожести
                    </h4>
                    
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px;">
                        <div style="
                            padding: 16px;
                            background: var(--surface);
                            border-radius: 10px;
                            border-top: 4px solid #ef4444;
                        ">
                            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                                <span style="font-size: 24px;">🚨</span>
                                <span style="font-weight: 600; color: var(--text);">Плагиат (≥70%)</span>
                            </div>
                            <div style="font-size: 36px; font-weight: 800; color: #ef4444; margin-bottom: 4px;">
                                ${highSimilarities}
                            </div>
                            <div style="font-size: 13px; color: var(--text-muted);">
                                ${Math.round(highSimilarities / data.similarities.length * 100)}% от всех документов
                            </div>
                        </div>
                        
                        <div style="
                            padding: 16px;
                            background: var(--surface);
                            border-radius: 10px;
                            border-top: 4px solid #f59e0b;
                        ">
                            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                                <span style="font-size: 24px;">⚠️</span>
                                <span style="font-weight: 600; color: var(--text);">Похожие (30-70%)</span>
                            </div>
                            <div style="font-size: 36px; font-weight: 800; color: #f59e0b; margin-bottom: 4px;">
                                ${mediumSimilarities}
                            </div>
                            <div style="font-size: 13px; color: var(--text-muted);">
                                ${Math.round(mediumSimilarities / data.similarities.length * 100)}% от всех документов
                            </div>
                        </div>
                        
                        <div style="
                            padding: 16px;
                            background: var(--surface);
                            border-radius: 10px;
                            border-top: 4px solid #10b981;
                        ">
                            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                                <span style="font-size: 24px;">✅</span>
                                <span style="font-weight: 600; color: var(--text);">Оригиналы (<30%)</span>
                            </div>
                            <div style="font-size: 36px; font-weight: 800; color: #10b981; margin-bottom: 4px;">
                                ${lowSimilarities}
                            </div>
                            <div style="font-size: 13px; color: var(--text-muted);">
                                ${Math.round(lowSimilarities / data.similarities.length * 100)}% от всех документов
                            </div>
                        </div>
                    </div>
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
        
        const maxCount = Math.max(...data.authors.map(a => a.document_count));
        
        let html = `
            <div style="margin-top: 24px;">
                <div class="card" style="background: linear-gradient(135deg, var(--primary), var(--secondary)); color: white; margin-bottom: 20px;">
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 16px;">
                        <div>
                            <div style="font-size: 32px; font-weight: 800; margin-bottom: 4px;">
                                ${data.total_authors}
                            </div>
                            <div style="font-size: 13px; opacity: 0.9;">
                                Всего авторов
                            </div>
                        </div>
                        <div>
                            <div style="font-size: 32px; font-weight: 800; margin-bottom: 4px;">
                                ${data.authors.reduce((sum, a) => sum + a.document_count, 0)}
                            </div>
                            <div style="font-size: 13px; opacity: 0.9;">
                                Всего документов
                            </div>
                        </div>
                        <div>
                            <div style="font-size: 32px; font-weight: 800; margin-bottom: 4px;">
                                ${maxCount}
                            </div>
                            <div style="font-size: 13px; opacity: 0.9;">
                                Максимум у одного автора
                            </div>
                        </div>
                    </div>
                </div>
        `;
        
        data.authors.forEach((author, index) => {
            const barWidth = (author.document_count / maxCount) * 100;
            
            let medal = '';
            if (index === 0) medal = '🥇';
            else if (index === 1) medal = '🥈';
            else if (index === 2) medal = '🥉';
            
            html += `
                <div style="
                    padding: 16px;
                    margin-bottom: 12px;
                    background: var(--surface);
                    border-radius: 12px;
                    border-left: 4px solid var(--primary);
                    transition: all 0.3s;
                " onmouseover="this.style.transform='translateX(4px)'" 
                   onmouseout="this.style.transform='translateX(0)'">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <div style="
                                width: 40px;
                                height: 40px;
                                border-radius: 50%;
                                background: linear-gradient(135deg, var(--primary), var(--secondary));
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                font-size: 18px;
                                font-weight: 800;
                                color: white;
                            ">
                                ${medal || (index + 1)}
                            </div>
                            <div>
                                <div style="font-weight: 700; font-size: 16px; margin-bottom: 2px;">
                                    ${author.author}
                                </div>
                                <div style="font-size: 12px; color: var(--text-muted);">
                                    👤 @${author.username}
                                </div>
                            </div>
                        </div>
                        <div style="
                            background: linear-gradient(135deg, var(--primary), var(--secondary));
                            color: white;
                            padding: 8px 16px;
                            border-radius: 20px;
                            font-weight: 700;
                            font-size: 14px;
                        ">
                            ${author.document_count} ${author.document_count === 1 ? 'документ' : author.document_count < 5 ? 'документа' : 'документов'}
                        </div>
                    </div>
                    <div style="
                        width: 100%;
                        height: 8px;
                        background: rgba(148, 163, 184, 0.2);
                        border-radius: 4px;
                        overflow: hidden;
                    ">
                        <div style="
                            height: 100%;
                            width: ${barWidth}%;
                            background: linear-gradient(90deg, var(--primary), var(--secondary));
                            border-radius: 4px;
                            transition: width 0.6s ease;
                        "></div>
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
        btn.innerHTML = '<span class="material-icons">bar_chart</span> Показать статистику';
    }
}
// Остальные функции остаются без изменений...

// Обновляем applyFilters для работы с датами
async function applyFilters() {
    const author = document.getElementById('filterAuthor').value.trim();
    const title = document.getElementById('filterTitle').value.trim();
    const minLength = document.getElementById('filterMinLength').value;
    const dateFrom = document.getElementById('filterDateFrom').value;
    const dateTo = document.getElementById('filterDateTo').value;
    
    let url = `${API_URL}/documents?`;
    
    if (author) url += `author=${encodeURIComponent(author)}&`;
    if (title) url += `title=${encodeURIComponent(title)}&`;
    if (minLength) url += `min_length=${minLength}&`;
    if (dateFrom) url += `date_from=${dateFrom}&`;
    if (dateTo) url += `date_to=${dateTo}&`;
    
    
    try {
        const response = await fetch(url, { credentials: 'include' });
        const docs = await response.json();
        displayDocuments(docs);
    } catch (error) {
        console.error('Ошибка:', error);
    }
}

async function checkDocument(docId) {
    const n = parseInt(document.getElementById('checkN').value) || 3;
    const threshold = parseFloat(document.getElementById('checkThreshold').value) || 0;
    const resultDiv = document.getElementById(`result-${docId}`);
    
    const btn = event.target.closest('button');
    btn.disabled = true;
    btn.innerHTML = '<span class="material-icons rotating">sync</span> Проверка...';
    
    try {
        const response = await fetch(`${API_URL}/check/${docId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ n, threshold })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error);
        }
        
        const percentage = Math.round(data.score * 100);
        const statusClass = percentage < 30 ? 'status-success' : 
                           percentage < 70 ? 'status-warning' : 'status-error';
        const statusText = percentage < 30 ? 'Оригинальный' : 
                          percentage < 70 ? 'Подозрительный' : 'Плагиат!';
        
        let html = `
            <div class="result-card">
                <div class="similarity-circle">${percentage}%</div>
                <h3 style="text-align: center; margin-bottom: 8px;">Результат проверки</h3>
                <div class="status-badge ${statusClass}" style="display: flex; justify-content: center; margin: 0 auto; width: fit-content;">
                    ${statusText}
                </div>
            </div>
            
            ${data.filtered_by_threshold ? `
                <div class="info-box">
                    <p><strong>🎯 Применен порог:</strong> показаны только результаты ≥ ${Math.round(data.filtered_by_threshold * 100)}%</p>
                </div>
            ` : ''}
            
            <div class="info-box">
                <h4>📊 Статистика</h4>
                <p>• Токенов: ${data.stats.tokens}</p>
                <p>• N-грамм: ${data.stats.ngrams}</p>
                <p>• Проверено документов: ${data.stats.documents_checked}</p>
                <p>• Кэш используется: ${data.stats.cache_used ? '✅ Да' : '❌ Нет'}</p>
            </div>
        `;
        
        if (data.matches && data.matches.length > 0) {
            html += '<div class="info-box"><h4>Похожие документы</h4>';
            data.matches.forEach((match, i) => {
                const matchPercent = Math.round(match.similarity * 100);
                const matchStatus = matchPercent < 30 ? 'status-success' : 
                                   matchPercent < 70 ? 'status-warning' : 'status-error';
                html += `
                    <div class="doc-item" style="margin-top: 12px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <div class="doc-title">${i+1}. ${match.doc_title}</div>
                                <div class="doc-meta">👤 ${match.doc_author}</div>
                            </div>
                            <span class="status-badge ${matchStatus}">${matchPercent}%</span>
                        </div>
                    </div>
                `;
            });
            html += '</div>';
        } else if (data.filtered_by_threshold) {
            html += `
                <div class="info-box">
                    <p>⚠️ Нет документов, соответствующих порогу схожести</p>
                </div>
            `;
        }
        
        resultDiv.innerHTML = html;
        
    } catch (error) {
        resultDiv.innerHTML = `
            <div class="info-box" style="border-left: 4px solid var(--error);">
                <p style="color: var(--error);"><strong>❌ Ошибка проверки:</strong> ${error.message}</p>
            </div>
        `;
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<span class="material-icons">search</span> Проверить';
    }
}
