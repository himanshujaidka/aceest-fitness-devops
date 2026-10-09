"""ACEest Fitness & Gym - small Flask application for the DevOps assignment."""
import os
import sqlite3
from pathlib import Path
from flask import Flask, jsonify, request, render_template_string

DEFAULT_DB = Path(os.environ.get("ACEEST_DB_PATH", "aceest_fitness.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    age INTEGER NOT NULL CHECK(age > 0 AND age < 120),
    weight REAL NOT NULL CHECK(weight > 0),
    program TEXT NOT NULL,
    calories INTEGER NOT NULL CHECK(calories > 0)
);
CREATE TABLE IF NOT EXISTS progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    week TEXT NOT NULL,
    adherence INTEGER NOT NULL CHECK(adherence >= 0 AND adherence <= 100),
    FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE,
    UNIQUE(client_id, week)
);
"""

PROGRAM_FACTORS = {
    "Fat Loss": 22,
    "Muscle Gain": 35,
    "Beginner": 26,
}


def connect_db(path=None):
    db_path = str(path or DEFAULT_DB)
    if db_path != ":memory:":
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def create_app(test_config=None):
    application = Flask(__name__)
    application.config.update(
        DATABASE=str(DEFAULT_DB),
        TESTING=False,
        JSON_SORT_KEYS=False,
    )
    if test_config:
        application.config.update(test_config)

    connection = connect_db(application.config["DATABASE"])
    try:
        connection.executescript(SCHEMA)
        connection.commit()
    finally:
        connection.close()

    def db_connection():
        return connect_db(application.config["DATABASE"])

    @application.get("/")
    def index():
        return render_template_string("""
        <!doctype html>
        <html lang="en">
        <head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
        <title>ACEest Fitness &amp; Gym</title>
        <style>
          body{font-family:Arial,sans-serif;max-width:850px;margin:40px auto;padding:0 18px;background:#171717;color:#f4f4f4}
          header{background:#d4af37;color:#111;padding:20px;border-radius:10px}
          code{background:#292929;padding:3px 6px;border-radius:4px}
          a{color:#e6c85a} li{margin:9px 0}
        </style></head>
        <body><header><h1>ACEest Fitness &amp; Gym</h1>
        <p>A lightweight fitness client and weekly progress service.</p></header>
        <h2>Available endpoints</h2><ul>
        <li><code>GET /health</code> — application health check</li>
        <li><code>GET /api/clients</code> — list clients</li>
        <li><code>POST /api/clients</code> — create a client</li>
        <li><code>GET /api/clients/&lt;id&gt;</code> — get one client</li>
        <li><code>PUT /api/clients/&lt;id&gt;</code> — update a client</li>
        <li><code>DELETE /api/clients/&lt;id&gt;</code> — delete a client</li>
        <li><code>GET /api/clients/&lt;id&gt;/progress</code> — list weekly progress</li>
        <li><code>POST /api/clients/&lt;id&gt;/progress</code> — record weekly adherence</li>
        </ul><p>See <a href="https://github.com/">GitHub</a> repository README for setup and testing instructions.</p></body></html>
        """)

    @application.get("/health")
    def health():
        return jsonify(status="ok", service="aceest-fitness")

    def parse_client_payload(payload, partial=False):
        if not isinstance(payload, dict):
            raise ValueError("Request body must be a JSON object.")
        data = {}
        allowed = {"name", "age", "weight", "program"}
        unknown = set(payload) - allowed
        if unknown:
            raise ValueError(f"Unsupported field(s): {', '.join(sorted(unknown))}")
        if not partial or "name" in payload:
            name = payload.get("name")
            if not isinstance(name, str) or not name.strip():
                raise ValueError("Name is required.")
            data["name"] = name.strip()
        if not partial or "age" in payload:
            try:
                age = int(payload.get("age"))
            except (TypeError, ValueError):
                raise ValueError("Age must be a whole number.")
            if age <= 0 or age >= 120:
                raise ValueError("Age must be between 1 and 119.")
            data["age"] = age
        if not partial or "weight" in payload:
            try:
                weight = float(payload.get("weight"))
            except (TypeError, ValueError):
                raise ValueError("Weight must be a number.")
            if weight <= 0:
                raise ValueError("Weight must be greater than zero.")
            data["weight"] = weight
        if not partial or "program" in payload:
            program = payload.get("program")
            if program not in PROGRAM_FACTORS:
                raise ValueError("Program must be Fat Loss, Muscle Gain, or Beginner.")
            data["program"] = program
        if "weight" in data and "program" in data:
            data["calories"] = round(data["weight"] * PROGRAM_FACTORS[data["program"]])
        return data

    @application.get("/api/clients")
    def list_clients():
        with db_connection() as connection:
            rows = connection.execute("SELECT * FROM clients ORDER BY id").fetchall()
        return jsonify([dict(row) for row in rows])

    @application.post("/api/clients")
    def create_client():
        try:
            data = parse_client_payload(request.get_json(silent=True))
        except ValueError as error:
            return jsonify(error=str(error)), 400
        with db_connection() as connection:
            try:
                cursor = connection.execute(
                    "INSERT INTO clients(name, age, weight, program, calories) VALUES(?,?,?,?,?)",
                    (data["name"], data["age"], data["weight"], data["program"], data["calories"]),
                )
            except sqlite3.IntegrityError:
                return jsonify(error="A client with that name already exists."), 409
            row = connection.execute("SELECT * FROM clients WHERE id=?", (cursor.lastrowid,)).fetchone()
        return jsonify(dict(row)), 201

    @application.get("/api/clients/<int:client_id>")
    def get_client(client_id):
        with db_connection() as connection:
            row = connection.execute("SELECT * FROM clients WHERE id=?", (client_id,)).fetchone()
        if row is None:
            return jsonify(error="Client not found."), 404
        return jsonify(dict(row))

    @application.put("/api/clients/<int:client_id>")
    def update_client(client_id):
        with db_connection() as connection:
            existing = connection.execute("SELECT * FROM clients WHERE id=?", (client_id,)).fetchone()
            if existing is None:
                return jsonify(error="Client not found."), 404
            payload = request.get_json(silent=True)
            try:
                data = parse_client_payload(payload, partial=True)
            except ValueError as error:
                return jsonify(error=str(error)), 400
            merged = dict(existing)
            merged.update(data)
            # Recalculate calories whenever weight or program changes.
            if "weight" in data or "program" in data:
                merged["calories"] = round(float(merged["weight"]) * PROGRAM_FACTORS[merged["program"]])
            try:
                connection.execute(
                    "UPDATE clients SET name=?, age=?, weight=?, program=?, calories=? WHERE id=?",
                    (merged["name"], merged["age"], merged["weight"], merged["program"], merged["calories"], client_id),
                )
            except sqlite3.IntegrityError:
                return jsonify(error="A client with that name already exists."), 409
            row = connection.execute("SELECT * FROM clients WHERE id=?", (client_id,)).fetchone()
        return jsonify(dict(row))

    @application.delete("/api/clients/<int:client_id>")
    def delete_client(client_id):
        with db_connection() as connection:
            cursor = connection.execute("DELETE FROM clients WHERE id=?", (client_id,))
            if cursor.rowcount == 0:
                return jsonify(error="Client not found."), 404
        return jsonify(message="Client deleted.")

    @application.get("/api/clients/<int:client_id>/progress")
    def list_progress(client_id):
        with db_connection() as connection:
            client = connection.execute("SELECT id FROM clients WHERE id=?", (client_id,)).fetchone()
            if client is None:
                return jsonify(error="Client not found."), 404
            rows = connection.execute(
                "SELECT id, client_id, week, adherence FROM progress WHERE client_id=? ORDER BY week",
                (client_id,),
            ).fetchall()
        return jsonify([dict(row) for row in rows])

    @application.post("/api/clients/<int:client_id>/progress")
    def create_progress(client_id):
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify(error="Request body must be a JSON object."), 400
        week = payload.get("week")
        adherence = payload.get("adherence")
        if not isinstance(week, str) or not week.strip():
            return jsonify(error="Week is required."), 400
        if isinstance(adherence, bool) or not isinstance(adherence, int) or not 0 <= adherence <= 100:
            return jsonify(error="Adherence must be an integer from 0 to 100."), 400
        with db_connection() as connection:
            if connection.execute("SELECT id FROM clients WHERE id=?", (client_id,)).fetchone() is None:
                return jsonify(error="Client not found."), 404
            try:
                cursor = connection.execute(
                    "INSERT INTO progress(client_id, week, adherence) VALUES(?,?,?)",
                    (client_id, week.strip(), adherence),
                )
            except sqlite3.IntegrityError:
                return jsonify(error="Progress for this client and week already exists."), 409
            row = connection.execute("SELECT * FROM progress WHERE id=?", (cursor.lastrowid,)).fetchone()
        return jsonify(dict(row)), 201

    return application


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
