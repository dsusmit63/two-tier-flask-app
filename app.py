import os
import time

import mysql.connector
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# Database configuration
DB_CONFIG = {
    "host": os.environ.get("MYSQL_HOST", "db"),  # IMPORTANT: docker service name
    "user": os.environ.get("MYSQL_USER", "root"),
    "password": os.environ.get("MYSQL_PASSWORD", "password"),
    "database": os.environ.get("MYSQL_DB", "testdb"),
}


# Retry DB connection (handles container startup timing issues)
def get_db_connection():
    retries = 5
    while retries > 0:
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            print("✅ Connected to MySQL")
            return conn
        except mysql.connector.Error as err:
            print(f"❌ DB connection failed: {err}")
            retries -= 1
            time.sleep(3)

    raise Exception("Database connection failed after retries")


# Initialize database
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INT AUTO_INCREMENT PRIMARY KEY,
            message TEXT
        )
    """
    )

    conn.commit()
    cursor.close()
    conn.close()


@app.route("/")
def home():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT message FROM messages")
    messages = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("index.html", messages=messages)


@app.route("/submit", methods=["POST"])
def submit():
    new_message = request.form.get("new_message")

    if not new_message:
        return jsonify({"error": "Message cannot be empty"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO messages (message) VALUES (%s)", (new_message,))
    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({"message": new_message})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=False)
