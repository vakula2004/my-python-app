import os
import requests
import redis
import psycopg2
from psycopg2 import pool
import socket
from flask import Flask, render_template
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Counter
import time
REQUEST_COUNT = Counter('flask_app_requests_total', 'Total HTTP Requests')
app = Flask(__name__)
metrics = PrometheusMetrics(app) # Это автоматически создаст эндпоинт /metrics

# 1. Глобальный Redis (одно соединение на весь процесс)
r = redis.Redis(
    host=os.getenv('REDIS_HOST', 'redis-service'), 
    port=6379, 
    decode_responses=True
)

# 2. Пул соединений для PostgreSQL
try:
    db_pool = psycopg2.pool.SimpleConnectionPool(
        1, 10, # Минимум 1, максимум 10 соединений
        host=os.getenv('DB_HOST', 'postgres-service'),
        database='cryptodb',
        user='postgres',
        password=os.getenv('DB_PASSWORD', 'supersecret'),
        connect_timeout=2
    )
except Exception as e:
    print(f"CRITICAL: Could not create DB pool: {e}")

def get_db_conn():
    return db_pool.getconn()

def put_db_conn(conn):
    db_pool.putconn(conn)

def save_to_db(symbol, price):
    conn = None
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("INSERT INTO history (symbol, price) VALUES (%s, %s)", (symbol, str(price)))
        conn.commit()
        cur.close()
    except Exception as e:
        print(f"!!! ОШИБКА ЗАПИСИ: {e}")
    finally:
        if conn: put_db_conn(conn)

@app.route('/health')
def health():
    conn = None
    try:
        conn = get_db_conn()
        return "OK", 200
    except Exception as e:
        return f"Database unreachable: {e}", 500
    finally:
        if conn: put_db_conn(conn)
@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}
@app.route('/')
def index():
    REQUEST_COUNT.inc() # Увеличиваем при каждом заходе
    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
    results = {}
    
    # Сбор текущих цен
    for symbol in symbols:
        price = r.get(symbol)
        source = "cache"
        if not price:
            try:
                res = requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}', timeout=5)
                price = res.json()['price']
                r.set(symbol, price, ex=60)
                source = "api"
                save_to_db(symbol, price)
            except Exception as e:
                print(f"Ошибка API {symbol}: {e}")
                price = "0.0"
        results[symbol] = {"price": price, "source": source}

    # Сбор данных для таблиц и графиков
    history_table = []
    graph_data = {s: {'prices': [], 'times': []} for s in symbols}
    
    conn = None
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        
        # Последние записи
        cur.execute("SELECT symbol, price, tstamp FROM history ORDER BY tstamp DESC LIMIT 10;")
        history_table = cur.fetchall()
        
        # Данные для графиков
        cur.execute("""
            SELECT symbol, price, tstamp FROM (
                SELECT symbol, price, tstamp, 
                ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY tstamp DESC) as rn
                FROM history
                WHERE symbol IN ('BTCUSDT', 'ETHUSDT', 'BNBUSDT')
            ) t WHERE rn <= 20 ORDER BY tstamp ASC;
        """)
        
        for row in cur.fetchall():
            sym = row[0]
            if sym in graph_data:
                graph_data[sym]['prices'].append(float(row[1]))
                graph_data[sym]['times'].append(row[2].strftime('%H:%M:%S'))
        cur.close()
    except Exception as e:
        print(f"!!! ОШИБКА БАЗЫ: {e}")
    finally:
        if conn: put_db_conn(conn)

    return render_template('index.html', 
                           data=results, 
                           history=history_table, 
                           graph_json=graph_data, 
                           host=socket.gethostname())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)