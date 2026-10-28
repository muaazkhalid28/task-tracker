import os, time, socket
from flask import Flask, request, jsonify, render_template
import psycopg2

app = Flask(__name__)

def get_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "db"),
        dbname=os.getenv("DB_NAME", "tasksdb"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "secret"),
    )

def init_db():
    for _ in range(20):          # wait until the database is ready
        try:
            conn = get_conn(); cur = conn.cursor()
            cur.execute("CREATE TABLE IF NOT EXISTS tasks (id SERIAL PRIMARY KEY, title TEXT NOT NULL)")
            conn.commit(); cur.close(); conn.close()
            return
        except Exception:
            time.sleep(2)

@app.route("/")
def home():
    return render_template("index.html", host=socket.gethostname())

@app.route("/health")
def health():
    return "200", 200

@app.route("/api/tasks", methods=["GET"])
def list_tasks():
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT id, title FROM tasks ORDER BY id")
    rows = [{"id": r[0], "title": r[1]} for r in cur.fetchall()]
    cur.close(); conn.close()
    return jsonify(rows)

@app.route("/api/tasks", methods=["POST"])
def add_task():
    title = request.json.get("title", "").strip()
    if title:
        conn = get_conn(); cur = conn.cursor()
        cur.execute("INSERT INTO tasks (title) VALUES (%s)", (title,))
        conn.commit(); cur.close(); conn.close()
    return jsonify({"ok": True})

init_db()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
