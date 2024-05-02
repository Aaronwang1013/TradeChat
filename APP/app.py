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
import random
import time
# from functools import wraps
import jwt 
from datetime import datetime, timedelta
# process real time data
from flask_socketio import SocketIO, emit
import time


app = Flask(__name__)
app.secret_key = Config.SECRET_KEY
csrf = CSRFProtect(app)
socketio = SocketIO(app)


icons = ['TSLA.png', 'aapl.png', 'amzn.png', 'goog.png', 'meta.png', 'msft.png', 'nvda.png']
timestamp = []
prices = []


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
        access_token = access_token.split(' ')[1]
        decoded_token = jwt.decode(access_token, 
                                Config.SECRET_KEY,
                                algorithms=Config.JWT_ALGORITHM)
        username = decoded_token['sub']
        email = decoded_token['email']
        return render_template('profile.html', username=username, email=email, icons = icons)
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
    page = request.args.get('page', 1, type=int)
    per_page = 30
    DATABASE_URL = f"mongodb+srv://{Config.MONGODB_USER}:{Config.MONGODB_PASSWORD}@cluster0.ibhiiti.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    client = MongoClient(DATABASE_URL)
    collection = client['TradeChat']['comment']
    comments = collection.find().sort('_id', -1).skip((page-1)*per_page).limit(per_page)
    total_comments = collection.count_documents({})
    total_pages = total_comments // per_page + (1 if total_comments % per_page > 0 else 0)
    return render_template('discussion.html', comments=comments, page=page, total_comments=total_comments, total_pages=total_pages, icons = icons)


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
def stock():
    prices = get_realtime_data()
    return render_template('stock.html', icons = icons, prices=prices)

def background_thread():
    """ 後台線程，定期發送股價更新 """
    while True:
        # 模擬股價更新
        stock_prices = get_realtime_data()  
        socketio.emit('update_prices', {'data': stock_prices}, namespace='/stock')
        time.sleep(1)  

@socketio.on('connect', namespace='/stock')
def test_connect():
    global thread
    if not thread.is_alive():
        thread = socketio.start_background_task(background_thread)




@app.route('/sentiment')
def sentiment():
    company = request.args.get("company")
    if company == 'Overall':  
        data = get_reddit_sentiment()
    elif company == 'AAPL':
        data = get_sentiment_by_company(company)
    elif company == 'AMZN':
        data = get_sentiment_by_company(company)
    elif company == 'GOOGL':
        data = get_sentiment_by_company(company)
    elif company == 'MSFT':
        data = get_sentiment_by_company(company)
    elif company == 'NVDA':
        data = get_sentiment_by_company(company)
    elif company == 'TSLA':
        data = get_sentiment_by_company(company)
    elif company == 'META':
        data = get_sentiment_by_company(company)
    return data



@app.route('/fear_greed_gauge')
def fear_greed_gauge():
    current_index = get_fear_greed_index()
    graphJSON = create_fear_greed_gauge(round(current_index))
    return graphJSON

@app.route('/fear_greed_updated_time')
def fear_greed_updated_time():
    time.sleep(3)
    last_update_time = get_fear_greed_updated_time()
    taiwan_timezone = pytz.timezone('Asia/Taipei')
    taiwan_time = last_update_time.astimezone(taiwan_timezone)
    formatted_time = taiwan_time.strftime('%Y-%m-%d %H:%M:%S')
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
    df['date'] = pd.to_datetime(df['date'])
    df.set_index(df['date'], inplace=True)
    # calculate benefits
    df['bnh_returns'] = np.log(df['close']/df['close'].shift(1))
    initial_price = df['close'].iloc[0]
    shares_bought = int(amount) / initial_price
    df['protfolio_value'] = shares_bought * df['close']
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x = df['date'],
                y = df['protfolio_value'],
                mode = 'lines',
                name = f'By and hold strategy in {company}')
    )
    fig.add_annotation(
        x=df.index[-1], y=df['protfolio_value'].iloc[-1],
        text=f"Final Value: ${df['protfolio_value'].iloc[-1]:,.2f}",
        showarrow=True,
        arrowhead=1,
        ax=-50,
        ay=-100
    )
    ## MA strategy
    if strategy == 'sma':
        df['SMA50'] =df['close'].rolling(window=50).mean()
        df['SMA200'] = df['close'].rolling(window=200).mean()
        ## trading signal
        df['signal'] = 0
        df['signal'][50:] = df['SMA50'][50:] > df['SMA200'][50:]
        # if SMA50 > SMA200, then buy, else sell
        # df['position'] = np.where(df['SMA50'] > df['SMA200'], 1, 0)
        df['position'] = np.where(df['SMA50'] > df['SMA200'], 1, 
                          np.where(df['SMA50'] < df['SMA200'], -1, 0))
        # move the signal today to tomorrow
        df['position'] = df['position'].shift(1)
        df.dropna(inplace=True) 
        # calculate strategy returns
        df['strategy_returns'] = df['bnh_returns'] * df['position']
        df['portfolio_value_sma'] = (np.exp(df['strategy_returns'].cumsum())) * int(amount)
        # make ma plot
        fig.add_trace(
        go.Scatter(x=df['date'], 
                    y=df['portfolio_value_sma'], 
                    mode='lines', 
                    name=f'SMA Strategy in {company}')
        )
        fig.update_layout(
        title = "Comparsion between Strategies",
        xaxis_title = "Date",
        yaxis_title = "Portfolio Value",
        template='plotly_dark',
        showlegend=True
        )
        fig.add_annotation(
            x=df.index[-1], y=df['portfolio_value_sma'].iloc[-1],
            text=f"Final Value: ${df['portfolio_value_sma'].iloc[-1]:,.2f}",
            showarrow=True,
            arrowhead=1,
            ax=-50,
            ay=-100
        )
        fig_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    ## mean reversion
    if strategy == 'mean_reversion':
        window = 25
        df['mean_price'] = df['close'].rolling(window=window).mean()
        df['std_dev'] = df['close'].rolling(window=window).std()
        # set the upper and lower bands
        df['lower_band'] = df['mean_price'] - 2 * df['std_dev']
        df['upper_band'] = df['mean_price'] + 2 * df['std_dev']
        df['position'] = np.where(df['close'] < df['lower_band'], 1, np.where(df['close'] > df['upper_band'], -1, 0))
        df['position'] = df['position'].shift(1)
        df['mr_returns'] = df['bnh_returns'] * df['position']
        df['portfolio_value_mr'] = (np.exp(df['mr_returns'].cumsum())) * int(amount)
        fig.add_trace(
        go.Scatter(x=df['date'], 
                    y=df['portfolio_value_mr'], 
                    mode='lines', 
                    name=f'MR Strategy in {company}')
        )
        fig.update_layout(
        title = "Comparsion between Strategies",
        xaxis_title = "Date",
        yaxis_title = "Portfolio Value",
        template='plotly_dark',
        showlegend=True
        )
        fig.add_annotation(
            x=df.index[-1], y=df['portfolio_value_mr'].iloc[-1],
            text=f"Final Value: ${df['portfolio_value_mr'].iloc[-1]:,.2f}",
            showarrow=True,
            arrowhead=1,
            ax=-50,
            ay=-100
        )
        fig_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    
    fig_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return fig_json

@app.route('/api/comment_stats')
def comment_stats():
    data = get_comment_company_count()
    return data

if __name__ == "__main__":
    thread = socketio.start_background_task(background_thread)
    socketio.run(app, debug=True)