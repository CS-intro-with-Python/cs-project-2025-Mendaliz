from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import json

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Важно: измените в продакшене

# Простое хранилище в памяти
users = []
recipes = []
next_id = 1

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
    for user in users:
        if user['email'] == data['email']:
            return jsonify({'error': 'Email exists'}), 400
    
    global next_id
    user_id = next_id
    next_id += 1
    
    new_user = {
        'id': user_id,
        'email': data['email'],
        'password': data['password'],
        'username': data['email'].split('@')[0]  # Используем часть email как username
    }
    
    users.append(new_user)
    return jsonify({'id': user_id, 'email': data['email'], 'username': new_user['username']}), 201

# Вход
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'error': 'Need email and password'}), 400
    
    for user in users:
        if user['email'] == data['email'] and user['password'] == data['password']:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['email'] = user['email']
            return jsonify({'id': user['id'], 'email': user['email'], 'username': user['username']}), 200
    
    return jsonify({'error': 'Wrong email or password'}), 401

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
    
    global next_id
    recipe_id = next_id
    next_id += 1
    
    new_recipe = {
        'id': recipe_id,
        'user_id': session['user_id'],
        'title': data['title'],
        'url': data.get('url', ''),
        'content': data.get('content', ''),
        'type': 'saved',  # saved или verified
        'tags': data.get('tags', []),
        'notes': []
    }
    
    recipes.append(new_recipe)
    return jsonify(new_recipe), 201

# Получить рецепты пользователя
@app.route('/api/recipes', methods=['GET'])
def get_recipes():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user_id']
    tag = request.args.get('tag')
    recipe_type = request.args.get('type')
    
    filtered = [r for r in recipes if r['user_id'] == user_id]
    
    if tag:
        filtered = [r for r in filtered if tag in r['tags']]
    
    if recipe_type:
        filtered = [r for r in filtered if r['type'] == recipe_type]
    
    return jsonify({'recipes': filtered})

# Добавить заметку
@app.route('/api/recipes/<int:recipe_id>/notes', methods=['POST'])
def add_note(recipe_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.json
    
    if not data or 'text' not in data:
        return jsonify({'error': 'Need text'}), 400
    
    for recipe in recipes:
        if recipe['id'] == recipe_id and recipe['user_id'] == session['user_id']:
            note_id = len(recipe['notes']) + 1
            note = {
                'id': note_id,
                'text': data['text']
            }
            recipe['notes'].append(note)
            return jsonify(note), 201
    
    return jsonify({'error': 'Recipe not found'}), 404

# Создать подтвержденную версию
@app.route('/api/recipes/<int:recipe_id>/verify', methods=['POST'])
def verify_recipe(recipe_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    original = None
    for recipe in recipes:
        if recipe['id'] == recipe_id and recipe['user_id'] == session['user_id']:
            original = recipe
            break
    
    if not original:
        return jsonify({'error': 'Recipe not found'}), 404
    
    global next_id
    new_id = next_id
    next_id += 1
    
    # Создаем улучшенную версию
    notes_text = "\n".join([f"Note {n['id']}: {n['text']}" for n in original['notes']])
    
    new_recipe = {
        'id': new_id,
        'user_id': session['user_id'],
        'title': original['title'] + " (verified)",
        'url': original['url'],
        'content': original['content'] + "\n\n---\nNotes:\n" + notes_text,
        'type': 'verified',
        'tags': original['tags'],
        'notes': [],
        'original_id': recipe_id
    }
    
    recipes.append(new_recipe)
    return jsonify(new_recipe), 201

# Получить один рецепт
@app.route('/api/recipes/<int:recipe_id>', methods=['GET'])
def get_recipe(recipe_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    for recipe in recipes:
        if recipe['id'] == recipe_id and recipe['user_id'] == session['user_id']:
            return jsonify(recipe)
    
    return jsonify({'error': 'Recipe not found'}), 404

# Получить все теги пользователя
@app.route('/api/tags')
def get_tags():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_tags = set()
    for recipe in recipes:
        if recipe['user_id'] == session['user_id']:
            user_tags.update(recipe['tags'])
    
    tags_with_count = []
    for tag in user_tags:
        count = sum(1 for r in recipes if r['user_id'] == session['user_id'] and tag in r['tags'])
        tags_with_count.append({'name': tag, 'count': count})
    
    return jsonify({'tags': tags_with_count})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)