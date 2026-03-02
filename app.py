from flask import Flask, jsonify
import socket
import datetime
import os

app = Flask(__name__)

# Переменная для имитации состояния "здоровья"
app_ready = True

@app.route('/')
def hello():
    # Собираем данные о среде
    info = {
        "message": "Privet! App is running in K8s!",
        "pod_name": socket.gethostname(),
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "version": "2.0.0",
        "env": os.getenv("APP_ENV", "production")
    }
    
    # Красивый HTML вывод
    return f"""
    <html>
        <body style="font-family: Arial; text-align: center; background-color: #f0f2f5;">
            <h1 style="color: #1a73e8;">{info['message']}</h1>
            <p><b>Pod Name:</b> <span style="color: #d93025;">{info['pod_name']}</span></p>
            <p><b>Server Time:</b> {info['time']}</p>
            <hr width="300px">
            <small>Version: {info['version']} | Environment: {info['env']}</small>
        </body>
    </html>
    """

@app.route('/health')
def health():
    if app_ready:
        return jsonify(status="UP"), 200
    else:
        return jsonify(status="DOWN"), 503

if __name__ == '__main__':
    # Включаем debug режим для удобства (в продакшене лучше выключать)
    app.run(host='0.0.0.0', port=5000, debug=True)
