from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODITIONS'] = False

db = SQLAlchemy(app)

# Модели
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(80))
    created_at = db.Column(db.DateTime, default=datetime.now())

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(500))
    content = db.Column(db.Text)
    type = db.Column(db.String(20), default='saved')  # 'saved' или 'verified'
    original_recipe_id = db.Column(db.Integer)  # для verified рецептов
    created_at = db.Column(db.DateTime, default=datetime.now())
    
    # JSON поле для тегов
    tags = db.Column(db.Text, default='[]')  # храним как JSON строку
    
    # JSON поле для заметок
    notes = db.Column(db.Text, default='[]')  # храним как JSON строку

# Создаем таблицы при первом запуске
with app.app_context():
    db.create_all()

# Главная страница
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth_page'))
    return render_template('index.html', username=session.get('username'))

# Страница аутентификации
@app.route('/auth')
def auth_page():
    if 'user_id' in session:
        return redirect(url_for('index'))
    return render_template('auth.html')

# Выйти
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth_page'))

# Регистрация
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'error': 'Need email and password'}), 400
    
    # Проверяем, есть ли такой email
    existing_user = User.query.filter_by(email=data['email']).first()
    if existing_user:
        return jsonify({'error': 'Email exists'}), 400
    
    # Создаем пользователя
    username = data['email'].split('@')[0]
    new_user = User(
        email=data['email'],
        password=data['password'],
        username=username
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({
        'id': new_user.id,
        'email': new_user.email,
        'username': new_user.username
    }), 201

# Вход
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'error': 'Need email and password'}), 400
    
    user = User.query.filter_by(email=data['email'], password=data['password']).first()
    if not user:
        return jsonify({'error': 'Wrong email or password'}), 401
    
    session['user_id'] = user.id
    session['username'] = user.username
    session['email'] = user.email
    
    return jsonify({
        'id': user.id,
        'email': user.email,
        'username': user.username
    }), 200

# Проверить аутентификацию
@app.route('/api/check-auth')
def check_auth():
    if 'user_id' in session:
        return jsonify({'authenticated': True, 'username': session.get('username')}), 200
    return jsonify({'authenticated': False}), 401

# Создать рецепт
@app.route('/api/recipes', methods=['POST'])
def create_recipe():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.json
    
    if not data or 'title' not in data:
        return jsonify({'error': 'Need title'}), 400
    
    # Создаем рецепт
    new_recipe = Recipe(
        user_id=session['user_id'],
        title=data['title'],
        url=data.get('url', ''),
        content=data.get('content', ''),
        type='saved',
        tags=json.dumps(data.get('tags', [])),
        notes=json.dumps([])  # начинаем с пустого списка заметок
    )
    
    db.session.add(new_recipe)
    db.session.commit()
    
    return jsonify({
        'id': new_recipe.id,
        'title': new_recipe.title,
        'type': new_recipe.type
    }), 201

# Получить рецепты пользователя
@app.route('/api/recipes', methods=['GET'])
def get_recipes():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Базовый запрос
    query = Recipe.query.filter_by(user_id=session['user_id'])
    
    # Фильтрация по типу
    recipe_type = request.args.get('type')
    if recipe_type in ['saved', 'verified']:
        query = query.filter_by(type=recipe_type)
    
    # Фильтрация по тегу
    tag = request.args.get('tag')
    if tag:
        query = query.filter(Recipe.tags.contains(f'"{tag}"'))
    
    recipes_list = query.all()
    
    # Преобразуем в словари
    result = []
    for recipe in recipes_list:
        result.append({
            'id': recipe.id,
            'title': recipe.title,
            'type': recipe.type,
            'tags': json.loads(recipe.tags),
            'notes_count': len(json.loads(recipe.notes))
        })
    
    return jsonify({'recipes': result})

# Добавить заметку
@app.route('/api/recipes/<int:recipe_id>/notes', methods=['POST'])
def add_note(recipe_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.json
    
    if not data or 'text' not in data:
        return jsonify({'error': 'Need text'}), 400
    
    recipe = Recipe.query.filter_by(id=recipe_id, user_id=session['user_id']).first()
    if not recipe:
        return jsonify({'error': 'Recipe not found'}), 404
    
    notes = json.loads(recipe.notes)
    
    # При добавлении заметки рецепт перестает быть верифицированным
    if recipe.type == 'verified':
        recipe.type = 'saved'
    
    # Создаем новую заметку
    new_note = {
        'id': len(notes) + 1,
        'text': data['text']
    }
    notes.append(new_note)
    
    # Обновляем рецепт
    recipe.notes = json.dumps(notes)
    db.session.commit()
    
    return jsonify(new_note), 201

# Создать подтвержденную версию
@app.route('/api/recipes/<int:recipe_id>/verify', methods=['POST'])
def verify_recipe(recipe_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    original = Recipe.query.filter_by(id=recipe_id, user_id=session['user_id']).first()
    if not original:
        return jsonify({'error': 'Recipe not found'}), 404
    
    notes = json.loads(original.notes)
    notes_text = "\n".join([f"Note {n['id']}: {n['text']}" for n in notes])
    
    # Создаем верифицированную версию
    verified_recipe = Recipe(
        user_id=session['user_id'],
        title=original.title + " (verified)",
        url=original.url,
        content=original.content + "\n\n---\nNotes:\n" + notes_text,
        type='verified',
        original_recipe_id=original.id,
        tags=original.tags,
        notes=json.dumps([])  # новая версия начинается с чистых заметок
    )
    
    db.session.add(verified_recipe)
    db.session.commit()
    
    return jsonify({
        'id': verified_recipe.id,
        'title': verified_recipe.title,
        'type': verified_recipe.type
    }), 201

# Получить один рецепт (этот уже есть)
@app.route('/api/recipes/<int:recipe_id>', methods=['GET'])
def get_recipe(recipe_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    recipe = Recipe.query.filter_by(id=recipe_id, user_id=session['user_id']).first()
    if not recipe:
        return jsonify({'error': 'Recipe not found'}), 404
    
    return jsonify({
        'id': recipe.id,
        'title': recipe.title,
        'url': recipe.url,
        'content': recipe.content,
        'type': recipe.type,
        'tags': json.loads(recipe.tags),
        'notes': json.loads(recipe.notes),
        'original_recipe_id': recipe.original_recipe_id
    })

# Обновить рецепт
@app.route('/api/recipes/<int:recipe_id>', methods=['PUT'])
def update_recipe(recipe_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.json
    
    recipe = Recipe.query.filter_by(id=recipe_id, user_id=session['user_id']).first()
    if not recipe:
        return jsonify({'error': 'Recipe not found'}), 404
    
    # Обновляем поля
    if 'title' in data:
        recipe.title = data['title']
    if 'url' in data:
        recipe.url = data.get('url', '')
    if 'content' in data:
        recipe.content = data.get('content', '')
    if 'tags' in data:
        recipe.tags = json.dumps(data.get('tags', []))
    
    # При обновлении рецепт перестает быть верифицированным
    if recipe.type == 'verified':
        recipe.type = 'saved'
    
    db.session.commit()
    
    return jsonify({
        'id': recipe.id,
        'title': recipe.title,
        'type': recipe.type
    }), 200

# Удалить рецепт (этот уже есть)
@app.route('/api/recipes/<int:recipe_id>', methods=['DELETE'])
def delete_recipe(recipe_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    recipe = Recipe.query.filter_by(id=recipe_id, user_id=session['user_id']).first()
    if not recipe:
        return jsonify({'error': 'Recipe not found'}), 404
    
    db.session.delete(recipe)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Recipe deleted'})

# Получить все теги пользователя
@app.route('/api/tags')
def get_tags():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Получаем все рецепты пользователя
    user_recipes = Recipe.query.filter_by(user_id=session['user_id']).all()
    
    # Собираем уникальные теги
    all_tags = set()
    
    for recipe in user_recipes:
        tags = json.loads(recipe.tags)
        all_tags.update(tags)
    
    # Считаем количество рецептов для каждого тега
    tags_with_count = []
    for tag in all_tags:
        count = Recipe.query.filter(
            Recipe.user_id == session['user_id'],
            Recipe.tags.contains(f'"{tag}"')
        ).count()
        tags_with_count.append({'name': tag, 'count': count})
    
    return jsonify({'tags': tags_with_count})

# Страница просмотра рецепта
@app.route('/recipe/<int:recipe_id>')
def view_recipe_page(recipe_id):
    if 'user_id' not in session:
        return redirect(url_for('auth_page'))
    return render_template('recipe_view.html', recipe_id=recipe_id)

# Страница редактирования рецепта
@app.route('/recipe/<int:recipe_id>/edit')
def edit_recipe_page(recipe_id):
    if 'user_id' not in session:
        return redirect(url_for('auth_page'))
    return render_template('recipe_edit.html', recipe_id=recipe_id)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)