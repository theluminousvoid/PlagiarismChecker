#!/usr/bin/env python3
"""
PlagiarismChecker API с базой данных и авторизацией
"""

from flask import Flask, jsonify, request, send_from_directory, session
from flask_cors import CORS
import sqlite3
import hashlib
import secrets
from datetime import datetime
from pathlib import Path
from functools import wraps

# Импорты из наших модулей
from core.domain import Document, Submission
from core.transforms import normalize, tokenize, ngrams, jaccard
from core.closures import by_author, by_title, by_min_length, compose_filters
from core.memo import check_submission_cached, get_cache_stats
from core.ftypes import validate_submission
from core.recursion import compare_submissions_recursive, tree_walk_documents

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = secrets.token_hex(32)

# Настройки CORS для работы с cookies
CORS(app, 
     supports_credentials=True,
     origins=['http://localhost:5000', 'http://127.0.0.1:5000'],
     allow_headers=['Content-Type'],
     methods=['GET', 'POST', 'OPTIONS'])

# Настройки сессии
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False  # True только для HTTPS

DB_FILE = 'plagiarism.db'

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
    
    # Таблица документов (загруженные пользователями тексты)
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
    
    # Таблица проверок (результаты проверок админами)
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
    
    # Создаём админа по умолчанию
    admin_pass = hash_password('admin123')
    try:
        c.execute('''
            INSERT INTO users (username, password_hash, full_name, role)
            VALUES (?, ?, ?, ?)
        ''', ('admin', admin_pass, 'Администратор', 'admin'))
    except sqlite3.IntegrityError:
        pass  # Админ уже существует
    
    # Создаём тестового пользователя
    user_pass = hash_password('user123')
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
            return jsonify({'error': 'Доступ запрещён. Только для администраторов'}), 403
        return f(*args, **kwargs)
    return decorated_function

# ===== ROUTES =====
@app.route('/')
def index():
    """Главная страница"""
    return send_from_directory('templates', 'index.html')

@app.route('/api/register', methods=['POST'])
def register():
    """Регистрация нового пользователя"""
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
        
        # Автоматический вход после регистрации
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
    """Вход в систему"""
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
    
    # Сохраняем сессию
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
    """Выход из системы"""
    session.clear()
    return jsonify({'message': 'Выход выполнен'})

@app.route('/api/me', methods=['GET'])
@login_required
def get_current_user():
    """Получить текущего пользователя"""
    return jsonify({
        'id': session['user_id'],
        'username': session['username'],
        'full_name': session['full_name'],
        'role': session['role']
    })

@app.route('/api/documents', methods=['POST'])
@login_required
def upload_document():
    """Загрузить документ (только для обычных пользователей)"""
    if session.get('role') != 'user':
        return jsonify({'error': 'Только обычные пользователи могут загружать документы'}), 403
    
    data = request.json
    title = data.get('title', '').strip()
    text = data.get('text', '').strip()
    
    if not title or not text:
        return jsonify({'error': 'Заполните название и текст'}), 400
    
    # Валидация через Either (Лаба №4)
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
    """Получить документы"""
    conn = get_db()
    c = conn.cursor()
    
    # Обычные пользователи видят только свои документы
    # Админы видят все
    if session.get('role') == 'user':
        c.execute('''
            SELECT d.id, d.title, d.text, d.created_at, u.full_name as author
            FROM documents d
            JOIN users u ON d.user_id = u.id
            WHERE d.user_id = ?
            ORDER BY d.created_at DESC
        ''', (session['user_id'],))
    else:
        # Применяем фильтры (Лаба №2: замыкания)
        author = request.args.get('author', '')
        min_length = request.args.get('min_length', 0, type=int)
        
        query = '''
            SELECT d.id, d.title, d.text, d.created_at, u.full_name as author, u.username
            FROM documents d
            JOIN users u ON d.user_id = u.id
            ORDER BY d.created_at DESC
        '''
        c.execute(query)
    
    docs = c.fetchall()
    conn.close()
    
    result = []
    for doc in docs:
        result.append({
            'id': doc['id'],
            'title': doc['title'],
            'text': doc['text'][:200] + '...' if len(doc['text']) > 200 else doc['text'],
            'text_full': doc['text'],
            'author': doc['author'],
            'created_at': doc['created_at']
        })
    
    # Применяем фильтры если админ (Лаба №2)
    if session.get('role') == 'admin':
        author = request.args.get('author', '')
        min_length = request.args.get('min_length', 0, type=int)
        
        if author or min_length > 0:
            filters = []
            if author:
                filters.append(lambda d: author.lower() in d['author'].lower())
            if min_length > 0:
                filters.append(lambda d: len(d['text_full']) >= min_length)
            
            # Композиция фильтров (Лаба №2)
            if filters:
                combined = lambda d: all(f(d) for f in filters)
                result = list(filter(combined, result))
    
    return jsonify(result)

@app.route('/api/check/<int:doc_id>', methods=['POST'])
@admin_required
def check_document(doc_id):
    """Проверить документ на плагиат (только админы)"""
    data = request.json
    n = data.get('n', 3)
    
    conn = get_db()
    c = conn.cursor()
    
    # Получаем проверяемый документ
    c.execute('SELECT * FROM documents WHERE id = ?', (doc_id,))
    doc = c.fetchone()
    
    if not doc:
        conn.close()
        return jsonify({'error': 'Документ не найден'}), 404
    
    # Получаем все остальные документы для сравнения
    c.execute('SELECT * FROM documents WHERE id != ?', (doc_id,))
    other_docs = c.fetchall()
    
    if not other_docs:
        conn.close()
        return jsonify({
            'score': 0.0,
            'matches': [],
            'message': 'Нет документов для сравнения'
        })
    
    # Преобразуем в объекты Document
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
    
    # Создаём Submission
    submission = Submission(
        id=str(doc_id),
        user_id=str(doc['user_id']),
        text=doc['text'],
        ts=doc['created_at']
    )
    
    # Проверяем с мемоизацией (Лаба №3)
    result = check_submission_cached(submission, compare_docs, n)
    
    # Сохраняем результат проверки
    matched_doc_id = int(result['matches'][0]['doc_id']) if result['matches'] else None
    c.execute('''
        INSERT INTO checks (admin_id, document_id, similarity_score, matched_doc_id)
        VALUES (?, ?, ?, ?)
    ''', (session['user_id'], doc_id, result['score'], matched_doc_id))
    
    conn.commit()
    conn.close()
    
    return jsonify(result)

@app.route('/api/stats', methods=['GET'])
@login_required
def get_stats():
    """Статистика системы"""
    conn = get_db()
    c = conn.cursor()
    
    # Общая статистика
    c.execute('SELECT COUNT(*) as count FROM documents')
    total_docs = c.fetchone()['count']
    
    c.execute('SELECT COUNT(*) as count FROM checks')
    total_checks = c.fetchone()['count']
    
    c.execute('SELECT COUNT(*) as count FROM users WHERE role = "user"')
    total_users = c.fetchone()['count']
    
    # Статистика текущего пользователя
    if session.get('role') == 'user':
        c.execute('SELECT COUNT(*) as count FROM documents WHERE user_id = ?', 
                  (session['user_id'],))
        my_docs = c.fetchone()['count']
    else:
        my_docs = 0
    
    conn.close()
    
    return jsonify({
        'total_documents': total_docs,
        'total_checks': total_checks,
        'total_users': total_users,
        'my_documents': my_docs,
        'cache_stats': get_cache_stats()
    })

@app.route('/api/checks/history', methods=['GET'])
@admin_required
def get_checks_history():
    """История проверок (только админы)"""
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

@app.route('/api/analytics/recursive', methods=['GET'])
@admin_required
def analytics_recursive():
    """Рекурсивный анализ (Лаба №2)"""
    try:
        conn = get_db()
        c = conn.cursor()
        
        c.execute('SELECT * FROM documents')
        docs_data = c.fetchall()
        conn.close()
        
        if len(docs_data) < 2:
            return jsonify({'error': 'Нужно минимум 2 документа'}), 400
        
        # Преобразуем в объекты
        documents = []
        submissions = []
        
        for d in docs_data:
            doc = Document(
                id=str(d['id']),
                title=str(d['title']),
                text=str(d['text']),
                author='',
                ts=str(d['created_at'])
            )
            documents.append(doc)
            
            sub = Submission(
                id=str(d['id']),
                user_id=str(d['user_id']),
                text=str(d['text']),
                ts=str(d['created_at'])
            )
            submissions.append(sub)
        
        documents = tuple(documents)
        submissions = tuple(submissions)
        
        # Рекурсивное сравнение
        similarities = compare_submissions_recursive(submissions, documents, n=3)
        
        # Рекурсивный обход дерева
        doc_tree = tree_walk_documents(documents, max_depth=10)
        
        return jsonify({
            'similarities': list(similarities),
            'document_tree': list(doc_tree),
            'message': 'Анализ завершён'
        })
        
    except Exception as e:
        # Логируем ошибку
        print(f"ОШИБКА: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'error': f'Ошибка: {str(e)}'
        }), 500

@app.route('/api/check-my-document/<int:doc_id>', methods=['POST'])
@login_required
def check_my_document(doc_id):
    """Проверить свой документ на плагиат (для обычных пользователей)"""
    data = request.json
    n = data.get('n', 3)
    
    conn = get_db()
    c = conn.cursor()
    
    # Получаем документ пользователя
    c.execute('SELECT * FROM documents WHERE id = ? AND user_id = ?', 
              (doc_id, session['user_id']))
    doc = c.fetchone()
    
    if not doc:
        conn.close()
        return jsonify({'error': 'Документ не найден'}), 404
    
    # Получаем ВСЕ другие документы для сравнения
    c.execute('SELECT * FROM documents WHERE id != ?', (doc_id,))
    other_docs = c.fetchall()
    
    conn.close()
    
    if not other_docs:
        return jsonify({
            'score': 0.0,
            'matches': [],
            'message': 'Нет документов для сравнения'
        })
    
    # Преобразуем в объекты
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
    
    # Создаём Submission
    submission = Submission(
        id=str(doc_id),
        user_id=str(doc['user_id']),
        text=doc['text'],
        ts=doc['created_at']
    )
    
    # Проверяем с мемоизацией (Лаба №3)
    result = check_submission_cached(submission, compare_docs, n)
    
    return jsonify(result)

if __name__ == '__main__':
    print("🚀 Инициализация базы данных...")
    init_db()
    print("✅ База данных готова!")
    print("\n📝 Тестовые аккаунты:")
    print("   Админ: login=admin, password=admin123")
    print("   Пользователь: login=user, password=user123")
    print("\n🚀 PlagiarismChecker API запущен!")
    print("📍 http://localhost:5000")
    print("🛑 Ctrl+C для остановки\n")
    
    app.run(debug=True, port=5000)