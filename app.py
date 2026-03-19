import os
import requests
import redis
import psycopg2
import socket
from flask import Flask, render_template

app = Flask(__name__)

def save_to_db(symbol, price):
    print(f"--> Попытка записи в БД: {symbol} = {price}") # Увидим в логах
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'postgres-service'),
            database='cryptodb',
            user='postgres',
            password='supersecret'
        )
        cur = conn.cursor()
        cur.execute("INSERT INTO history (symbol, price) VALUES (%s, %s)", (symbol, str(price)))
        conn.commit()
        cur.close()
        conn.close()
        print(f"OK: Записано в БД")
    except Exception as e:
        print(f"!!! ОШИБКА БД: {e}")

@app.route('/')
def get_crypto():
    print("--- Новый запрос на главную страницу ---")
    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
    results = {}
    
    # Подключение к Redis
    r = redis.Redis(host=os.getenv('REDIS_HOST', 'redis-service'), port=6379, decode_responses=True)

    for symbol in symbols:
        price = r.get(symbol)
        source = "cache"
        if not price:
            res = requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}')
            price = res.json()['price']
            r.set(symbol, price, ex=60)
            source = "api"
        
        results[symbol] = {"price": price, "source": source}
        # ВЫЗЫВАЕМ ЗАПИСЬ
        save_to_db(symbol, price)
        
    return render_template('index.html', data=results, host=socket.gethostname())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)