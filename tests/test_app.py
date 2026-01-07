import pytest
import json
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from server import app, db, User, Recipe

# =================== FIXTURES ===================

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

@pytest.fixture
def test_user(client):
    user = User(
        email='test@example.com',
        password='testpass123',
        username='testuser'
    )
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def test_recipe(test_user):
    recipe = Recipe(
        user_id=test_user.id,
        title='Test Recipe',
        description='Test description',
        url='https://example.com',
        ingredients=json.dumps([
            {'name': 'Flour', 'amount': 200, 'unit': 'g'},
            {'name': 'Sugar', 'amount': 100, 'unit': 'g'}
        ]),
        content='Test content',
        tags=json.dumps(['test', 'baking']),
        rate=5
    )
    db.session.add(recipe)
    db.session.commit()
    return recipe

@pytest.fixture
def auth_headers(client, test_user):
    with client.session_transaction() as sess:
        sess['user_id'] = test_user.id
        sess['username'] = test_user.username
        sess['email'] = test_user.email
    
    return {'Content-Type': 'application/json'}

# =================== UNIT TESTS - MODELS ===================

class TestModels:
    def test_user_creation(self, test_user):
        assert test_user.id is not None
        assert test_user.email == 'test@example.com'
        assert test_user.username == 'testuser'
        assert test_user.password == 'testpass123'
        assert isinstance(test_user.created_at, datetime)
    
    def test_recipe_creation(self, test_recipe):
        assert test_recipe.id is not None
        assert test_recipe.title == 'Test Recipe'
        assert test_recipe.rate == 5
        assert isinstance(test_recipe.created_at, datetime)
        
        ingredients = json.loads(test_recipe.ingredients)
        assert isinstance(ingredients, list)
        assert len(ingredients) == 2
        assert ingredients[0]['name'] == 'Flour'
        
        tags = json.loads(test_recipe.tags)
        assert isinstance(tags, list)
        assert 'test' in tags
        assert 'baking' in tags
    
    def test_recipe_user_relationship(self, test_user, test_recipe):
        assert test_recipe.user_id == test_user.id
        
        user_recipes = Recipe.query.filter_by(user_id=test_user.id).all()
        assert len(user_recipes) > 0
        assert test_recipe in user_recipes

# =================== UNIT TESTS - INPUT VALIDATION ===================

class TestInputValidation:
    @pytest.mark.parametrize('ingredients_input,expected_count', [
        ([{'name': 'Flour', 'amount': 200, 'unit': 'g'}], 1),
        ([
            {'name': 'Flour', 'amount': 200, 'unit': 'g'},
            {'name': 'Sugar', 'amount': 100, 'unit': 'g'},
            {'name': 'Eggs', 'amount': 2, 'unit': 'pieces'}
        ], 3),
    ])
    def test_ingredients_format_validation(self, client, auth_headers, test_user,
                                         ingredients_input, expected_count):
        with client.session_transaction() as sess:
            sess['user_id'] = test_user.id
        
        test_data = {
            'title': 'Test Recipe',
            'ingredients': ingredients_input
        }
        
        response = client.post('/api/recipes',
                             json=test_data,
                             headers=auth_headers)
        
        if response.status_code == 201:
            response_data = response.get_json()
            assert 'id' in response_data
            
            recipe = Recipe.query.get(response_data['id'])
            ingredients = json.loads(recipe.ingredients)
            assert len(ingredients) == expected_count

# =================== UNIT TESTS - ERROR HANDLING ===================

class TestErrorHandling:
    def test_unauthorized_access_to_protected_endpoints(self, client):
        """Endpoint secure"""
        endpoints = [
            ('/api/recipes', 'GET'),
            ('/api/recipes', 'POST'),
            ('/api/recipes/1', 'GET'),
            ('/api/recipes/1', 'PUT'),
            ('/api/recipes/1', 'DELETE'),
            ('/api/tags', 'GET'),
            ('/api/meals', 'GET'),
        ]
        
        for endpoint, method in endpoints:
            if method == 'GET':
                response = client.get(endpoint)
            elif method == 'POST':
                response = client.post(endpoint)
            elif method == 'PUT':
                response = client.put(endpoint)
            elif method == 'DELETE':
                response = client.delete(endpoint)
            
            assert response.status_code == 401
            data = response.get_json()
            assert 'error' in data
            assert data['error'] == 'Not authenticated'
    
    def test_invalid_login_credentials(self, client, test_user):
        """Incorrect ligin"""
        response = client.post('/api/login',
                             json={'email': 'wrong@example.com', 'password': 'testpass123'},
                             headers={'Content-Type': 'application/json'})
        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data
        
        response = client.post('/api/login',
                             json={'email': 'test@example.com', 'password': 'wrongpass'},
                             headers={'Content-Type': 'application/json'})
        assert response.status_code == 401
        
        response = client.post('/api/login',
                             json={},
                             headers={'Content-Type': 'application/json'})
        assert response.status_code == 400

# =================== INTEGRATION TESTS ===================

class TestIntegrationScenarios:
    def test_full_user_registration_and_recipe_flow(self, client):
        """Full scenario: register -> login -> recipe creation -> getting recipe -> editing -> deleting"""
        # 1. Registration
        user_data = {
            'email': 'integration@example.com',
            'password': 'integration123'
        }
        
        response = client.post('/api/register',
                             json=user_data,
                             headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        user_info = response.get_json()
        assert 'id' in user_info
        
        # 2. Enter
        response = client.post('/api/login',
                             json=user_data,
                             headers={'Content-Type': 'application/json'})
        assert response.status_code == 200
        login_info = response.get_json()
        assert login_info['email'] == user_data['email']
        
        with client.session_transaction() as sess:
            assert 'user_id' in sess
            assert sess['user_id'] == user_info['id']
        
        # 3. Make recipe
        recipe_data = {
            'title': 'Integration Test Recipe',
            'description': 'Created during integration test',
            'ingredients': [
                {'name': 'Flour', 'amount': 250, 'unit': 'g'},
                {'name': 'Sugar', 'amount': 150, 'unit': 'g'}
            ],
            'tags': ['integration', 'test', 'baking'],
            'rate': 4
        }
        
        response = client.post('/api/recipes',
                             json=recipe_data,
                             headers={'Content-Type': 'application/json'})
        assert response.status_code == 201
        recipe_info = response.get_json()
        recipe_id = recipe_info['id']
        assert recipe_info['title'] == recipe_data['title']
        
        # 4. Get created recipe
        response = client.get(f'/api/recipes/{recipe_id}',
                            headers={'Content-Type': 'application/json'})
        assert response.status_code == 200
        retrieved_recipe = response.get_json()
        assert retrieved_recipe['id'] == recipe_id
        assert retrieved_recipe['title'] == recipe_data['title']
        assert retrieved_recipe['rate'] == recipe_data['rate']
        assert 'integration' in retrieved_recipe['tags']
        
        ingredients = retrieved_recipe['ingredients']
        assert len(ingredients) == 2
        assert ingredients[0]['name'] == 'Flour'
        assert ingredients[0]['amount'] == 250
        
        # 5. Edit recipe
        update_data = {
            'title': 'Updated Integration Recipe',
            'rate': 5,
            'description': 'Updated description'
        }
        
        response = client.put(f'/api/recipes/{recipe_id}',
                            json=update_data,
                            headers={'Content-Type': 'application/json'})
        assert response.status_code == 200
        
        response = client.get(f'/api/recipes/{recipe_id}',
                            headers={'Content-Type': 'application/json'})
        updated_recipe = response.get_json()
        assert updated_recipe['title'] == update_data['title']
        assert updated_recipe['rate'] == update_data['rate']
        assert updated_recipe['description'] == update_data['description']
        
        # 6. Delete recipe
        response = client.delete(f'/api/recipes/{recipe_id}',
                               headers={'Content-Type': 'application/json'})
        assert response.status_code == 200
        
        response = client.get(f'/api/recipes/{recipe_id}',
                            headers={'Content-Type': 'application/json'})
        assert response.status_code == 404
    
    def test_tag_filtering_and_aggregation(self, client, test_user):
        """Tags filtration"""
        with client.session_transaction() as sess:
            sess['user_id'] = test_user.id
            sess['username'] = test_user.username
        
        recipes_data = [
            {
                'title': 'Pasta Carbonara',
                'tags': ['italian', 'pasta', 'dinner'],
                'ingredients': []
            },
            {
                'title': 'Caesar Salad',
                'tags': ['salad', 'healthy', 'lunch'],
                'ingredients': []
            },
            {
                'title': 'Chocolate Cake',
                'tags': ['dessert', 'baking', 'chocolate'],
                'ingredients': []
            },
            {
                'title': 'Spaghetti Bolognese',
                'tags': ['italian', 'pasta', 'dinner'],
                'ingredients': []
            }
        ]
        
        created_ids = []
        for recipe_data in recipes_data:
            response = client.post('/api/recipes',
                                 json=recipe_data,
                                 headers={'Content-Type': 'application/json'})
            assert response.status_code == 201
            created_ids.append(response.get_json()['id'])
        
        # 1. Test tag 'italian
        response = client.get('/api/recipes?tags=italian',
                            headers={'Content-Type': 'application/json'})
        assert response.status_code == 200
        filtered = response.get_json()
        assert 'recipes' in filtered
        assert len(filtered['recipes']) == 2
        for recipe in filtered['recipes']:
            assert 'italian' in recipe['tags']
        
        # 2. Test teg 'pasta'
        response = client.get('/api/recipes?tags=pasta',
                            headers={'Content-Type': 'application/json'})
        filtered = response.get_json()
        assert len(filtered['recipes']) == 2
        
        # 3. Test two tags
        response = client.get('/api/recipes?tags=italian,pasta',
                            headers={'Content-Type': 'application/json'})
        filtered = response.get_json()
        assert len(filtered['recipes']) == 2
        
        # 4. Test tag endpoint
        response = client.get('/api/tags',
                            headers={'Content-Type': 'application/json'})
        assert response.status_code == 200
        tags_data = response.get_json()
        assert 'tags' in tags_data
        
        for tag_info in tags_data['tags']:
            if tag_info['name'] == 'italian':
                assert tag_info['count'] == 2
            elif tag_info['name'] == 'pasta':
                assert tag_info['count'] == 2
            elif tag_info['name'] == 'salad':
                assert tag_info['count'] == 1
    
    def test_meal_planning_and_shopping_list(self, client, test_user):
        """Planning meals and creating checklist"""
        with client.session_transaction() as sess:
            sess['user_id'] = test_user.id
        
        recipes = [
            {
                'title': 'Pancakes',
                'ingredients': [
                    {'name': 'Flour', 'amount': 200, 'unit': 'g'},
                    {'name': 'Milk', 'amount': 300, 'unit': 'ml'},
                    {'name': 'Eggs', 'amount': 2, 'unit': 'pieces'}
                ]
            },
            {
                'title': 'Omelette',
                'ingredients': [
                    {'name': 'Eggs', 'amount': 3, 'unit': 'pieces'},
                    {'name': 'Milk', 'amount': 50, 'unit': 'ml'},
                    {'name': 'Cheese', 'amount': 100, 'unit': 'g'}
                ]
            },
            {
                'title': 'Salad',
                'ingredients': [
                    {'name': 'Lettuce', 'amount': 1, 'unit': 'head'},
                    {'name': 'Tomato', 'amount': 2, 'unit': 'pieces'},
                    {'name': 'Cheese', 'amount': 50, 'unit': 'g'}
                ]
            }
        ]
        
        recipe_ids = []
        for recipe in recipes:
            full_recipe = {
                **recipe,
                'description': 'Test',
                'tags': ['test'],
                'rate': 5
            }
            
            response = client.post('/api/recipes',
                                 json=full_recipe,
                                 headers={'Content-Type': 'application/json'})
            assert response.status_code == 201
            recipe_ids.append(response.get_json()['id'])
        
        # One recipe
        response = client.get(f'/api/meals?recipe_ids={recipe_ids[0]}',
                            headers={'Content-Type': 'application/json'})
        assert response.status_code == 200
        meals_data = response.get_json()
        assert 'meals' in meals_data
        
        meals = meals_data['meals']
        assert {'name': 'Flour', 'amount': 200, 'unit': 'g'} in meals
        
        # Two recipes
        two_recipes = f'{recipe_ids[0]},{recipe_ids[1]}'
        response = client.get(f'/api/meals?recipe_ids={two_recipes}',
                            headers={'Content-Type': 'application/json'})
        assert response.status_code == 200
        meals_data = response.get_json()
        meals = meals_data['meals']
        
        assert {'name': 'Eggs', 'amount': 5, 'unit': 'pieces'} in meals  # 2 + 3 = 5
        
        # Three recipes
        all_recipes = ','.join(str(id) for id in recipe_ids)
        response = client.get(f'/api/meals?recipe_ids={all_recipes}',
                            headers={'Content-Type': 'application/json'})
        assert response.status_code == 200
        meals_data = response.get_json()
        meals = meals_data['meals']
        
        assert {'name': 'Cheese', 'amount': 150, 'unit': 'g'} in meals  # 100 + 50 = 150

# =================== TESTS START ===================

if __name__ == '__main__':
    import sys
    sys.exit(pytest.main([__file__, '-v']))