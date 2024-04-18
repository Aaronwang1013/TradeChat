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
# make plot
import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go


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


def read_twitter_data():
    DATABASE_URL = f"mongodb+srv://{Config.MONGODB_USER}:{Config.MONGODB_PASSWORD}@cluster0.ibhiiti.mongodb.net/?retryWrites=true&w=secure&appName=Cluster0"
    client = MongoClient(DATABASE_URL)
    tweet_collection = client['TradeChat']['Twitter_tweets']
    stock_collection = client['TradeChat']['Twitter_stock']
    # Retrieve all the collections
    tweet_data = list(tweet_collection.find({}))
    stock_data = list(stock_collection.find({}))
    tweet_df = pd.DataFrame(tweet_data)
    stock_df = pd.DataFrame(stock_data)
    client.close()
    return tweet_df, stock_df


def sentiment_overtime(tweet_df, stock_df, title, score_column_name="score", save_path=None):
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_trace(
        go.Scatter(x=tweet_df['day_date'], y=tweet_df[score_column_name], mode='lines', name=score_column_name),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(x=stock_df['day_date'], y=stock_df['close_value'], mode='lines', name='Stock Price'),
        secondary_y=True,
    )

    fig.update_layout(
        title=f"Effects of {title} tweets to stock price",
        xaxis_title="Day date",
        yaxis_title=score_column_name,
        yaxis2_title="Stock Price",
    )

    return fig


def draw_stock_price_with_sentiment(tweet_df, stock_df, start_day, end_day, score_name="score"):
    ticker_symbols =  tweet_df["ticker_symbol"].unique()
    company = pd.read_csv('./dataset/Company.csv')
    for ticker_symbol in ticker_symbols:
        print(f"Ticker symbol: {ticker_symbol}")

        sub_company = company[company["ticker_symbol"] == ticker_symbol]["company_name"]
        if len(sub_company) != 1:
            continue

        company_name = sub_company.iloc[0]

        print(f"Stock price of {company_name} company with ticker symbol is {ticker_symbol}")

        sub_tweet_df = tweet_df[tweet_df["ticker_symbol"] == ticker_symbol]
        sub_tweet_df = sub_tweet_df[(sub_tweet_df["day_date"]>=pd.to_datetime(start_day)) & (sub_tweet_df["day_date"]<=pd.to_datetime(end_day))]

        sub_stock_df = stock_df[stock_df["ticker_symbol"] == ticker_symbol]
        sub_stock_df = sub_stock_df[(sub_stock_df["day_date"]>=pd.to_datetime(start_day)) & (sub_stock_df["day_date"]<=pd.to_datetime(end_day))]
        save_path = f"./images/{ticker_symbol}_sentiment_overtime.png"
        fig = sentiment_overtime(sub_tweet_df, sub_stock_df, company_name, score_column_name=score_name, save_path = save_path)




@app.route('/twitter_sentiment', mehotds=['GET', 'POST'])
def twitter_sentiment():
    tweet_df, stock_df = read_twitter_data()
    start_day = min(tweet_df['day_date'])
    end_day = max(tweet_df['day_date'])
    fig = draw_stock_price_with_sentiment(tweet_df, stock_df, start_day, end_day)
    return render_template('twitter_sentiment_form.html', fig=fig)
    
            

@app.route('/stock')
def about():
    return render_template('stock.html')

@app.route('/chat')
def chat():
    return render_template('chat.html')



if __name__ == "__main__":
    app.run(debug=True)