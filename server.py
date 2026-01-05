from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(80))
    created_at = db.Column(db.DateTime, default=datetime.now)

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    rate = db.Column(db.SmallInteger, default=5)
    url = db.Column(db.String(500))
    description = db.Column(db.Text)
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    tags = db.Column(db.Text, default='[]')

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth_page'))
    return render_template('index.html', username=session.get('username'))

@app.route('/auth')
def auth_page():
    if 'user_id' in session:
        return redirect(url_for('index'))
    return render_template('auth.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth_page'))

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'error': 'Need email and password'}), 400
    
    existing_user = User.query.filter_by(email=data['email']).first()
    if existing_user:
        return jsonify({'error': 'Email exists'}), 400
    
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

@app.route('/api/check-auth')
def check_auth():
    if 'user_id' in session:
        return jsonify({'authenticated': True, 'username': session.get('username')}), 200
    return jsonify({'authenticated': False}), 401

@app.route('/api/recipes', methods=['POST'])
def create_recipe():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.json
    
    if not data or 'title' not in data:
        return jsonify({'error': 'Need title'}), 400
    
    new_recipe = Recipe(
        user_id=session['user_id'],
        title=data['title'],
        rate=data.get('rate', 5),
        url=data.get('url', ''),
        description=data.get('description', ''),
        content=data.get('content', ''),
        tags=json.dumps(data.get('tags', []))
    )
    
    db.session.add(new_recipe)
    db.session.commit()
    
    return jsonify({
        'id': new_recipe.id,
        'title': new_recipe.title,
        'rate': new_recipe.rate
    }), 201

@app.route('/api/recipes', methods=['GET'])
def get_recipes():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    query = Recipe.query.filter_by(user_id=session['user_id']).order_by(Recipe.rate.desc())
    
    tags = request.args.get('tags')
    if tags:
        for tag in tags.split(','):
            query = query.filter(Recipe.tags.contains(f'"{tag}"'))
    
    recipes_list = query.all()
    
    result = []
    for recipe in recipes_list:
        result.append({
            'id': recipe.id,
            'title': recipe.title,
            'rate': recipe.rate,
            'description': recipe.description,
            'tags': json.loads(recipe.tags),
            'created_at': recipe.created_at.strftime('%Y-%m-%d %H:%M')
        })
    
    return jsonify({'recipes': result})

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
        'rate': recipe.rate,
        'url': recipe.url,
        'description': recipe.description,
        'content': recipe.content,
        'tags': json.loads(recipe.tags),
        'created_at': recipe.created_at.strftime('%Y-%m-%d %H:%M')
    })

@app.route('/api/recipes/<int:recipe_id>', methods=['PUT'])
def update_recipe(recipe_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.json
    
    recipe = Recipe.query.filter_by(id=recipe_id, user_id=session['user_id']).first()
    if not recipe:
        return jsonify({'error': 'Recipe not found'}), 404
    
    recipe.title = data.get('title', recipe.title)
    recipe.rate = data.get('rate', recipe.rate)
    recipe.url = data.get('url', recipe.url)
    recipe.description = data.get('description', recipe.description)
    recipe.content = data.get('content', recipe.content)
    recipe.tags = json.dumps(data.get('tags', []))
    
    db.session.commit()
    
    return jsonify({
        'id': recipe.id,
        'title': recipe.title,
        'rate': recipe.rate
    }), 200

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

@app.route('/api/tags')
def get_tags():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_recipes = Recipe.query.filter_by(user_id=session['user_id']).all()
    
    all_tags = set()
    
    for recipe in user_recipes:
        tags = json.loads(recipe.tags)
        all_tags.update(tags)
    
    tags_with_count = []
    for tag in all_tags:
        count = Recipe.query.filter(
            Recipe.user_id == session['user_id'],
            Recipe.tags.contains(f'"{tag}"')
        ).count()
        tags_with_count.append({'name': tag, 'count': count})
    
    return jsonify({'tags': tags_with_count})

@app.route('/recipe/<int:recipe_id>')
def view_recipe_page(recipe_id):
    if 'user_id' not in session:
        return redirect(url_for('auth_page'))
    return render_template('recipe_view.html', recipe_id=recipe_id)

@app.route('/recipe/<int:recipe_id>/edit')
def edit_recipe_page(recipe_id):
    if 'user_id' not in session:
        return redirect(url_for('auth_page'))
    return render_template('recipe_edit.html', recipe_id=recipe_id)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)