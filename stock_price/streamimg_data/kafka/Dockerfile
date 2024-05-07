FROM debezium/kafka:latest


WORKDIR /app

# copy the current directory contents into the container at /app
COPY . /app


CMD ["sh", "kafka_setup_ecs.sh"]