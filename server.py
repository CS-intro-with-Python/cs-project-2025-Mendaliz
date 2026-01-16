from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from functools import wraps


def setup_sql_logger(app):
    """Logs for SQL requests"""
    
    if not os.path.exists('logs'):
        os.makedirs('logs')
        
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - [%(levelname)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    app_logger = app.logger
    app_logger.handlers.clear()
    app_logger.setLevel(logging.INFO)
    
    app_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=5*1024*1024,
        backupCount=3
    )
    app_handler.setFormatter(formatter)
    app_logger.addHandler(app_handler)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    app_logger.addHandler(console_handler)
    
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.INFO)
    werkzeug_logger.propagate = False
    
    werkzeug_handler = RotatingFileHandler(
        'logs/werkzeug.log',
        maxBytes=10*1024*1024,
        backupCount=5
    )
    werkzeug_handler.setFormatter(formatter)
    werkzeug_logger.addHandler(werkzeug_handler)
    
    sql_logger = logging.getLogger('sqlalchemy.engine')
    sql_logger.setLevel(logging.DEBUG)
    sql_logger.propagate = False
    
    sql_handler = RotatingFileHandler(
        'logs/sql.log',
        maxBytes=10*1024*1024,
        backupCount=5
    )
    sql_handler.setFormatter(formatter)
    sql_logger.addHandler(sql_handler)

def log_response(func):
    """Decorator for logging requests"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        app.logger.info(f"Request to {request.path} - Method: {request.method}")
        
        response = func(*args, **kwargs)
        
        if isinstance(response, tuple) and len(response) == 2:
            data, status = response
            app.logger.info(f"Response from {request.path} - Status: {status}")
            if status >= 400:
                app.logger.error(f"Error response: {data.get_data(as_text=True).rstrip()}")
        else:
            app.logger.info(f"Response from {request.path}")
        
        return response
    return wrapper

app = Flask(__name__)
app.secret_key = 'my-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

setup_sql_logger(app)

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
    url = db.Column(db.String(500))
    description = db.Column(db.Text)
    ingredients = db.Column(db.Text, default='[]')
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    tags = db.Column(db.Text, default='[]')
    rate = db.Column(db.SmallInteger, default=5)

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

@app.route('/recipe/<int:recipe_id>')
def view_recipe_page(recipe_id):
    if 'user_id' not in session:
        return redirect(url_for('auth_page'))
    return render_template('recipe_view.html', username=session.get('username'), recipe_id=recipe_id)

@app.route('/recipe/<int:recipe_id>/edit')
def edit_recipe_page(recipe_id):
    if 'user_id' not in session:
        return redirect(url_for('auth_page'))
    return render_template('recipe_edit.html', username=session.get('username'), recipe_id=recipe_id)

@app.route('/recipe/checklist')
def view_checklist():
    if 'user_id' not in session:
        return redirect(url_for('auth_page'))
    return render_template('checklist_view.html', username=session.get('username'))

@app.route('/api/register', methods=['POST'])
@log_response
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
@log_response
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

@log_response
@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    if 'user_id' in session:
        return jsonify({'authenticated': True, 'username': session.get('username')}), 200
    return jsonify({'authenticated': False}), 401

@log_response
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
    
    return jsonify({'recipes': result}), 200

@app.route('/api/recipes', methods=['POST'])
@log_response
def create_recipe():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.json
    
    if not data or 'title' not in data:
        return jsonify({'error': 'Need title'}), 400
    
    new_recipe = Recipe(
        user_id=session['user_id'],
        title=data['title'],
        url=data.get('url', ''),
        description=data.get('description', ''),
        ingredients=json.dumps(data.get('ingredients', [])),
        content=data.get('content', ''),
        tags=json.dumps(data.get('tags', [])),
        rate=data.get('rate', 5)
    )
    
    db.session.add(new_recipe)
    db.session.commit()
    
    return jsonify({
        'id': new_recipe.id,
        'title': new_recipe.title,
        'rate': new_recipe.rate
    }), 201

@app.route('/api/recipes/<int:recipe_id>', methods=['GET'])
@log_response
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
        'ingredients': json.loads(recipe.ingredients),
        'content': recipe.content,
        'tags': json.loads(recipe.tags),
        'created_at': recipe.created_at.strftime('%Y-%m-%d %H:%M')
    }), 200

@app.route('/api/recipes/<int:recipe_id>', methods=['PUT'])
@log_response
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
    recipe.ingredients = json.dumps(data.get('ingredients', []))
    recipe.content = data.get('content', recipe.content)
    recipe.tags = json.dumps(data.get('tags', []))
    
    db.session.commit()
    
    return jsonify({
        'id': recipe.id,
        'title': recipe.title,
        'rate': recipe.rate
    }), 200

@app.route('/api/recipes/<int:recipe_id>', methods=['DELETE'])
@log_response
def delete_recipe(recipe_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    recipe = Recipe.query.filter_by(id=recipe_id, user_id=session['user_id']).first()
    if not recipe:
        return jsonify({'error': 'Recipe not found'}), 404
    
    db.session.delete(recipe)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Recipe deleted'}), 200

@app.route('/api/tags')
@log_response
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
    
    return jsonify({'tags': tags_with_count}), 200

@app.route('/api/meals')
@log_response
def get_meals():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    recipe_ids = request.args.get('recipe_ids')
    if recipe_ids is None:
        return jsonify({}), 400
    recipe_ids = recipe_ids.split(',')
    user_recipes = Recipe.query.filter_by(user_id=session['user_id']).filter(Recipe.id.in_(recipe_ids)).all()
    ingredients = []
    
    for recipe in user_recipes:
        recipe_ingredients = json.loads(recipe.ingredients)
        for ingredient in recipe_ingredients:
            added = 0
            name = ingredient.get('name', '')
            amount = ingredient.get('amount', 0)
            unit = ingredient.get('unit', '')
            for i in range(len(ingredients)):
                prep = ingredients[i]
                if prep['name'] == name and prep['unit'] == unit:
                    try:
                        int(prep['amount']), int(amount)
                        prep['amount'] += int(amount)
                        added = 1
                    except:
                        pass
            if added == 0:
                try:
                    amount = int(amount)
                except:
                    pass
                ingredients.append({'name': name, 'amount': amount, 'unit': unit})
    
    return jsonify({"meals": sorted(ingredients, key=lambda t: (t['name'], t['unit']))}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)