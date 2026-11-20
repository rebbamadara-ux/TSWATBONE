import os
import re
import uuid
from datetime import datetime, timezone

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

app = Flask(__name__)

database_url = os.getenv("DATABASE_URL", "sqlite:///rebba_dev.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
db = SQLAlchemy(app)

USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,20}$")
serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"] or "local-dev-only-change-me")

class Player(db.Model):
    __tablename__ = "players"

    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.String(36), unique=True, nullable=False, index=True)
    username = db.Column(db.String(20), unique=True, nullable=False, index=True)
    email = db.Column(db.String(254), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    level = db.Column(db.Integer, nullable=False, default=1)
    experience = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False,
                           default=lambda: datetime.now(timezone.utc))

    def public_data(self):
        return {
            "player_id": self.player_id,
            "username": self.username,
            "level": self.level,
            "experience": self.experience,
            "created_at": self.created_at.isoformat()
        }

def issue_token(player):
    return serializer.dumps({"player_id": player.player_id}, salt="rebba-auth")

def current_player():
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    token = header[7:].strip()
    if not token:
        return None
    try:
        payload = serializer.loads(token, salt="rebba-auth", max_age=60 * 60 * 24 * 7)
    except (BadSignature, SignatureExpired):
        return None
    return Player.query.filter_by(player_id=payload.get("player_id")).first()

@app.get("/")
def index():
    return jsonify({
        "service": "REBBA Auth API",
        "status": "online",
        "note": "Authentication test service; not a complete Free Fire game server."
    })

@app.get("/health")
def health():
    try:
        db.session.execute(db.text("SELECT 1"))
        return jsonify({"ok": True, "database": "connected"}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"ok": False, "database": "unavailable"}), 503

@app.post("/api/auth/register")
def register():
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))

    if not USERNAME_RE.fullmatch(username):
        return jsonify({"error": "username must be 3-20 characters: letters, numbers, underscore"}), 400
    if len(email) > 254 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        return jsonify({"error": "valid email required"}), 400
    if len(password) < 10 or len(password) > 128:
        return jsonify({"error": "password must be 10-128 characters"}), 400

    if Player.query.filter_by(username=username).first():
        return jsonify({"error": "username already exists"}), 409
    if Player.query.filter_by(email=email).first():
        return jsonify({"error": "email already exists"}), 409

    player = Player(
        player_id=str(uuid.uuid4()),
        username=username,
        email=email,
        password_hash=generate_password_hash(password)
    )
    db.session.add(player)
    db.session.commit()
    return jsonify({
        "message": "account created",
        "player": player.public_data(),
        "token": issue_token(player)
    }), 201

@app.post("/api/auth/login")
def login():
    data = request.get_json(silent=True) or {}
    identity = str(data.get("identity", "")).strip()
    password = str(data.get("password", ""))

    player = Player.query.filter(
        db.or_(Player.username == identity, Player.email == identity.lower())
    ).first()

    if not player or not check_password_hash(player.password_hash, password):
        return jsonify({"error": "invalid login details"}), 401

    return jsonify({
        "message": "login successful",
        "player": player.public_data(),
        "token": issue_token(player)
    }), 200

@app.get("/api/player/me")
def me():
    player = current_player()
    if not player:
        return jsonify({"error": "missing or invalid token"}), 401
    return jsonify({"player": player.public_data()}), 200

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
