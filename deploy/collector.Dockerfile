FROM otel/opentelemetry-collector-contrib@sha256:8164eab2e6bca9c9b0837a8d2f118a6618489008a839db7f9d6510e66be3923c
COPY config/otel/qualification.yml /etc/otelcol-contrib/config.yaml
USER 10001:10001
