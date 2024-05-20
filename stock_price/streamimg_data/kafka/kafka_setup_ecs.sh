# blocks until kafka is reachable
/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list
echo -e 'Creating kafka topics'
/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --if-not-exists --topic BTC --replication-factor 1 --partitions 1 --config retention.ms=86400000
/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --if-not-exists --topic TSLA --replication-factor 1 --partitions 1 --config retention.ms=86400000
/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --if-not-exists --topic NVDA --replication-factor 1 --partitions 1 --config retention.ms=86400000
/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --if-not-exists --topic AMZN --replication-factor 1 --partitions 1 --config retention.ms=86400000
/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --if-not-exists --topic MSFT --replication-factor 1 --partitions 1 --config retention.ms=86400000
/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --if-not-exists --topic AAPL --replication-factor 1 --partitions 1 --config retention.ms=86400000
/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --if-not-exists --topic GOOG --replication-factor 1 --partitions 1 --config retention.ms=86400000
/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --if-not-exists --topic META --replication-factor 1 --partitions 1 --config retention.ms=86400000
echo -e 'Successfully created the following topics:'
/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list