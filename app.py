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
def get_history():
    history = []
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'postgres-service'),
            database='cryptodb',
            user='postgres',
            password='supersecret'
        )
        cur = conn.cursor()
        cur.execute("SELECT symbol, price, tstamp FROM history ORDER BY tstamp DESC LIMIT 10;")
        history = cur.fetchall() # Получаем список кортежей
        cur.close()
        conn.close()
    except Exception as e:
        print(f"!!! ОШИБКА ЧТЕНИЯ БД: {e}")
    return history
@app.route('/health')
def health():
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'postgres-service'),
            database='cryptodb',
            user='postgres',
            password='supersecret',
            connect_timeout=2
        )
        conn.close()
        return "OK", 200
    except Exception as e:
        return f"Database unreachable: {e}", 500
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
        history_data = get_history()
        
    return render_template('index.html', 
                           data=results, 
                           history=history_data, 
                           host=socket.gethostname())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)