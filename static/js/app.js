// API Base URL
const API_URL = '/api';

// State
let currentUser = null;
let monitoringEventSource = null;

// Пагинация
let myDocsCurrentPage = 0;
const myDocsPageSize = 10;

// ===== INIT =====
window.addEventListener('DOMContentLoaded', async () => {
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
    // Закрываем мониторинг если был открыт
    if (monitoringEventSource) {
        monitoringEventSource.close();
    }
    
    try {
        await fetch(`${API_URL}/logout`, {
            method: 'POST',
            credentials: 'include'
        });
        
        currentUser = null;
        document.getElementById('loginPage').style.display = 'flex';
        document.getElementById('mainPage').classList.remove('active');
        
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
                <span>Проверка</span>
            </div>
            <div class="menu-item" onclick="showSection('database')">
                <span class="material-icons">storage</span>
                <span>Документы</span>
            </div>
            <div class="menu-item" onclick="showSection('history')">
                <span class="material-icons">history</span>
                <span>История</span>
            </div>
            <div class="menu-item" onclick="showSection('monitoring')">
                <span class="material-icons">monitor_heart</span>
                <span>Мониторинг</span>
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
    if (sectionId === 'my-docs') {
        myDocsCurrentPage = 0;
        renderMyDocuments();
    }
    if (sectionId === 'check') renderCheckPage();
    if (sectionId === 'database') renderAllDocuments();
    if (sectionId === 'history') renderHistory();
    if (sectionId === 'monitoring') startMonitoring();
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
                    <div class="metric-value">${stats.activity_stats?.total_events || 0}</div>
                    <div class="metric-label">Событий</div>
                </div>
            `;
        }
        
        document.getElementById('metricsGrid').innerHTML = metricsHTML;
        
        document.getElementById('dashboardStats').innerHTML = `
            <div class="info-box">
                <h4>💾 Статистика:</h4>
                <p>Размер кэша: ${stats.cache_stats.size} записей</p>
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
            
            const checkResponse = await fetch(`${API_URL}/check-my-document/${docId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ n: 3 })
            });
            
            const checkResult = await checkResponse.json();
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
            </div>
        </div>
    `;
}

// ===== MY DOCUMENTS (USER) =====
async function renderMyDocuments(page = 0) {
    myDocsCurrentPage = page;
    
    try {
        const params = new URLSearchParams({
            page: myDocsCurrentPage,
            page_size: myDocsPageSize
        });
        
        const response = await fetch(`${API_URL}/documents?${params}`, { credentials: 'include' });
        const data = await response.json();
        
        if (data.documents.length === 0 && myDocsCurrentPage === 0) {
            document.getElementById('myDocsContent').innerHTML = `
                <p style="text-align: center; color: var(--text-muted); padding: 40px;">
                    У вас пока нет загруженных документов
                </p>
            `;
            return;
        }
        
        const totalPages = Math.ceil(data.total / myDocsPageSize);
        
        let html = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding: 16px; background: var(--surface-light); border-radius: 12px;">
                <span style="font-weight: 600;">📚 Всего документов: ${data.total}</span>
                <div class="pagination">
                    <button class="btn btn-sm" onclick="renderMyDocuments(${myDocsCurrentPage - 1})" 
                            ${myDocsCurrentPage === 0 ? 'disabled' : ''}>
                        ← Назад
                    </button>
                    <span style="padding: 8px 16px; background: var(--surface); border-radius: 8px;">
                        Страница ${myDocsCurrentPage + 1} из ${totalPages}
                    </span>
                    <button class="btn btn-sm" onclick="renderMyDocuments(${myDocsCurrentPage + 1})" 
                            ${(myDocsCurrentPage + 1) >= totalPages ? 'disabled' : ''}>
                        Вперед →
                    </button>
                </div>
            </div>
        `;
        
        data.documents.forEach(doc => {
            html += `
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
            `;
        });
        
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

// Продолжение в следующем сообщении из-за ограничения длины...

// ===== CHECK PAGE (ADMIN) =====
async function renderCheckPage() {
    document.getElementById('checkContent').innerHTML = `
        <div class="card">
            <h3 class="card-title">
                <span class="material-icons">search</span>
                Проверка документа на плагиат
            </h3>
            
            <div class="form-group">
                <label class="input-label">Текст для проверки</label>
                <textarea class="textarea" id="checkText" placeholder="Вставьте текст для проверки..." rows="6"></textarea>
            </div>
            
            <div class="form-grid">
                <div class="form-group">
                    <label class="input-label">Размер фрагментов (n-граммы)</label>
                    <input type="number" class="input" id="checkN" value="3" min="2" max="5">
                </div>
                <div class="form-group">
                    <label class="input-label">Минимальная схожесть (%)</label>
                    <input type="number" class="input" id="checkThreshold" value="0" min="0" max="100" 
                        placeholder="0 = показать все">
                </div>
            </div>
            
            <button class="btn" onclick="startFullCheck()">
                <span class="material-icons">search</span>
                Начать проверку
            </button>
            
            <div id="checkResults" style="margin-top: 20px;"></div>
        </div>
    `;
}

async function startFullCheck() {
    const text = document.getElementById('checkText').value.trim();
    const n = parseInt(document.getElementById('checkN').value) || 3;
    const threshold = parseFloat(document.getElementById('checkThreshold').value) / 100 || 0.0;
    
    if (!text) {
        alert('Введите текст для проверки');
        return;
    }
    
    const resultsDiv = document.getElementById('checkResults');
    resultsDiv.innerHTML = `
        <div class="result-card">
            <h4 style="display: flex; align-items: center; gap: 8px; margin-bottom: 20px;">
                <span class="material-icons rotating">sync</span>
                <span>Выполняется проверка</span>
            </h4>
            
            <div class="progress-bar" style="height: 12px; margin-bottom: 16px;">
                <div class="progress-fill" id="checkProgress" style="width: 0%;"></div>
            </div>
            
            <div id="progressText" style="text-align: center; color: var(--text-secondary); margin-bottom: 20px;">
                Подготовка...
            </div>
            
            <div id="checkResultsList"></div>
            <div id="finalCheckStats" style="display: none; margin-top: 24px;"></div>
        </div>
    `;
    
    try {
        const response = await fetch(`${API_URL}/plagiarism/check`, {
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
        let allResults = [];
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = JSON.parse(line.slice(6));
                    
                    if (data.status === 'started') {
                        document.getElementById('progressText').textContent = `Начинаем проверку ${data.total} документов...`;
                    } 
                    else if (data.progress !== undefined) {
                        document.getElementById('checkProgress').style.width = `${data.progress}%`;
                        document.getElementById('progressText').textContent = `Проверено: ${data.progress}%`;
                        
                        if (data.similarity > 0) {
                            allResults.push(data);
                            addCheckResult(data);
                        }
                    }
                    else if (data.status === 'completed') {
                        completeCheck(allResults, data.total_results);
                    }
                }
            }
        }
        
    } catch (error) {
        console.error('Check error:', error);
        resultsDiv.innerHTML = `
            <div class="info-box" style="background: rgba(239, 68, 68, 0.1); border-color: var(--error);">
                <p style="color: var(--error);"><strong>❌ Ошибка проверки:</strong> ${error.message}</p>
            </div>
        `;
    }
}

function addCheckResult(result) {
    const container = document.getElementById('checkResultsList');
    
    if (container.children.length === 0) {
        const header = document.createElement('h5');
        header.style.cssText = 'margin: 20px 0 16px; color: var(--text); font-size: 16px;';
        header.innerHTML = '🔍 Найденные совпадения:';
        container.appendChild(header);
    }
    
    const element = document.createElement('div');
    element.className = 'doc-item';
    element.style.cssText = 'animation: slideIn 0.5s cubic-bezier(0.4, 0, 0.2, 1);';
    
    const similarityPercent = (result.similarity * 100).toFixed(1);
    let statusClass = 'status-success';
    let statusIcon = '✅';
    
    if (similarityPercent > 70) {
        statusClass = 'status-error';
        statusIcon = '❌';
    } else if (similarityPercent > 30) {
        statusClass = 'status-warning';
        statusIcon = '⚠️';
    }
    
    element.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div style="flex: 1;">
                <div class="doc-title">${escapeHtml(result.doc_title)}</div>
                <div class="doc-meta">👤 ${escapeHtml(result.doc_author)}</div>
                <div class="progress-bar" style="margin-top: 8px;">
                    <div class="progress-fill" style="width: ${similarityPercent}%;"></div>
                </div>
            </div>
            <div class="status-badge ${statusClass}" style="font-size: 18px; font-weight: 700;">
                ${statusIcon} ${similarityPercent}%
            </div>
        </div>
    `;
    
    container.appendChild(element);
}

function completeCheck(results, totalResults) {
    document.getElementById('checkProgress').style.width = '100%';
    document.getElementById('progressText').innerHTML = `
        <span style="color: var(--success); font-weight: 600;">✅ Проверка завершена!</span>
    `;
    
    results.sort((a, b) => b.similarity - a.similarity);
    
    const maxSimilarity = results.length > 0 ? results[0].similarity : 0;
    const maxPercent = Math.round(maxSimilarity * 100);
    
    let statusClass, statusText, statusColor;
    if (maxPercent < 30) {
        statusClass = 'status-success';
        statusText = 'Текст оригинальный';
        statusColor = 'var(--success)';
    } else if (maxPercent < 70) {
        statusClass = 'status-warning';
        statusText = 'Обнаружены совпадения';
        statusColor = 'var(--warning)';
    } else {
        statusClass = 'status-error';
        statusText = 'Высокая вероятность плагиата';
        statusColor = 'var(--error)';
    }
    
    const highSim = results.filter(r => r.similarity > 0.7).length;
    const medSim = results.filter(r => r.similarity >= 0.3 && r.similarity <= 0.7).length;
    const lowSim = results.filter(r => r.similarity < 0.3).length;
    
    const statsDiv = document.getElementById('finalCheckStats');
    statsDiv.style.display = 'block';
    statsDiv.innerHTML = `
        <div style="background: linear-gradient(135deg, ${statusColor}22, ${statusColor}11); 
                    border: 1px solid ${statusColor}44; 
                    border-radius: 16px; 
                    padding: 24px;
                    text-align: center;">
            
            <div class="similarity-circle" style="width: 180px; height: 180px; font-size: 48px; margin: 0 auto 20px;">
                ${maxPercent}%
            </div>
            
            <div class="status-badge ${statusClass}" style="font-size: 18px; margin-bottom: 20px;">
                ${statusText}
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 16px; margin-top: 24px;">
                <div style="background: var(--surface); padding: 16px; border-radius: 12px;">
                    <div style="font-size: 24px; font-weight: 700; color: var(--error);">${highSim}</div>
                    <div style="font-size: 12px; color: var(--text-muted);">Высокая схожесть</div>
                </div>
                <div style="background: var(--surface); padding: 16px; border-radius: 12px;">
                    <div style="font-size: 24px; font-weight: 700; color: var(--warning);">${medSim}</div>
                    <div style="font-size: 12px; color: var(--text-muted);">Средняя схожесть</div>
                </div>
                <div style="background: var(--surface); padding: 16px; border-radius: 12px;">
                    <div style="font-size: 24px; font-weight: 700; color: var(--success);">${lowSim}</div>
                    <div style="font-size: 12px; color: var(--text-muted);">Низкая схожесть</div>
                </div>
                <div style="background: var(--surface); padding: 16px; border-radius: 12px;">
                    <div style="font-size: 24px; font-weight: 700; color: var(--primary);">${totalResults}</div>
                    <div style="font-size: 12px; color: var(--text-muted);">Всего совпадений</div>
                </div>
            </div>
        </div>
    `;
}

// ===== DOCUMENTS (ADMIN) =====
let currentPage = 0;
const pageSize = 20;
let currentFilters = {};

async function renderAllDocuments() {
    await loadDocuments(0);
}

async function loadDocuments(page = 0) {
    currentPage = page;
    
    try {
        const params = new URLSearchParams({
            page: currentPage,
            page_size: pageSize,
            ...currentFilters
        });
        
        const response = await fetch(`${API_URL}/documents?${params}`, { credentials: 'include' });
        const data = await response.json();
        
        displayDocuments(data.documents, data.total, currentPage);
    } catch (error) {
        console.error('Ошибка загрузки документов:', error);
    }
}

function displayDocuments(docs, total, page) {
    const container = document.getElementById('documentsTable');
    
    if (docs.length === 0) {
        container.innerHTML = `<p style="text-align: center; color: var(--text-muted); padding: 40px;">Документы не найдены</p>`;
        return;
    }
    
    const totalPages = Math.ceil(total / pageSize);
    
    let html = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding: 16px; background: var(--surface-light); border-radius: 12px;">
            <span style="font-weight: 600;">📊 Всего документов: ${total}</span>
            <div class="pagination">
                <button class="btn btn-sm" onclick="loadDocuments(${page - 1})" ${page === 0 ? 'disabled' : ''}>← Назад</button>
                <span style="padding: 8px 16px; background: var(--surface); border-radius: 8px;">Страница ${page + 1} из ${totalPages}</span>
                <button class="btn btn-sm" onclick="loadDocuments(${page + 1})" ${(page + 1) >= totalPages ? 'disabled' : ''}>Вперед →</button>
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
    
    await loadDocuments(0);
}

function clearFilters() {
    document.getElementById('filterAuthor').value = '';
    document.getElementById('filterTitle').value = '';
    document.getElementById('filterMinLength').value = '';
    document.getElementById('filterDateFrom').value = '';
    document.getElementById('filterDateTo').value = '';
    
    currentFilters = {};
    loadDocuments(0);
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
                                👤 ${check.doc_author} • 
                                👨‍💼 ${check.admin_name} • 
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

// ===== MONITORING (ADMIN) =====
async function startMonitoring() {
    // Закрываем предыдущее соединение
    if (monitoringEventSource) {
        monitoringEventSource.close();
    }
    
    document.getElementById('monitoringContent').innerHTML = `
        <div class="card">
            <h3 class="card-title">
                <span class="material-icons">monitor_heart</span>
                Мониторинг в реальном времени
            </h3>
            <p style="color: var(--text-secondary); margin-bottom: 20px;">
                Отслеживание активности системы и подозрительных документов
            </p>
            <div id="monitoringStats"></div>
        </div>
        
        <div class="card" style="margin-top: 20px;">
            <h4 style="margin-bottom: 16px;">📤 Последние загрузки</h4>
            <div id="recentSubmissions"></div>
        </div>
        
        <div class="card" style="margin-top: 20px;">
            <h4 style="margin-bottom: 16px;">✅ Последние проверки</h4>
            <div id="recentChecks"></div>
        </div>
        
        <div class="card" style="margin-top: 20px;">
            <h4 style="margin-bottom: 16px;">⚠️ Требуют внимания</h4>
            <div id="suspiciousMatches"></div>
        </div>
    `;
    
    // Загружаем начальные данные
    await updateMonitoringData();
    
    // Обновляем каждые 5 секунд
    setInterval(updateMonitoringData, 5000);
}

async function updateMonitoringData() {
    try {
        const response = await fetch(`${API_URL}/monitoring/events`, { credentials: 'include' });
        const data = await response.json();
        
        // Статистика
        const stats = data.activity_stats;
        document.getElementById('monitoringStats').innerHTML = `
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 16px;">
                <div style="background: var(--surface-light); padding: 16px; border-radius: 12px; text-align: center;">
                    <div style="font-size: 28px; font-weight: 700; color: var(--primary);">${stats.total_events}</div>
                    <div style="font-size: 13px; color: var(--text-muted);">Всего событий</div>
                </div>
                <div style="background: var(--surface-light); padding: 16px; border-radius: 12px; text-align: center;">
                    <div style="font-size: 28px; font-weight: 700; color: var(--success);">${stats.submissions}</div>
                    <div style="font-size: 13px; color: var(--text-muted);">Загрузок</div>
                </div>
                <div style="background: var(--surface-light); padding: 16px; border-radius: 12px; text-align: center;">
                    <div style="font-size: 28px; font-weight: 700; color: var(--info);">${stats.checks}</div>
                    <div style="font-size: 13px; color: var(--text-muted);">Проверок</div>
                </div>
                <div style="background: var(--surface-light); padding: 16px; border-radius: 12px; text-align: center;">
                    <div style="font-size: 28px; font-weight: 700; color: var(--error);">${stats.alerts}</div>
                    <div style="font-size: 13px; color: var(--text-muted);">Алертов</div>
                </div>
            </div>
        `;
        
        // Последние загрузки
        const submissions = data.recent_submissions.slice(0, 5).map(s => `
            <div style="padding: 12px; background: var(--surface-light); border-radius: 8px; margin-bottom: 8px;">
                <div style="font-weight: 600;">${s.title}</div>
                <div style="font-size: 13px; color: var(--text-muted);">
                    👤 Пользователь: ${s.user_id} • 
                    📅 ${new Date(s.timestamp).toLocaleTimeString('ru-RU')} • 
                    📝 ${s.text_length} символов
                </div>
            </div>
        `).join('');
        document.getElementById('recentSubmissions').innerHTML = submissions || '<p style="text-align: center; color: var(--text-muted);">Нет новых загрузок</p>';
        
        // Последние проверки
        const checks = data.check_results.slice(0, 5).map(c => {
            const percentage = Math.round(c.similarity * 100);
            const statusClass = percentage < 30 ? 'status-success' : percentage < 70 ? 'status-warning' : 'status-error';
            return `
                <div style="padding: 12px; background: var(--surface-light); border-radius: 8px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-weight: 600;">Документ #${c.doc_id}</div>
                        <div style="font-size: 13px; color: var(--text-muted);">
                            📅 ${new Date(c.timestamp).toLocaleTimeString('ru-RU')}
                        </div>
                    </div>
                    <div class="status-badge ${statusClass}">${percentage}%</div>
                </div>
            `;
        }).join('');
        document.getElementById('recentChecks').innerHTML = checks || '<p style="text-align: center; color: var(--text-muted);">Нет проверок</p>';
        
        // Подозрительные
        const suspicious = data.suspicious_matches.slice(0, 5).map(s => {
            const percentage = Math.round(s.similarity * 100);
            return `
                <div style="padding: 12px; background: rgba(239, 68, 68, 0.1); border: 1px solid var(--error); border-radius: 8px; margin-bottom: 8px;">
                    <div style="font-weight: 600; color: var(--error);">⚠️ Документ #${s.doc_id}</div>
                    <div style="font-size: 13px; color: var(--text-muted);">
                        Схожесть: ${percentage}% • 
                        📅 ${new Date(s.timestamp).toLocaleTimeString('ru-RU')}
                    </div>
                </div>
            `;
        }).join('');
        document.getElementById('suspiciousMatches').innerHTML = suspicious || '<p style="text-align: center; color: var(--text-muted);">Подозрительных документов нет</p>';
        
    } catch (error) {
        console.error('Ошибка обновления мониторинга:', error);
    }
}

// ===== UTILS =====
function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
