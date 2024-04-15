from flask import Flask, render_template, request
from flask import flash
from flask import jsonify
from flask import redirect
from flask import url_for
from flask_wtf import CSRFProtect
from config import Config
from flask_bcrypt import check_password_hash
from flask_bcrypt import generate_password_hash 
import forms
from pymongo import MongoClient


app = Flask(__name__)
app.secret_key = Config.SECRET_KEY
csrf = CSRFProtect(app)




@app.route('/')
def index():
    icons = ['TSLA.png', 'aapl.png', 'amzn.png', 'goog.png', 'meta.png', 'msft.png', 'nvda.png']
    return render_template('index.html', icons = icons)


@app.route('/user/signup', methods=['GET', 'POST'])
def signup():
    signupform = forms.SignupForm()
    if request.method == 'POST':
        username = signupform.name.data
        email = signupform.email.data
        password = signupform.password.data
        hashed_password = generate_password_hash(password)
        if signupform.validate_on_submit() == True:
            flash(f'Account created for {username}!', 'success')
            # create a MongoClient to the running mongod instance
            DATABASE_URL = f"mongodb+srv://{Config.MONGODB_USER}:{Config.MONGODB_PASSWORD}@cluster0.ibhiiti.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
            client = MongoClient(DATABASE_URL)
            # initialize collection
            collection = client['TradeChat']['User']
            # create a new user
            new_user = {
                "username": username,
                "email": email,
                "password": hashed_password
            }

            # insert the new user into the 'users' collection
            collection.insert_one(new_user)
            flash('Signup successful. You will now be redirected to the homepage.', 'success')
            return render_template('signup_success.html')
        elif signupform.validate_on_submit() == False:
            return jsonify({'error': 'Invalid form data'}, 403)
        else:
            return jsonify({'error': 'Invalid request method'}, 403)
    return render_template('signup.html', form=signupform)

@app.route('/stock')
def about():
    return render_template('stock.html')

@app.route('/chat')
def chat():
    return render_template('chat.html')



if __name__ == "__main__":
    app.run(debug=True)