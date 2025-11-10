from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os

from database import init_db, get_db, add_to_db
from models import User
from auth import hash_password, decode_token  # login teammate will use verify_password later

load_dotenv()
app = Flask(__name__)

# Allow frontend access to these endpoints
CORS(app, resources={
    r"/auth/*": {
        "origins": ["http://localhost:5173"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Create database tables if not exist
init_db()


@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "auth-microservice"}), 200


# User registration (Olivia)
@app.route('/auth/register', methods=['POST'])
def register():
    data = request.json or {}
    email = data.get('email', '').lower().strip()
    password = data.get('password', '')
    name = data.get('name', '').strip()

    # Check required fields
    if not email or not password or not name:
        return jsonify({"error": "All fields are required"}), 400
    
    # Password must be at least 6 characters
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    with get_db() as db:
        # Check if email already used
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            return jsonify({"error": "Email already exists"}), 409

        # Save new user with hashed password
        hashed = hash_password(password)
        new_user = User(email=email, name=name, password_hash=hashed)
        add_to_db(db, new_user)

    return jsonify({
        "user_id": new_user.id,
        "message": "User created successfully"
    }), 201


# User login (teammate)
@app.route('/auth/login', methods=['POST'])
def login():
    # TODO: implement by login owner
    return jsonify({"message": "login not implemented"}), 501


# User logout (Elliot)
@app.route('/auth/logout', methods=['POST'])
def logout():
    # TODO: implement by logout owner
    return jsonify({"message": "logout not implemented"}), 501


# Check token validation
@app.route('/auth/verify', methods=['GET'])
def verify():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "No token provided"}), 401

    token = auth_header.split(' ')[1]
    payload = decode_token(token)

    return jsonify({
        "valid": True,
        "user": {
            "id": payload['user_id'],
            "email": payload['email'],
            "name": payload['name']
        }
    }), 200


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)