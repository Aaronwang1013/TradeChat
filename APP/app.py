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
    icons = ['TSLA.png', 'AAPL.png', 'AMZN.png', 'GOOG.png', 'META.png', 'MSFT.png', 'NVDA.png']
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


@app.route('/user/signin', methods=['GET', 'POST'])
def signin():
    loginform = forms.SigninForm()
    if request.method == 'POST':
        if loginform.validate_on_submit():
            email = loginform.email.data
            password = loginform.password.data

            # create a MongoClient to the running mongod instance
            DATABASE_URL = f"mongodb+srv://{Config.MONGODB_USER}:{Config.MONGODB_PASSWORD}@cluster0.ibhiiti.mongodb.net/?retryWrites=true&w=secure&appName=Cluster0"
            client = MongoClient(DATABASE_URL)
            collection = client['TradeChat']['User']

            # find user in the database
            email = collection.find_one({"email": email})
            print(email)
            if email and check_password_hash(email['password'], password):
                flash('Login Successful. You will now be redirected to the homepage.', 'success')
                return render_template('signin_success.html')
            else:
                flash('Login Unsuccessful. Please check username and password', 'danger')

        return jsonify({'error': 'Invalid form data'}, 403)
    return render_template('signin.html', form=loginform)

    
            

@app.route('/stock')
def about():
    return render_template('stock.html')

@app.route('/chat')
def chat():
    return render_template('chat.html')



if __name__ == "__main__":
    app.run(debug=True)