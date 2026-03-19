import os
import requests
from flask import Flask, render_template
import socket
import redis

app = Flask(__name__)
# Подключаемся к Redis (имя хоста будет таким же, как имя Service в K8s)
redis_host = os.getenv('REDIS_HOST', 'redis-service')
cache = redis.Redis(host=redis_host, port=6379, decode_responses=True)

@app.route('/')
def get_crypto():
    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ARBUSDT']
    results = {}
    hostname = socket.gethostname() # Чтобы видеть, какой под ответил

    try:
        for symbol in symbols:
            cached_price = cache.get(symbol)
            if cached_price:
                results[symbol] = {"price": cached_price, "source": "cache"}
            else:
                response = requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}')
                data = response.json()
                price = "{:,.2f}".format(float(data['price']))
                cache.set(symbol, price, ex=60)
                results[symbol] = {"price": price, "source": "api"}
        
        # Отправляем данные в HTML-шаблон
        return render_template('index.html', data=results, host=hostname)
    
    except Exception as e:
        return f"Ошибка: {str(e)}", 500
#if __name__ == '__main__':
#    app.run(host='0.0.0.0', port=5000)
