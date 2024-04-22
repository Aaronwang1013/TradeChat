FROM grafana/grafana:latest

COPY ./grafana.ini /etc/grafana/grafana.ini


RUN /bin/bash -c 'grafana-cli plugins install grafana-mongodb-datasource'