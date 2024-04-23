from flask import Flask, render_template, request
from flask import flash
from flask import jsonify
from flask import make_response
from flask import redirect
from flask import url_for
from flask_wtf import CSRFProtect
from config import Config
from flask_bcrypt import check_password_hash
from flask_bcrypt import generate_password_hash 
import forms
from functools import wraps
from pymongo import MongoClient
# make plot
from api_util import *
# from functools import wraps
import jwt 
from datetime import datetime, timedelta


app = Flask(__name__)
app.secret_key = Config.SECRET_KEY
csrf = CSRFProtect(app)

icons = ['TSLA.png', 'AAPL.png', 'AMZN.png', 'GOOG.png', 'META.png', 'MSFT.png', 'NVDA.png']

def token_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except jwt.ExpiredSignatureError:
            flash('Access token expired. Please sign in again.', 'warning')
            return redirect(url_for('signup'))
        except jwt.InvalidTokenError:
            flash('Invalid token. Please sign in again.', 'warnging')
            return redirect(url_for('signup'))
    return decorated_function


def generate_access_token(username, email):
    payload = {
        'exp': datetime.utcnow() + timedelta(seconds=3600),
        'sub': username,
        'email': email
    }
    access_token = jwt.encode(
                payload,
                Config.SECRET_KEY,
                algorithm=Config.JWT_ALGORITHM
            )
    return access_token
    

@app.route('/')
def index(): 
    return render_template('index.html', icons = icons)


@app.route('/home')
@token_required
def home():
    access_token = request.cookies.get('access_token')
    if access_token:
        access_token = access_token.split(' ')[1]
        decoded_token = jwt.decode(access_token, 
                                Config.SECRET_KEY,
                                algorithms=Config.JWT_ALGORITHM)
        username = decoded_token['sub']
    else:
        username = None
    return render_template('index.html', icons = icons, username=username)



@app.route('/user/signup', methods=['GET', 'POST'])
@token_required
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
            ## jwt access token
            access_token = generate_access_token(username, email)
            response = make_response(render_template('signup_success.html'))
            response.set_cookie('access_token', f'Bearer {access_token}')
            return response
        elif signupform.validate_on_submit() == False:
            return jsonify({'error': 'Invalid form data'}, 403)
        else:
            return jsonify({'error': 'Invalid request method'}, 403)
    return render_template('signup.html', form=signupform)


@app.route('/user/signin', methods=['GET', 'POST'])
@token_required
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
            if email:
                # find user in the database
                user_data = collection.find_one({"email": email}, {"_id": 0, "username": 1, "password": 1})
                if check_password_hash(user_data.get('password'), password):
                    print("userdata:", user_data)
                    flash('Login Successful. You will now be redirected to the homepage.', 'success')
                    username = user_data.get('username')
                    access_token = generate_access_token(username, email)
                    response = make_response(redirect(url_for('home')))
                    response.set_cookie('access_token',  f'Bearer {access_token}')
                    return response
            else:
                flash('Login Unsuccessful. Please check username and password', 'danger')

        return jsonify({'error': 'Invalid form data'}, 403)
    return render_template('signin.html', form=loginform)


@app.route('/user/signout')
def signout():
    response = make_response(redirect(url_for('index')))
    response.delete_cookie('access_token')
    flash('Successfully signout', 'info')
    return response


@app.route('/user/profile')
@token_required
def profile():
    access_token = request.cookies.get('access_token')
    if access_token:
        access_token = access_token.split(' ')[1]
        decoded_token = jwt.decode(access_token, 
                                Config.SECRET_KEY,
                                algorithms=Config.JWT_ALGORITHM)
        username = decoded_token['sub']
        email = decoded_token['email']
        return render_template('profile.html', username=username, email=email)
    else:
        flash("You need to sign in to access your profile", "warning")
        return redirect(url_for('signup'))


@app.route('/twitter_sentiment', methods=['GET', 'POST'])
def twitter_sentiment():
    if request.method == 'POST':
        data = request.json
        company_name = data.get('company')
        tweet_df, stock_df = read_twitter_data(company_name)
        start_day = min(tweet_df['day_date'])
        end_day = max(tweet_df['day_date'])
        fig_json = draw_stock_price_with_sentiment(tweet_df, stock_df, start_day, end_day, company_name)
        return fig_json
    else:
        return jsonify({"error": "Company name not found in request JSON"}), 400


@app.route('/discussion')
def discussion():
    DATABASE_URL = f"mongodb+srv://{Config.MONGODB_USER}:{Config.MONGODB_PASSWORD}@cluster0.ibhiiti.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    client = MongoClient(DATABASE_URL)
    collection = client['TradeChat']['comment']
    comments = collection.find({})
    return render_template('discussion.html', comments=comments)


@app.route('/post_comment', methods=['POST'])
@token_required
def post_comment():
    DATABASE_URL = f"mongodb+srv://{Config.MONGODB_USER}:{Config.MONGODB_PASSWORD}@cluster0.ibhiiti.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    client = MongoClient(DATABASE_URL)
    collection = client['TradeChat']['comment']
    access_token = request.cookies.get('access_token')
    if access_token:
        timestamp = datetime.utcnow()
        access_token = access_token.split(' ')[1]
        decoded_token = jwt.decode(access_token, 
                                Config.SECRET_KEY,
                                algorithms=Config.JWT_ALGORITHM)
        username = decoded_token['sub']
        comment = request.form['comment']
        company = request.form['company']
        comment_data = {
            "username": username,
            "comment": comment,
            "company": company,
            "timestamp": timestamp
        }
        result = collection.insert_one(comment_data)
        if result.inserted_id:
            flash('Comment posted successfully!', 'success')
            return redirect(url_for('discussion'))
        else:
            return jsonify({"error": "Failed to post comment"}), 500
    else:
        flash('Please sign in to post a comment.', 'info')
        return redirect(url_for('signin'))


@app.route('/stock')
def about():
    return render_template('stock.html')

@app.route('/chat')
def chat():
    return render_template('chat.html')



if __name__ == "__main__":
    app.run(debug=True)