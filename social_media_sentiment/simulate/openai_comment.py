import requests

from bs4 import BeautifulSoup 
from config import Config
from openai import OpenAI
import time
import random


client = OpenAI(api_key=Config.OPENAI_API_KEY)

def get_csrf_token(session, url):
    response = session.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    csrf_token = soup.find('input', {'name': 'csrf_token'}).get('value')
    return csrf_token

def generate_comment(company):
    response = client.chat.completions.create(
    model="gpt-3.5-turbo-0125",
    messages=[
        {"role": "system", "content": "You are a netizen who has many knowledge about US stock market."},
        {"role": "user", "content": f"Write a comment about {company} stock price"}
    ]
    )
    return response.choices[0].message.content


def login_and_get_token(session, email, password, csrf_token):
    login_url = 'http://54.254.126.184/user/signin'
    response = session.post(login_url, data={"email": email, 
                                              "password": password, 
                                              "csrf_token": csrf_token})
    time.sleep(2)
    if response.status_code == 200:
        print(f"Login successful for {email}")
        return session.cookies.get('access_token')
    else:
        print(f"Login failed for {email} with password {password}")
        return None


def post_comment(session, token, comment, company, csrf_token):
    post_url = "http://54.254.126.184/post_comment"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = session.post(post_url, headers=headers, data={"comment": comment, 
                                                              "company": company,
                                                              "csrf_token": csrf_token})
    if response.status_code == 200:
        print(f"Comment posted for {company}")
    else:
        print(f"Failed to post comment, {response.text}")

def simulate(user_emails, companies, company_weights):
    session = requests.Session()
    csrf_url = 'http://54.254.126.184/user/signin'
    csrf_token = get_csrf_token(session, csrf_url)
    try:
        while True:
            user = random.choice(user_emails)
            token = login_and_get_token(session, user['email'], user['password'], csrf_token)
            if token:
                company = random.choices(companies, weights=company_weights, k = 8)[0]
                comment = generate_comment(company)
                post_comment(session, token, comment, company, csrf_token)
                # time.sleep(1)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':

    company_list = ["Overall Economy", "NVDA", "GOOG", "AMZN",
                    "TSLA", "MSFT", "META", "AAPL"]
    company_weights = [1, 10, 3, 4, 9, 5, 2, 2]
    user_list = [
        {'email': 'johnbaldwin@example.com', 'password':'_+8Wa(IcEf'},
        {'email': 'vargasjasmin@example.net', 'password':'GI$K3Ht+Hx'},
        {'email': 'gomezmichael@example.org', 'password':'YP8ODuNCD&'},
        {'email': 'bshepherd@example.com', 'password':'DRR5MZxY$Q'},
        {'email': 'curtishill@example.com', 'password': ')6aN@I!lmh'},
        {'email': 'jason18@example.com', 'password':'^i92X#3t!D'},
        {'email': 'alexandria05@example.com', 'password':'MSd7F)pt)k'},
        {'email': 'tbarnett@example.com', 'password':'*4GwzsH0w1'},
        {'email': 'vyoung@example.org', 'password': 'p+r6Lz3eur'}
    ]

    simulate(user_list, company_list, company_weights)
