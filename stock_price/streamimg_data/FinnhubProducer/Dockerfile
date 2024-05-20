FROM python:3.8.19-bullseye

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8001

CMD ["python", "FinnhubProducer.py"]