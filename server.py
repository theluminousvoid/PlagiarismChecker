#!/usr/bin/env python3
"""
PlagiarismChecker API с базой данных и авторизацией
"""

from flask import Flask, jsonify,  request, send_from_directory, session
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
from core.closures import by_author, by_title,  by_min_length, compose_filters, by_date_range, create_similarity_threshold
from core.memo import check_submission_cached, get_cache_stats
from core.ftypes import validate_submission
from core.recursion import compare_submissions_recursive, tree_walk_documents, count_documents_by_author_recursive
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
    
    # Валидация через Either
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
    """Получить документы с фильтрами"""
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
        query = '''
            SELECT d.id, d.title, d.text, d.created_at, u.full_name as author, u.username
            FROM documents d
            JOIN users u ON d.user_id = u.id
            ORDER BY d.created_at DESC
        '''
        c.execute(query)
    
    docs = c.fetchall()
    conn.close()
    
    # Преобразуем в объекты Document для фильтрации
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
        
        # Фильтр по автору
        author = request.args.get('author', '')
        if author:
            filters.append(by_author(author))
            
        title_keyword = request.args.get('title', '')
        if title_keyword:
            filters.append(by_title(title_keyword))
        
        # Фильтр по минимальной длине
        min_length = request.args.get('min_length', 0, type=int)
        if min_length > 0:
            filters.append(by_min_length(min_length))
        
        # НОВОЕ: Фильтр по диапазону дат
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        if date_from and date_to:
            filters.append(by_date_range(date_from, date_to))
        
        # Композиция фильтров
        if filters:
            combined = compose_filters(*filters)
            documents = tuple(filter(combined, documents))
    
    # Форматируем ответ
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
    """Проверить документ на плагиат с настраиваемым порогом"""
    data = request.json
    n = data.get('n', 3)
    threshold = data.get('threshold', 0.0)  # НОВОЕ: порог схожести
    
    conn = get_db()
    c = conn.cursor()
    
    # Получаем проверяемый документ
    c.execute('SELECT * FROM documents WHERE id = ?', (doc_id,))
    doc = c.fetchone()
    
    if not doc:
        conn.close()
        return jsonify({'error': 'Документ не найден'}), 404
    
    # Получаем все остальные документы для сравнения С АВТОРАМИ через JOIN
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
    
    # Преобразуем в объекты Document С АВТОРАМИ
    compare_docs = tuple(
        Document(
            id=str(d['id']),
            title=d['title'],
            text=d['text'],
            author=d['author_name'],  # ← ИСПРАВЛЕНО: теперь берём автора из JOIN
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
    
    # Проверяем с мемоизацией
    result = check_submission_cached(submission, compare_docs, n)
    
    # НОВОЕ: Фильтруем результаты по порогу
    if threshold > 0:
        threshold_filter = create_similarity_threshold(threshold)
        result['matches'] = [
            match for match in result['matches']
            if threshold_filter(match['similarity'])
        ]
        result['filtered_by_threshold'] = threshold
    
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

@app.route('/api/stats/authors', methods=['GET'])
@admin_required
def get_author_stats():
    """
    Статистика по авторам с использованием рекурсии
    Использует count_documents_by_author_recursive()
    """
    conn = get_db()
    c = conn.cursor()
    
    # Получаем всех пользователей
    c.execute('SELECT id, full_name, username FROM users WHERE role = "user"')
    users = c.fetchall()
    
    # Получаем все документы
    c.execute('''
        SELECT d.*, u.full_name as author_name
        FROM documents d
        JOIN users u ON d.user_id = u.id
    ''')
    docs_data = c.fetchall()
    conn.close()
    
    # Преобразуем в объекты Document
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
    
    # Считаем документы для каждого автора РЕКУРСИВНО
    author_stats = []
    for user in users:
        count = count_documents_by_author_recursive(documents, user['full_name'])
        author_stats.append({
            'author': user['full_name'],
            'username': user['username'],
            'document_count': count
        })
    
    # Сортируем по количеству документов
    author_stats.sort(key=lambda x: x['document_count'], reverse=True)
    
    return jsonify({
        'authors': author_stats,
        'total_authors': len(author_stats),
        'method': 'recursive_count'
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
    try:
        conn = get_db()
        c = conn.cursor()
        
        c.execute('SELECT * FROM documents ORDER BY id')
        docs_data = c.fetchall()
        conn.close()
        
        print(f"\n{'='*60}")
        print(f"📊 НАЧАЛО РЕКУРСИВНОГО АНАЛИЗА")
        print(f"📄 Всего документов в базе: {len(docs_data)}")
        print(f"{'='*60}\n")
        
        if len(docs_data) < 2:
            return jsonify({'error': 'Нужно минимум 2 документа'}), 400
        
        # Создаем словарь для быстрого поиска названий
        doc_titles = {}
        for d in docs_data:
            doc_titles[str(d['id'])] = d['title']
            print(f"  ID {d['id']:3d}: {d['title']:40s} ({len(d['text'])} символов)")
        
        print(f"\n{'='*60}\n")
        
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
        print("🔄 Запуск compare_submissions_recursive...")
        similarities = compare_submissions_recursive(submissions, documents, n=3)
        print(f"✅ Схожести рассчитаны: {similarities}\n")
        
        # Рекурсивный обход дерева - пробуем разные стартовые точки
        print("🌳 Поиск самого длинного дерева документов...\n")
        
        best_tree = tuple()
        best_start_idx = 0
        
        # Пробуем начать с КАЖДОГО документа
        for idx in range(len(documents)):
            # Временно отключаем отладочный вывод для других стартов
            import sys
            import io
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()
            
            tree = tree_walk_documents(documents, root=idx, max_depth=15)
            
            # Возвращаем вывод
            sys.stdout = old_stdout
            
            title_short = documents[idx].title[:35] + '...' if len(documents[idx].title) > 35 else documents[idx].title
            print(f"  📍 Старт с индекса {idx:2d} (ID={documents[idx].id:3s}, '{title_short:38s}'): длина = {len(tree)}")
            
            if len(tree) > len(best_tree):
                best_tree = tree
                best_start_idx = idx
                print(f"     ✨ Новый лучший результат!")
        
        doc_tree = best_tree
        
        print(f"\n{'='*60}")
        print(f"🏆 ВЫБРАНО САМОЕ ДЛИННОЕ ДЕРЕВО")
        print(f"   Старт: индекс {best_start_idx} (ID={documents[best_start_idx].id}, '{documents[best_start_idx].title}')")
        print(f"   Длина цепочки: {len(doc_tree)}")
        print(f"{'='*60}")
        
        # Показываем детали лучшего дерева
        print(f"\n🌳 Дерево связей:")
        for i, doc_id in enumerate(doc_tree):
            arrow = " → " if i < len(doc_tree) - 1 else ""
            print(f"   {doc_id}: {doc_titles.get(doc_id, 'Unknown')}{arrow}")
        print()
        
        # Добавляем названия документов
        tree_with_titles = [
            {'id': doc_id, 'title': doc_titles.get(doc_id, 'Unknown')}
            for doc_id in doc_tree
        ]
        
        # ИСПРАВЛЕНИЕ: Добавляем массив all_documents с полной информацией
        all_documents_info = [
            {
                'id': str(d['id']),
                'title': d['title']
            }
            for d in docs_data
        ]
        
        return jsonify({
            'similarities': list(similarities),
            'document_tree': list(doc_tree),
            'tree_with_titles': tree_with_titles,
            'all_documents': all_documents_info,  # ← ДОБАВИЛИ ЭТО!
            'message': 'Анализ завершён'
        })
        
    except Exception as e:
        print(f"\n❌ ОШИБКА: {str(e)}")
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
    
    # Проверяем с мемоизацией
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
