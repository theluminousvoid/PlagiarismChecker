#!/usr/bin/env python3
"""
PlagiarismChecker API с базой данных, авторизацией и ленивыми вычислениями
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
from core.closures import by_author, by_title, by_min_length, compose_filters, by_date_range, create_similarity_threshold
from core.memo import check_submission_cached, get_cache_stats
from core.ftypes import validate_submission
from core.recursion import compare_submissions_recursive, tree_walk_documents, count_documents_by_author_recursive
from core.lazy import lazy_compare_documents, lazy_paginate_documents, lazy_search_documents  # ← НОВОЕ

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
    
    # Создаём тестовые аккаунты
    admin_pass = hash_password('admin123')
    user_pass = hash_password('user123')
    
    try:
        c.execute('''
            INSERT INTO users (username, password_hash, full_name, role)
            VALUES (?, ?, ?, ?)
        ''', ('admin', admin_pass, 'Администратор', 'admin'))
    except sqlite3.IntegrityError:
        pass
    
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
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Требуется авторизация'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
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
    return send_from_directory('templates', 'index.html')

@app.route('/api/register', methods=['POST'])
def register():
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
        
        # Автоматический вход
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
        return jsonify({'error': 'Пользователь уже существует'}), 400

@app.route('/api/login', methods=['POST'])
def login():
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
    session.clear()
    return jsonify({'message': 'Выход выполнен'})

@app.route('/api/me', methods=['GET'])
@login_required
def get_current_user():
    return jsonify({
        'id': session['user_id'],
        'username': session['username'],
        'full_name': session['full_name'],
        'role': session['role']
    })

@app.route('/api/documents', methods=['POST'])
@login_required
def upload_document():
    if session.get('role') != 'user':
        return jsonify({'error': 'Только пользователи могут загружать документы'}), 403
    
    data = request.json
    title = data.get('title', '').strip()
    text = data.get('text', '').strip()
    
    if not title or not text:
        return jsonify({'error': 'Заполните все поля'}), 400
    
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
    
    # Применяем фильтры для админов
    if session.get('role') == 'admin':
        filters = []
        
        author = request.args.get('author', '')
        if author:
            filters.append(by_author(author))
        
        title = request.args.get('title', '')
        if title:
            filters.append(by_title(title))
        
        min_length = request.args.get('min_length', 0, type=int)
        if min_length > 0:
            filters.append(by_min_length(min_length))
        
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        if date_from and date_to:
            filters.append(by_date_range(date_from, date_to))
        
        if filters:
            combined = compose_filters(*filters)
            documents = tuple(filter(combined, documents))
    
    result = []
    for doc in documents:
        result.append({
            'id': doc.id,
            'title': doc.title,
            'text': doc.text[:200] + '...' if len(doc.text) > 200 else doc.text,
            'text_full': doc.text,
            'author': doc.author,
            'created_at': doc.ts
        })
    
    return jsonify(result)

@app.route('/api/check/<int:doc_id>', methods=['POST'])
@admin_required
def check_document(doc_id):
    """
    🚀 УЛУЧШЕННАЯ ПРОВЕРКА С ЛЕНИВЫМИ ВЫЧИСЛЕНИЯМИ
    Теперь использует генераторы для постепенной обработки
    """
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
    conn.close()
    
    if not other_docs:
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
    
    # 🚀 ИСПОЛЬЗУЕМ ЛЕНИВЫЕ ВЫЧИСЛЕНИЯ
    # Сравниваем постепенно, фильтруя по порогу на лету
    results = []
    for result in lazy_compare_documents(doc['text'], compare_docs, n, threshold):
        results.append({
            'doc_id': result['doc_id'],
            'doc_title': result['doc_title'],
            'doc_author': result['doc_author'],
            'similarity': result['similarity']
        })
    
    results.sort(key=lambda x: x['similarity'], reverse=True)
    max_similarity = results[0]['similarity'] if results else 0.0
    
    # Сохраняем результат
    matched_doc_id = int(results[0]['doc_id']) if results else None
    
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        INSERT INTO checks (admin_id, document_id, similarity_score, matched_doc_id)
        VALUES (?, ?, ?, ?)
    ''', (session['user_id'], doc_id, max_similarity, matched_doc_id))
    conn.commit()
    conn.close()
    
    # Статистика
    sub_normalized = normalize(doc['text'])
    sub_tokens = tokenize(sub_normalized)
    sub_ngrams = ngrams(sub_tokens, n)
    
    return jsonify({
        'score': max_similarity,
        'matches': results[:5],
        'filtered_by_threshold': threshold if threshold > 0 else None,
        'stats': {
            'tokens': len(sub_tokens),
            'ngrams': len(sub_ngrams),
            'documents_checked': len(compare_docs),
            'cache_used': False  # Ленивые вычисления не используют кэш
        }
    })

@app.route('/api/stats', methods=['GET'])
@login_required
def get_stats():
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
    
    return jsonify({
        'total_documents': total_docs,
        'total_checks': total_checks,
        'total_users': total_users,
        'my_documents': my_docs,
        'cache_stats': get_cache_stats()
    })

@app.route('/api/stats/authors', methods=['GET'])
@admin_required
def get_author_stats():
    conn = get_db()
    c = conn.cursor()
    
    c.execute('SELECT id, full_name, username FROM users WHERE role = "user"')
    users = c.fetchall()
    
    c.execute('''
        SELECT d.*, u.full_name as author_name
        FROM documents d
        JOIN users u ON d.user_id = u.id
    ''')
    docs_data = c.fetchall()
    conn.close()
    
    documents = tuple(
        Document(
            id=str(d['id']),
            title=d['title'],
            text=d['text'],
            author=d['author_name'],
            ts=d['created_at']
        )
        for d in docs_data
    )
    
    author_stats = []
    for user in users:
        count = count_documents_by_author_recursive(documents, user['full_name'])
        author_stats.append({
            'author': user['full_name'],
            'username': user['username'],
            'document_count': count
        })
    
    author_stats.sort(key=lambda x: x['document_count'], reverse=True)
    
    return jsonify({
        'authors': author_stats,
        'total_authors': len(author_stats),
        'method': 'recursive_count'
    })

@app.route('/api/checks/history', methods=['GET'])
@admin_required
def get_checks_history():
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
    try:
        conn = get_db()
        c = conn.cursor()
        
        c.execute('SELECT * FROM documents ORDER BY id')
        docs_data = c.fetchall()
        conn.close()
        
        if len(docs_data) < 2:
            return jsonify({'error': 'Нужно минимум 2 документа'}), 400
        
        doc_titles = {}
        for d in docs_data:
            doc_titles[str(d['id'])] = d['title']
        
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
        
        # Поиск лучшего дерева
        best_tree = tuple()
        best_start_idx = 0
        
        for idx in range(len(documents)):
            tree = tree_walk_documents(documents, root=idx, max_depth=15)
            if len(tree) > len(best_tree):
                best_tree = tree
                best_start_idx = idx
        
        doc_tree = best_tree
        
        tree_with_titles = [
            {'id': doc_id, 'title': doc_titles.get(doc_id, 'Unknown')}
            for doc_id in doc_tree
        ]
        
        all_documents_info = [
            {'id': str(d['id']), 'title': d['title']}
            for d in docs_data
        ]
        
        return jsonify({
            'similarities': list(similarities),
            'document_tree': list(doc_tree),
            'tree_with_titles': tree_with_titles,
            'all_documents': all_documents_info,
            'message': 'Анализ завершён'
        })
        
    except Exception as e:
        return jsonify({'error': f'Ошибка: {str(e)}'}), 500

@app.route('/api/check-my-document/<int:doc_id>', methods=['POST'])
@login_required
def check_my_document(doc_id):
    """
    🚀 УЛУЧШЕННАЯ ПРОВЕРКА ДЛЯ ПОЛЬЗОВАТЕЛЕЙ С ЛЕНИВЫМИ ВЫЧИСЛЕНИЯМИ
    """
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
    
    # 🚀 ИСПОЛЬЗУЕМ ЛЕНИВЫЕ ВЫЧИСЛЕНИЯ
    results = []
    for result in lazy_compare_documents(doc['text'], compare_docs, n, 0.0):
        results.append({
            'doc_id': result['doc_id'],
            'doc_title': result['doc_title'],
            'doc_author': result['doc_author'],
            'similarity': result['similarity']
        })
    
    results.sort(key=lambda x: x['similarity'], reverse=True)
    max_similarity = results[0]['similarity'] if results else 0.0
    
    sub_normalized = normalize(doc['text'])
    sub_tokens = tokenize(sub_normalized)
    sub_ngrams = ngrams(sub_tokens, n)
    
    return jsonify({
        'score': max_similarity,
        'matches': results[:5],
        'stats': {
            'tokens': len(sub_tokens),
            'ngrams': len(sub_ngrams),
            'documents_checked': len(compare_docs),
            'cache_used': False
        }
    })

if __name__ == '__main__':
    print("🚀 Инициализация базы данных...")
    init_db()
    print("✅ База данных готова!")
    print("\n📝 Тестовые аккаунты:")
    print("   Админ: login=admin, password=admin123")
    print("   Пользователь: login=user, password=user123")
    print("\n🚀 PlagiarismChecker API запущен!")
    print("📍 http://localhost:5000")
    print("🚀 Используются ленивые вычисления для оптимизации!")
    print("🛑 Ctrl+C для остановки\n")
    
    app.run(debug=True, port=5000)
