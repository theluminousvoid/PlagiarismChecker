#!/usr/bin/env python3
"""
PlagiarismChecker - Коммерческая система проверки на плагиат
Использует функциональное программирование и event-driven архитектуру
"""

from flask import Flask, jsonify, request, send_from_directory, session, Response
from flask_cors import CORS
import sqlite3
import hashlib
import secrets
from datetime import datetime
from pathlib import Path
from functools import wraps
import json
import time

# Импорты из наших модулей
from core.domain import Document, Submission
from core.transforms import normalize, tokenize, ngrams, jaccard
from core.closures import by_author, by_title, by_min_length, compose_filters, by_date_range, create_similarity_threshold
from core.memo import check_submission_cached, get_cache_stats
from core.ftypes import validate_submission
from core.recursion import compare_submissions_recursive, tree_walk_documents, count_documents_by_author_recursive
from core.lazy import paginate_documents, progressive_check, filter_documents, batch_process, search_documents
from core.events import (
    event_bus, 
    setup_event_handlers, 
    get_recent_submissions, 
    get_check_results, 
    get_suspicious_matches,
    get_activity_stats
)

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = secrets.token_hex(32)

# Настройки CORS
CORS(app, 
     supports_credentials=True,
     origins=['http://localhost:5000', 'http://127.0.0.1:5000'],
     allow_headers=['Content-Type'],
     methods=['GET', 'POST', 'OPTIONS'])

# Настройки сессии
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False

DB_FILE = 'plagiarism.db'

# Инициализация обработчиков событий
setup_event_handlers()

# ===== DATABASE SETUP =====
def init_db():
    """Инициализация базы данных"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Таблица пользователей
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('user', 'admin')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Таблица документов
    c.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Таблица проверок
    c.execute('''
        CREATE TABLE IF NOT EXISTS checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER NOT NULL,
            document_id INTEGER NOT NULL,
            similarity_score REAL NOT NULL,
            matched_doc_id INTEGER,
            checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (admin_id) REFERENCES users(id),
            FOREIGN KEY (document_id) REFERENCES documents(id),
            FOREIGN KEY (matched_doc_id) REFERENCES documents(id)
        )
    ''')
    
    # Создаём админа
    admin_pass = hashlib.sha256('admin123'.encode()).hexdigest()
    try:
        c.execute('''
            INSERT INTO users (username, password_hash, full_name, role)
            VALUES (?, ?, ?, ?)
        ''', ('admin', admin_pass, 'Администратор', 'admin'))
    except sqlite3.IntegrityError:
        pass
    
    # Создаём тестового пользователя
    user_pass = hashlib.sha256('user123'.encode()).hexdigest()
    try:
        c.execute('''
            INSERT INTO users (username, password_hash, full_name, role)
            VALUES (?, ?, ?, ?)
        ''', ('user', user_pass, 'Иван Иванов', 'user'))
    except sqlite3.IntegrityError:
        pass
    
    conn.commit()
    conn.close()

def get_db():
    """Получить соединение с БД"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str) -> str:
    """Хэширование пароля"""
    return hashlib.sha256(password.encode()).hexdigest()

# ===== AUTH DECORATORS =====
def login_required(f):
    """Декоратор: требуется авторизация"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Требуется авторизация'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Декоратор: требуется роль админа"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Требуется авторизация'}), 401
        if session.get('role') != 'admin':
            return jsonify({'error': 'Доступ запрещён'}), 403
        return f(*args, **kwargs)
    return decorated_function

# ===== ROUTES =====
@app.route('/')
def index():
    """Главная страница"""
    return send_from_directory('templates', 'index.html')

@app.route('/api/register', methods=['POST'])
def register():
    """Регистрация"""
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '')
    full_name = data.get('full_name', '').strip()
    
    if not username or not password or not full_name:
        return jsonify({'error': 'Заполните все поля'}), 400
    
    if len(username) < 3:
        return jsonify({'error': 'Логин должен быть минимум 3 символа'}), 400
    
    if len(password) < 6:
        return jsonify({'error': 'Пароль должен быть минимум 6 символов'}), 400
    
    conn = get_db()
    c = conn.cursor()
    
    try:
        password_hash = hash_password(password)
        c.execute('''
            INSERT INTO users (username, password_hash, full_name, role)
            VALUES (?, ?, ?, 'user')
        ''', (username, password_hash, full_name))
        conn.commit()
        
        user_id = c.lastrowid
        
        session['user_id'] = user_id
        session['username'] = username
        session['full_name'] = full_name
        session['role'] = 'user'
        
        conn.close()
        
        return jsonify({
            'message': 'Регистрация успешна',
            'user': {
                'id': user_id,
                'username': username,
                'full_name': full_name,
                'role': 'user'
            }
        })
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Пользователь с таким логином уже существует'}), 400

@app.route('/api/login', methods=['POST'])
def login():
    """Вход"""
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'error': 'Введите логин и пароль'}), 400
    
    conn = get_db()
    c = conn.cursor()
    
    password_hash = hash_password(password)
    c.execute('''
        SELECT id, username, full_name, role
        FROM users
        WHERE username = ? AND password_hash = ?
    ''', (username, password_hash))
    
    user = c.fetchone()
    conn.close()
    
    if not user:
        return jsonify({'error': 'Неверный логин или пароль'}), 401
    
    session['user_id'] = user['id']
    session['username'] = user['username']
    session['full_name'] = user['full_name']
    session['role'] = user['role']
    
    return jsonify({
        'message': 'Вход выполнен',
        'user': {
            'id': user['id'],
            'username': user['username'],
            'full_name': user['full_name'],
            'role': user['role']
        }
    })

@app.route('/api/logout', methods=['POST'])
def logout():
    """Выход"""
    session.clear()
    return jsonify({'message': 'Выход выполнен'})

@app.route('/api/me', methods=['GET'])
@login_required
def get_current_user():
    """Текущий пользователь"""
    return jsonify({
        'id': session['user_id'],
        'username': session['username'],
        'full_name': session['full_name'],
        'role': session['role']
    })

@app.route('/api/documents', methods=['POST'])
@login_required
def upload_document():
    """Загрузить документ"""
    if session.get('role') != 'user':
        return jsonify({'error': 'Только обычные пользователи могут загружать документы'}), 403
    
    data = request.json
    title = data.get('title', '').strip()
    text = data.get('text', '').strip()
    
    if not title or not text:
        return jsonify({'error': 'Заполните название и текст'}), 400
    
    # Валидация
    validation = validate_submission(text, min_length=50)
    if validation.is_left():
        return jsonify({'error': validation.get_left()}), 400
    
    conn = get_db()
    c = conn.cursor()
    
    c.execute('''
        INSERT INTO documents (user_id, title, text)
        VALUES (?, ?, ?)
    ''', (session['user_id'], title, text))
    
    doc_id = c.lastrowid
    conn.commit()
    conn.close()
    
    # 🔥 ПУБЛИКУЕМ СОБЫТИЕ: TEXT_SUBMITTED
    event_bus.publish('TEXT_SUBMITTED', {
        'user_id': str(session['user_id']),
        'doc_id': str(doc_id),
        'title': title,
        'text': text,
        'username': session.get('username', 'Unknown')
    })
    
    return jsonify({
        'message': 'Документ загружен',
        'document': {
            'id': doc_id,
            'title': title,
            'text_length': len(text)
        }
    }), 201

@app.route('/api/documents', methods=['GET'])
@login_required
def get_documents():
    """Получить документы с фильтрами и пагинацией"""
    page = request.args.get('page', 0, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    
    conn = get_db()
    c = conn.cursor()
    
    if session.get('role') == 'user':
        c.execute('''
            SELECT d.id, d.title, d.text, d.created_at, u.full_name as author
            FROM documents d
            JOIN users u ON d.user_id = u.id
            WHERE d.user_id = ?
            ORDER BY d.created_at DESC
        ''', (session['user_id'],))
    else:
        c.execute('''
            SELECT d.id, d.title, d.text, d.created_at, u.full_name as author, u.username
            FROM documents d
            JOIN users u ON d.user_id = u.id
            ORDER BY d.created_at DESC
        ''')
    
    docs = c.fetchall()
    conn.close()
    
    documents = tuple(
        Document(
            id=str(doc['id']),
            title=doc['title'],
            text=doc['text'],
            author=doc['author'],
            ts=doc['created_at']
        )
        for doc in docs
    )
    
    # Применяем фильтры
    if session.get('role') == 'admin':
        filters = []
        
        author = request.args.get('author', '')
        if author:
            filters.append(lambda doc: author.lower() in doc.author.lower())
            
        title_keyword = request.args.get('title', '')
        if title_keyword:
            filters.append(lambda doc: title_keyword.lower() in doc.title.lower())
        
        min_length = request.args.get('min_length', 0, type=int)
        if min_length > 0:
            filters.append(lambda doc: len(doc.text) >= min_length)
        
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        if date_from and date_to:
            filters.append(lambda doc: date_from <= doc.ts <= date_to)
        
        if filters:
            def combined_filter(doc):
                return all(predicate(doc) for predicate in filters)
            
            documents = tuple(filter_documents(documents, combined_filter))
    
    # Ленивая пагинация
    paginated_docs = list(paginate_documents(documents, page_size, page))
    
    result = []
    for doc in paginated_docs:
        result.append({
            'id': doc.id,
            'title': doc.title,
            'text': doc.text[:200] + '...' if len(doc.text) > 200 else doc.text,
            'text_full': doc.text,
            'author': doc.author,
            'created_at': doc.ts,
            'length': len(doc.text)
        })
    
    return jsonify({
        'documents': result,
        'total': len(documents),
        'page': page,
        'page_size': page_size
    })

@app.route('/api/plagiarism/check', methods=['POST'])
@login_required
def plagiarism_check():
    """Прогрессивная проверка плагиата"""
    data = request.json
    text = data.get('text', '')
    n = data.get('n', 3)
    threshold = data.get('threshold', 0.0)
    
    if not text:
        return jsonify({'error': 'Текст не может быть пустым'}), 400
    
    conn = get_db()
    c = conn.cursor()
    
    c.execute('''
        SELECT d.id, d.title, d.text, d.created_at, u.full_name as author
        FROM documents d
        JOIN users u ON d.user_id = u.id
    ''')
    docs = c.fetchall()
    conn.close()
    
    documents = tuple(
        Document(
            id=str(doc['id']),
            title=doc['title'],
            text=doc['text'],
            author=doc['author'],
            ts=doc['created_at']
        )
        for doc in docs
    )
    
    def generate():
        results = []
        yield 'data: {"status": "started", "total": ' + str(len(documents)) + '}\n\n'
        
        for result in progressive_check(text, documents, n, threshold):
            results.append(result)
            yield f"data: {json.dumps(result)}\n\n"
        
        yield f"data: {json.dumps({'status': 'completed', 'total_results': len(results)})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/check/<int:doc_id>', methods=['POST'])
@admin_required
def check_document(doc_id):
    """Проверить документ (админ)"""
    data = request.json
    n = data.get('n', 3)
    threshold = data.get('threshold', 0.0)
    
    conn = get_db()
    c = conn.cursor()
    
    c.execute('SELECT * FROM documents WHERE id = ?', (doc_id,))
    doc = c.fetchone()
    
    if not doc:
        conn.close()
        return jsonify({'error': 'Документ не найден'}), 404
    
    c.execute('''
        SELECT d.*, u.full_name as author_name
        FROM documents d
        JOIN users u ON d.user_id = u.id
        WHERE d.id != ?
    ''', (doc_id,))
    other_docs = c.fetchall()
    
    if not other_docs:
        conn.close()
        return jsonify({
            'score': 0.0,
            'matches': [],
            'message': 'Нет документов для сравнения'
        })
    
    compare_docs = tuple(
        Document(
            id=str(d['id']),
            title=d['title'],
            text=d['text'],
            author=d['author_name'],
            ts=d['created_at']
        )
        for d in other_docs
    )
    
    submission = Submission(
        id=str(doc_id),
        user_id=str(doc['user_id']),
        text=doc['text'],
        ts=doc['created_at']
    )
    
    result = check_submission_cached(submission, compare_docs, n)
    
    if threshold > 0:
        threshold_filter = create_similarity_threshold(threshold)
        result['matches'] = [
            match for match in result['matches']
            if threshold_filter(match['similarity'])
        ]
        result['filtered_by_threshold'] = threshold
    
    matched_doc_id = int(result['matches'][0]['doc_id']) if result['matches'] else None
    c.execute('''
        INSERT INTO checks (admin_id, document_id, similarity_score, matched_doc_id)
        VALUES (?, ?, ?, ?)
    ''', (session['user_id'], doc_id, result['score'], matched_doc_id))
    
    conn.commit()
    conn.close()
    
    # 🔥 ПУБЛИКУЕМ СОБЫТИЕ: CHECK_DONE
    event_bus.publish('CHECK_DONE', {
        'doc_id': str(doc_id),
        'doc_title': doc['title'],
        'similarity': result['score'],
        'admin_id': str(session['user_id']),
        'admin_name': session.get('full_name', 'Unknown')
    })
    
    # 🔥 Если высокая схожесть - публикуем ALERT
    if result['score'] > 0.7:
        event_bus.publish('ALERT', {
            'doc_id': str(doc_id),
            'doc_title': doc['title'],
            'similarity': result['score'],
            'severity': 'high' if result['score'] > 0.9 else 'medium',
            'message': f'Обнаружено подозрительное совпадение: {round(result["score"] * 100)}%'
        })
    
    return jsonify(result)

@app.route('/api/stats', methods=['GET'])
@login_required
def get_stats():
    """Статистика системы"""
    conn = get_db()
    c = conn.cursor()
    
    c.execute('SELECT COUNT(*) as count FROM documents')
    total_docs = c.fetchone()['count']
    
    c.execute('SELECT COUNT(*) as count FROM checks')
    total_checks = c.fetchone()['count']
    
    c.execute('SELECT COUNT(*) as count FROM users WHERE role = "user"')
    total_users = c.fetchone()['count']
    
    if session.get('role') == 'user':
        c.execute('SELECT COUNT(*) as count FROM documents WHERE user_id = ?', 
                  (session['user_id'],))
        my_docs = c.fetchone()['count']
    else:
        my_docs = 0
    
    conn.close()
    
    # Добавляем статистику событий
    activity = get_activity_stats()
    
    return jsonify({
        'total_documents': total_docs,
        'total_checks': total_checks,
        'total_users': total_users,
        'my_documents': my_docs,
        'cache_stats': get_cache_stats(),
        'activity_stats': activity
    })

@app.route('/api/monitoring/events', methods=['GET'])
@admin_required
def get_monitoring_events():
    """Получить события для мониторинга (только админы)"""
    return jsonify({
        'recent_submissions': get_recent_submissions(10),
        'check_results': get_check_results(20),
        'suspicious_matches': get_suspicious_matches(0.7),
        'activity_stats': get_activity_stats()
    })

@app.route('/api/monitoring/stream', methods=['GET'])
@admin_required
def monitoring_stream():
    """SSE стрим для real-time мониторинга"""
    def generate():
        # Отправляем текущее состояние
        yield f"data: {json.dumps({'type': 'init', 'data': {
            'recent_submissions': get_recent_submissions(5),
            'check_results': get_check_results(5),
            'suspicious_matches': get_suspicious_matches(0.7)
        }})}\n\n"
        
        # Периодически отправляем обновления
        while True:
            time.sleep(2)
            yield f"data: {json.dumps({'type': 'update', 'data': {
                'activity': get_activity_stats(),
                'timestamp': datetime.now().isoformat()
            }})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/search/documents', methods=['GET'])
@login_required
def search_documents_route():
    """Поиск по документам"""
    query = request.args.get('q', '')
    
    if not query:
        return jsonify({'results': []})
    
    conn = get_db()
    c = conn.cursor()
    
    if session.get('role') == 'user':
        c.execute('''
            SELECT d.id, d.title, d.text, d.created_at, u.full_name as author
            FROM documents d
            JOIN users u ON d.user_id = u.id
            WHERE d.user_id = ?
        ''', (session['user_id'],))
    else:
        c.execute('''
            SELECT d.id, d.title, d.text, d.created_at, u.full_name as author
            FROM documents d
            JOIN users u ON d.user_id = u.id
        ''')
    
    docs = c.fetchall()
    conn.close()
    
    documents = tuple(
        Document(
            id=str(doc['id']),
            title=doc['title'],
            text=doc['text'],
            author=doc['author'],
            ts=doc['created_at']
        )
        for doc in docs
    )
    
    search_results = []
    for doc, relevance in search_documents(documents, query):
        search_results.append({
            'document': {
                'id': doc.id,
                'title': doc.title,
                'text': doc.text[:150] + '...' if len(doc.text) > 150 else doc.text,
                'author': doc.author,
                'created_at': doc.ts
            },
            'relevance': relevance
        })
    
    return jsonify({'results': search_results})

@app.route('/api/checks/history', methods=['GET'])
@admin_required
def get_checks_history():
    """История проверок"""
    conn = get_db()
    c = conn.cursor()
    
    c.execute('''
        SELECT 
            c.id,
            c.similarity_score,
            c.checked_at,
            d.title as doc_title,
            u.full_name as doc_author,
            a.full_name as admin_name
        FROM checks c
        JOIN documents d ON c.document_id = d.id
        JOIN users u ON d.user_id = u.id
        JOIN users a ON c.admin_id = a.id
        ORDER BY c.checked_at DESC
        LIMIT 50
    ''')
    
    checks = c.fetchall()
    conn.close()
    
    result = []
    for check in checks:
        result.append({
            'id': check['id'],
            'similarity_score': round(check['similarity_score'] * 100, 2),
            'checked_at': check['checked_at'],
            'doc_title': check['doc_title'],
            'doc_author': check['doc_author'],
            'admin_name': check['admin_name']
        })
    
    return jsonify(result)

@app.route('/api/check-my-document/<int:doc_id>', methods=['POST'])
@login_required
def check_my_document(doc_id):
    """Проверить свой документ (пользователь)"""
    data = request.json
    n = data.get('n', 3)
    
    conn = get_db()
    c = conn.cursor()
    
    c.execute('SELECT * FROM documents WHERE id = ? AND user_id = ?', 
              (doc_id, session['user_id']))
    doc = c.fetchone()
    
    if not doc:
        conn.close()
        return jsonify({'error': 'Документ не найден'}), 404
    
    c.execute('SELECT * FROM documents WHERE id != ?', (doc_id,))
    other_docs = c.fetchall()
    
    conn.close()
    
    if not other_docs:
        return jsonify({
            'score': 0.0,
            'matches': [],
            'message': 'Нет документов для сравнения'
        })
    
    check_doc = Document(
        id=str(doc['id']),
        title=doc['title'],
        text=doc['text'],
        author='',
        ts=doc['created_at']
    )
    
    compare_docs = tuple(
        Document(
            id=str(d['id']),
            title=d['title'],
            text=d['text'],
            author='',
            ts=d['created_at']
        )
        for d in other_docs
    )
    
    submission = Submission(
        id=str(doc_id),
        user_id=str(doc['user_id']),
        text=doc['text'],
        ts=doc['created_at']
    )
    
    result = check_submission_cached(submission, compare_docs, n)
    
    return jsonify(result)

if __name__ == '__main__':
    print("🚀 Инициализация базы данных...")
    init_db()
    print("✅ База данных готова!")
    print("\n📝 Тестовые аккаунты:")
    print("   Админ: login=admin, password=admin123")
    print("   Пользователь: login=user, password=user123")
    print("\n🚀 PlagiarismChecker запущен!")
    print("📍 http://localhost:5000")
    print("🛑 Ctrl+C для остановки\n")
    
    app.run(debug=True, port=5000)
