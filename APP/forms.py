from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Email, ValidationError
from pymongo import MongoClient
from config import Config



def email_exists(form, field):
    # create a MongoClient to the running mongod instance
    DATABASE_URL = f"mongodb+srv://{Config.MONGODB_USER}:{Config.MONGODB_PASSWORD}@cluster0.ibhiiti.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    client = MongoClient(DATABASE_URL)
    # initialize collection
    collection = client['TradeChat']['User']
    # get the database
    if collection.find_one({'email': field.data}):
        raise ValidationError("Email already exists.")


class SignupForm(FlaskForm):
    name = StringField(
        'Name',
        validators=[
            DataRequired()
        ]
    )
    email = StringField(
        'Email',
        validators=[
            DataRequired(),
            Email(), 
            email_exists
        ]
    )
    password = PasswordField(
        'Password',
        validators=[
            DataRequired()
        ]
    )


class SigninForm(FlaskForm):
    name = StringField(
        'Name',
        validators=[
            DataRequired()
        ]
    )
    email = StringField(
        'Email',
        validators=[
            DataRequired(),
            Email()
        ]
    )
    password = PasswordField(
        'Password',
        validators=[
            DataRequired()
        ]
    )