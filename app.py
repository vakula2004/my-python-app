from flask import Flask, jsonify
import os
import socket
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
# Инициализируем метрики
metrics = PrometheusMetrics(app)

# Статическая информация для мониторинга (версия, хост)
metrics.info('app_info', 'Application info', version='1.0.3', host=socket.gethostname())

@app.route('/')
def hello():
    return f"Privet! I am running on pod: {socket.gethostname()}"

@app.route('/health')
def health():
    return jsonify(status="UP")

if __name__ == "__main__":
    # host='0.0.0.0' — это критически важно!
    app.run(host='0.0.0.0', port=5000)
