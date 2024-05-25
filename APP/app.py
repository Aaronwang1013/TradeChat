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
import pytz
# make plot
from api_util import *
import time
# from functools import wraps
import jwt 
from datetime import datetime, timedelta
# process real time data
import time
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


app = Flask(__name__)
app.secret_key = Config.SECRET_KEY
csrf = CSRFProtect(app)


image_folder = os.path.join(app.static_folder, 'images/company')
icons = [f for f in os.listdir(image_folder) if os.path.isfile(os.path.join(image_folder, f))]

timestamp = []
prices = []

## init mongo client
DATABASE_URL = f"mongodb+srv://{Config.MONGODB_USER}:{Config.MONGODB_PASSWORD}@cluster0.ibhiiti.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(DATABASE_URL)


def get_username(access_token):
    access_token = access_token.split(' ')[1]
    decoded_token = jwt.decode(
        access_token, 
        Config.SECRET_KEY, 
        algorithms=Config.JWT_ALGORITHM
    )
    username = decoded_token['sub']
    email = decoded_token['email']
    return username, email

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
    logger.info(f'Generated access token for {username}')
    return access_token
    

@app.route('/')
def index(): 
    return render_template('index.html', icons = icons)


@app.route('/home')
@token_required
def home():
    access_token = request.cookies.get('access_token')
    if access_token:
        username, email = get_username(access_token)
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
            collection = client['TradeChat']['User']
            if email:
                # find user in the database
                user_data = collection.find_one({"email": email}, {"_id": 0, "username": 1, "password": 1})
                if user_data:
                    if check_password_hash(user_data.get('password'), password):
                        flash('Login Successful. You will now be redirected to the homepage.', 'success')
                        username = user_data.get('username')
                        access_token = generate_access_token(username, email)
                        response = make_response(redirect(url_for('home')))
                        response.set_cookie('access_token',  f'Bearer {access_token}')
                        return response
                else:
                    flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('signin.html', form=loginform)


@app.route('/user/signout', methods = ['GET', 'POST'])
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
        username, email = get_username(access_token)
        return render_template('profile.html', username=username, email=email, icons = icons)
    else:
        flash("You need to sign in to access your profile", "warning")
        return redirect(url_for('signup'))


@app.route('/twitter_sentiment', methods=['GET', 'POST'])
def twitter_sentiment():
    if request.method == 'POST':
        data = request.json
        company_name = data.get('company')
        if company_name == "NVDA":
            return jsonify({"error": "Sentiment analysis for NVDA is not available."}), 400
        tweet_df, stock_df = read_twitter_data(company_name)
        start_day = min(tweet_df['day_date'])
        end_day = max(tweet_df['day_date'])
        fig_json = draw_stock_price_with_sentiment(tweet_df, stock_df, start_day, end_day, company_name)
        logger.info(f"Sentiment analysis for {company_name} completed")
        return fig_json
    else:
        logger.error("Company name not found in request JSON")
        return jsonify({"error": "Company name not found in request JSON"}), 400


@app.route('/discussion')
@token_required
def discussion():
    access_token = request.cookies.get('access_token')
    if access_token:
        username, email = get_username(access_token)
    page = request.args.get('page', 1, type=int)
    per_page = 30
    collection = client['TradeChat']['comment']
    comments = collection.find().sort('_id', -1).skip((page-1)*per_page).limit(per_page)
    total_comments = collection.count_documents({})
    total_pages = total_comments // per_page + (1 if total_comments % per_page > 0 else 0)
    logger.info(f"Displaying discussion page {page} with {total_comments} comments.")
    return render_template('discussion.html', comments=comments, page=page, total_comments=total_comments, 
                           total_pages=total_pages, icons = icons, username = username)


@app.route('/post_comment', methods=['POST'])
@token_required
def post_comment():
    collection = client['TradeChat']['comment']
    access_token = request.cookies.get('access_token')
    if access_token:
        timestamp = datetime.utcnow()
        username, email = get_username(access_token)
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
            logger.info(f"Comment posted by {username} for {company}")
            flash('Comment posted successfully!', 'success')
            return redirect(url_for('discussion'))
        else:
            logger.error(f"Failed to post comment by {username}")
            return jsonify({"error": "Failed to post comment"}), 500
    else:
        logger.error("User not signed in to post comment")
        flash('Please sign in to post a comment.', 'info')
        return redirect(url_for('signin'))


@app.route('/stock')
@token_required
def stock():
    access_token = request.cookies.get('access_token')
    if access_token:
        username, email = get_username(access_token)
    return render_template('stock.html', icons = icons, username = username)


@app.route('/stock_price')
def stock_price():
    prices = get_realtime_data()
    return jsonify(prices)



@app.route('/sentiment')
def sentiment():
    company_list = ['Overall', 'AAPL', 'AMZN', 'GOOGL', 'MSFT', 'NVDA', 'TSLA', 'META']
    company = request.args.get("company")
    if company == 'Overall':
        data = get_reddit_sentiment()
    elif company in company_list:
        data = get_sentiment_by_company(company)
    else:
        data = {"error": "Invalid company"}

    return data


@app.route('/fear_greed_gauge')
def fear_greed_gauge():
    current_index = get_fear_greed_index()
    if current_index:
        logger.info(f"Fear and Greed Index: {current_index}")
        graphJSON = create_fear_greed_gauge(round(current_index))
    return graphJSON

@app.route('/fear_greed_updated_time')
def fear_greed_updated_time():
    time.sleep(1)
    last_update_time = get_fear_greed_updated_time()
    taiwan_timezone = pytz.timezone('Asia/Taipei')
    taiwan_time = last_update_time.astimezone(taiwan_timezone)
    formatted_time = taiwan_time.strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f"Fear and Greed Index last updated at {formatted_time}")
    return jsonify(lastUpdateTime=formatted_time)


@app.route('/api/backtest', methods=['POST'])
def backtest():
    company = request.form['companyList']
    amount = request.form.get('amount')
    start_date = request.form.get('startDate')
    end_date = request.form.get('endDate')
    strategy = request.form.get('strategy')
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')
    documents = backtest_price(start_date, end_date, company)
    df = pd.DataFrame(documents)
    fig_json = backtest_figure(df, amount, company, strategy)
    return fig_json

@app.route('/api/comment_stats')
def comment_stats():
    data = get_comment_company_count()
    logger.info(f"Comment stats: {data}")
    return data

if __name__ == "__main__":
    app.run(debug=True)