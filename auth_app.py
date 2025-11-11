from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import datetime, timezone
import os

from database import init_db, get_db, add_to_db
from models import User, BlacklistedToken
from auth import hash_password, decode_token, verify_password, create_token, create_short_token

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


# add token jti to blacklist until expiration
def _blacklist_token(db, jti: str, exp_ts: int):
    expires_at = datetime.fromtimestamp(exp_ts, tz=timezone.utc)
    db.add(BlacklistedToken(jti=jti, expires_at=expires_at))
    db.commit()


# check if token jti is revoked
def _is_blacklisted(db, jti: str) -> bool:
    return db.query(BlacklistedToken).filter(BlacklistedToken.jti == jti).first() is not None


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
        short_token = create_short_token(12)
        
        new_user = User(email=email, name=name, password_hash=hashed, short_token=short_token)
        add_to_db(db, new_user)

    return jsonify({
        "user_id": new_user.id,
        "short_token": new_user.short_token,
        "message": "User created successfully"
    }), 201


# User login (Thomas Sharp)
@app.route('/auth/login', methods=['POST'])
def login():
    data = request.json or {}
    email = data.get('email', '').lower().strip()
    password = data.get('password', '')

    # check required fields
    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    with get_db() as db:
        # find user
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return jsonify({"error": "Invalid email or password"}), 401

        # verify password
        if not verify_password(password, user.password_hash):
            return jsonify({"error": "Invalid email or password"}), 401

        # Create short token if missing
        if not user.short_token:
            user.short_token = create_short_token(12)
            db.commit()
            db.refresh(user)
        
        # create token
        token = create_token(user.id, user.email, user.name)

    # return success + token
    return jsonify({
        "token": token,
        "user_id": user.id,
        "short_token": user.short_token,
        "message": "Login Successful",
    }), 200

@app.route('/auth/exists', methods=['GET'])
def exists():
    email = request.args.get("email", "").strip()
    if not email:
        return jsonify({"message": "no email provided"}), 400
    with get_db() as db:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return jsonify({"message": "email availiable"}), 200
    return jsonify({"message": "email taken"}), 401

# User logout (Elliot)
@app.route('/auth/logout', methods=['POST'])
def logout():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "No token provided"}), 401

    token = auth_header.split(' ')[1]
    try:
        payload = decode_token(token)
    except Exception:
        return jsonify({"message": "Already logged out or token invalid"}), 200

    jti = payload.get('jti')
    exp = payload.get('exp')
    if not jti or not exp:
        return jsonify({"error": "Invalid token payload"}), 400

    with get_db() as db:
        if _is_blacklisted(db, jti):
            return jsonify({"message": "Already logged out"}), 200
        _blacklist_token(db, jti, exp)

    return jsonify({"message": "Logout successful"}), 200



# User Delete (Thomas Sharp)
@app.route('/auth/delete-account', methods=['POST'])
def delete_account():
    # Verify account token
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "No token provided"}), 401

    token = auth_header.split(' ')[1]
    info = decode_token(token)

    jti = info.get('jti')
    exp = info.get('exp')
    if not jti:
        return jsonify({"error": "Invalid token payload"}), 400

    with get_db() as db:
        if _is_blacklisted(db, jti):
            return jsonify({"error": "Token revoked"}), 401
        _blacklist_token(db, jti, exp)
        
        user = db.query(User).filter(User.id == info['user_id']).first()
        db.delete(user)
        db.commit()
    
    return jsonify({
        "message": "account successfully deleted",
        "user": {
            "id": info['user_id'],
            "email": info['email'],
            "name": info['name']
        }
    }), 200

# Check token validation
@app.route('/auth/verify', methods=['GET'])
def verify():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "No token provided"}), 401

    token = auth_header.split(' ')[1]
    payload = decode_token(token)

    jti = payload.get('jti')
    if not jti:
        return jsonify({"error": "Invalid token payload"}), 400

    with get_db() as db:
        if _is_blacklisted(db, jti):
            return jsonify({"error": "Token revoked"}), 401

    return jsonify({
        "valid": True,
        "user": {
            "id": payload['user_id'],
            "email": payload['email'],
            "name": payload['name']
        }
    }), 200

# Find user by short token
@app.route('/auth/user-by-short/<short_token>', methods=['GET'])
def get_user_by_short(short_token):
    with get_db() as db:
        user = db.query(User).filter(User.short_token == short_token).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        return jsonify({
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "short_token": user.short_token,
        }), 200
        


adminCode = os.getenv("ADMIN_CODE")

@app.template_filter('friendly_datetime')
def friendly_datetime(value, format="%B %d, %Y at %I:%M %p"):
    """ Convert the date info from the database into a human readable format

    Args:
        value (str): The incoming dateTime string
        format (str): The format options for the returned dateTime string.

    Returns:
        str: The formatted dateTime string 
    """
    if not value:
        return "NULL"
    if isinstance(value, str):
        # Convert ISO string to datetime
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return value.strftime(format)

@app.route("/")
def index():
    """ Routes the user to the main UI page once opened
    
    Returns:
        rendering of templates/index.html
    """
    return render_template("index.html")

@app.route("/renderDebugMode", methods=["POST"])
def renderDebugMode():
    """ Routes the user to the admin pannel if the admin code
        From the "/" route matches the ADMIN_CODE env variable
    
    Returns:
        if the admin code is correct:
           redirect to the /admin route
        if the admin code is incoreect:
            rendering of templates/index.html 
    """
    if(request.form.get("AdminCode") == adminCode):
        return redirect(url_for("adminPannel", access_code = adminCode));
    return redirect(url_for("index"))


@app.route("/admin/<access_code>")
def adminPannel(access_code):
    """ Routes the user to the admin pannel via 
        /admin/<access_code>?view=<view_name>

    Args:
        access_code (string): The access code for your program
        view_name (string): the name of the view you want to enter
                            in the admin pannel
            Options: [
    
    Returns:
        if all arguments are correct / provided:
            rendering of the appropiate view from templates/admin-<view_name>View.html
        if access_code isn't valid:
            redirect to "/"
    """
    if access_code != adminCode:
        return redirect(url_for("index"))
    
    view = request.args.get("view")
    if view is None:
        # Redirect to same route with view="users"
        return redirect(url_for("adminPannel", access_code=access_code, view="users"))
    with get_db() as db:
        if view == "users":
            data = db.query(User).all()  # All email logs
            return render_template("admin-usersView.html", auth_data=data, access_code=access_code)
        elif view == "blacklist":
            data = db.query(BlacklistedToken).all()  # All email logs
            now = datetime.now(timezone.utc)
            enriched = []
            for t in data:
                expires_at = t.expires_at
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)
                enriched.append({
                    "id": t.id,
                    "jti": t.jti,
                    "created_at": t.created_at,
                    "expires_at": expires_at,
                    "valid": expires_at > now
                })
            return render_template("admin-blacklistView.html",blacklist_data=enriched,access_code=access_code)
        elif view == "add_user":
            return render_template("admin-addUser.html", access_code=access_code)


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))

    app.run(host='0.0.0.0', port=port, debug=True)
