# TradeChat

TradeChat provides a platform for users to discuss companies of interest and receive real-time feedback on market sentiment analysis for these companies. Additionally, it offers basic backtesting and forecasting tools to users, creating a comprehensive stock trading community platform.

Website: [TradeChat](https://tradechat.online/)

## Table of contents
- [TradeChat](#tradechat)
  - [Table of contents](#table-of-contents)
  - [Feature](#feature)
  - [Overall Architecture](#overall-architecture)
  - [Technical Detail](#technical-detail)
  - [Technical Detail](#technical-detail-1)
    - [Real-time market price](#real-time-market-price)
  - [Demo](#demo)
  - [Deployment](#deployment)
  - [Technologies Used](#technologies-used)

## Feature
- Real-time market price of seven big tech companies from FinnhubAPI.
- Historical Twitter sentiment analysis of the seven big tech companies.
- Market sentiment analysis with Reddit posts and comments using PRAW.
- Backtesting system.
- Join a community of traders to discuss companies of interest.

## Overall Architecture
![alt text](./docs/system_architecture.png)

- Webserver: 
  - HTML, CSS and Javascript are used to create the front-end of the application.
  - Plotly is used to create interactive plots for the Fear & Greed Index and sentiment  analysis.
  - A Flask-based webserver is used to serve the front-end and handle API requests.
  - Kafka is used to stream real-time market data from FinnhubAPI, pyspark is used to process the data and store in MongoDB.
  - Reddit posts and comments are fetched using PRAW, and sentiment analysis is done using vaderSentiment(https://pypi.org/project/vaderSentiment/). Airflow is used to schedule the sentiment analysis job.
  - Yahoo Finance API is used to fetch historical stock data for backtesting.


## Technical Detail

Containerization: Docker is used to containerize all the application. This allows for easy deployment and scaling of the application.

Deployment: The application is deployed using either EC2 or Fargate. The instances are managed by ECS, which handles scaling, load balancing, and monitoring of the application.

Database: MongoDB is used to store the processed market data and sentiment analysis. This allows for easy retrieval of data and analysis.




## Technical Detail
 ### Real-time market price
 ![alt text](./docs/stock_data_pipeline.png)
## Demo


## Deployment

## Technologies Used

```

```