import bcrypt   # Hash password 
import jwt      # JWT tokens
import datetime # Token expiration time
import os       # Read .env
import uuid     # Create unique ID
import secrets # Short token

# JWT basic setting
# Read secret key from .env, or use default 
JWT_SECRET = os.getenv('JWT_SECRET', 'change-me-in-prod')
JWT_ALGORITHM = 'HS256'     # Algorithm used to sign the token
TOKEN_EXPIRE_MINUTES = 60   # limit token time for 60 minutes

def hash_password(password: str) -> str:
    """Hash password for secure storage"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Check if the password is correct"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8')) # Returns True if match

def create_token(user_id: int, email: str, name: str) -> str:
    """
    Create a JWT token for login.
    Includes a JTI (JWT Token ID) for logout.
    """
    expiration = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    jti = uuid.uuid4().hex  # Create unique token ID
    
    payload = {
        'user_id': user_id,
        'email': email,
        'name': name,
        'jti': jti,  # Unique token ID for logout
        'exp': expiration
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    """Read and verify token"""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise Exception('Token expired')
    except jwt.InvalidTokenError:
        raise Exception('Invalid token')

def create_short_token(length: int = 12) -> str:
    """Create short for URL"""
    return secrets.token_urlsafe(length)[:length]
