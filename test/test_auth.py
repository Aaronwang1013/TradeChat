import pytest
import sys
sys.path.append('../APP') 
from app import app
from flask_bcrypt import generate_password_hash
from pymongo import MongoClient
from config import Config

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    client = app.test_client()

    # Setup
    DATABASE_URL = f"mongodb+srv://{Config.MONGODB_USER}:{Config.MONGODB_PASSWORD}@cluster0.ibhiiti.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    mongo_client = MongoClient(DATABASE_URL)
    db = mongo_client['TradeChat']
    collection = db['User']
    collection.insert_one({
        "email": "correct_email@example.com",
        "username": "testuser",
        "password": generate_password_hash("correct_password").decode('utf-8')
    })

    yield client

    # Teardown
    collection.delete_one({"email": "correct_email@example.com"})
    mongo_client.close()

@pytest.fixture
def auth(client):
    class AuthActions(object):
        def login(self, email='correct_email@example.com', password='correct_password'):
            return client.post(
                '/user/signin',
                data={'email': email, 'password': password},
                follow_redirects=True
            )
        
        def logout(self):
            return client.get('/user/signout', follow_redirects=True)

    return AuthActions()

def test_login_success(client, auth):
    response = auth.login(email='correct_email@example.com', password='correct_password')
    assert response.status_code == 200

def test_login_failure(client, auth):
    response = auth.login(email='wrong_email@example.com', password='wrong_password')
    assert response.status_code == 200

def test_logout(client, auth):
    auth.login(email='correct_email@example.com', password='correct_password')
    response = auth.logout()
    assert response.status_code == 200
