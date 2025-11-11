# User Authentication Microservice

Microservice Communication Contract

## Quick Start

```bash
python auth_app.py
```
Service runs on `http://localhost:5001`.

## Implementation Status

- **GET /health** — IMPLEMENTED
- **POST /auth/register** — IMPLEMENTED
- **POST /auth/login** — IMPLEMENTED
- **GET /auth/verify** — IMPLEMENTED (JWT + revocation check)
- **POST /auth/logout** — IMPLEMENTED (JWT jti blacklist + prune)
- **GET /auth/exists** — IMPLEMENTED (email availability; normalization)
- **GET /auth/user-by-short/:short_token** — IMPLEMENTED
- **POST /auth/delete-account** — IMPLEMENTED (revokes token + deletes user)

## Setup

```bash
git clone https://github.com/looking-sharp/User_Authentication_Microservice.git
cd User_Authentication_Microservice
python -m venv venv
# Windows PowerShell:
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#   .\venv\Scripts\Activate.ps1
# macOS/Linux:
#   source venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env   # then edit JWT_SECRET etc.
python auth_app.py
```

---

## ENDPOINTS

### 1) Health (IMPLEMENTED)

**Endpoint:** `GET /health`

**Purpose:** Service liveness.

**Response:**
```
HTTP 200 OK
{
  "status": "ok",
  "service": "auth-microservice"
}
```

---

### 2) Register User (IMPLEMENTED)

**Endpoint:** `POST /auth/register`  
**Purpose:** Create user with hashed password and short token

**Request:**
```
POST http://localhost:5001/auth/register
Content-Type: application/json

{
  "email": "alice@example.com",
  "password": "secret123",
  "name": "Alice"
}
```

**Responses:**
```
HTTP 201 Created
{
  "user_id": 1,
  "short_token": "KOmorIxUXwiR",
  "message": "User created successfully"
}
```
Errors:
- `400 Bad Request`: missing required fields or password too short
- `409 Conflict`: email already exists

---

### 3) Login (IMPLEMENTED)

**Endpoint:** `POST /auth/login`  
**Purpose:** Authenticate and return a signed JWT + short token (if not already issued)

**Request:**
```
POST http://localhost:5001/auth/login
Content-Type: application/json

{ "email": "alice@example.com", "password": "secret123" }
```

**Response:**
```
HTTP 200 OK
{
  "token": "<JWT>",
  "user_id": 1,
  "short_token": "KOmorIxUXwiR",
  "message": "Login Successful"
}
```
Errors:
- `400 Bad Request`: missing email or password
- `401 Unauthorized`: invalid credentials

---

### 4) Verify Token (IMPLEMENTED)

**Endpoint:** `GET /auth/verify`  
**Purpose:** Validate JWT, enforce revocation (blacklist), and return user info

**Headers:**
```
Authorization: Bearer <JWT>
```

**Response:**
```
HTTP 200 OK
{
  "valid": true,
  "user": { "id": 1, "email": "alice@example.com", "name": "Alice" }
}
```
Errors:
- `401 Unauthorized`: missing/invalid/expired/revoked token
- `400 Bad Request`: invalid token payload (missing jti)

---

### 5) Logout (IMPLEMENTED)

**Endpoint:** `POST /auth/logout`  
**Purpose:** Revoke current JWT by persisting its `jti` until expiration. Idempotent.

**Headers:**
```
Authorization: Bearer <JWT>
```

**Responses:**
```
HTTP 200 OK
{ "message": "Logout successful" }

HTTP 200 OK
{ "message": "Already logged out" }
```
Errors:
- `401 Unauthorized`: missing/invalid token

---

### 6) Email Availability (IMPLEMENTED)

**Endpoint:** `GET /auth/exists?email=<email>`  
**Purpose:** Check if an email is available. Email is normalized (trim + lowercase).

**Responses:**
```
HTTP 200 OK
{ "message": "email taken" }

HTTP 200 OK
{ "message": "email available" }

HTTP 400 Bad Request
{ "message": "no email provided" }
```

---

### 7) Lookup by Short Token (IMPLEMENTED)

**Endpoint:** `GET /auth/user-by-short/:short_token`  
**Purpose:** Resolve user info from short token.

**Response:**
```
HTTP 200 OK
{
  "id": 1,
  "email": "alice@example.com",
  "name": "Alice",
  "short_token": "KOmorIxUXwiR"
}
```
Errors:
- `404 Not Found`: `{ "error": "User not found" }`

---

### 8) Delete Account (IMPLEMENTED)

**Endpoint:** `POST /auth/delete-account`  
**Purpose:** Delete the authenticated user. Revokes the presented JWT before deletion.

**Headers:**
```
Authorization: Bearer <JWT>
```

**Response:**
```
HTTP 200 OK
{
  "message": "account successfully deleted",
  "user": { "id": 2, "email": "deleteme+123@example.com", "name": "ToDelete" }
}
```
Errors:
- `401 Unauthorized`: revoked/invalid token
- `400 Bad Request`: invalid token payload

---

## JWT & Security Model

- JWT payload includes: `user_id`, `email`, `name`, `jti`, `exp`
- **Revocation**: `/auth/logout` and `/auth/delete-account` store the `jti` in `blacklisted_tokens` until `exp`
- **Verification**: `/auth/verify` rejects tokens whose `jti` is blacklisted or whose signature/`exp` is invalid
- **Pruning**: expired blacklist rows are pruned on service startup and on each `/auth/verify` and `/auth/logout` call
- **Normalization**: emails are trimmed and lowercased before use

---

## Configuration

Environment Variables (`.env`):

- `JWT_SECRET` — signing key (default: `change-me-in-prod`)
- `DATABASE_URL` — SQLAlchemy URL (default: SQLite at `../data/auth.db`)
- `PORT` — Flask port (default: `5001`)

---

## Testing

A programmatic test runner is included: `test.py` (modeled after the Audit microservice tester).  
It performs real HTTP requests against the running service and prints results.

```bash
python -m pip install requests
python test.py
```

`test.py` covers:
- health
- register/login (happy & negative)
- verify (happy & negative; missing bearer; tampered)
- logout (idempotent behavior)
- exists (availability + missing email)
- user-by-short (happy + 404)
- delete-account flow (and post-delete failures)

---

## Dependencies

```
Flask==3.0.0
flask-cors==4.0.0
bcrypt==4.1.2
python-dotenv==1.0.0
pyjwt==2.8.0
SQLAlchemy==2.0.44
```

---

## Deployment Status

| Feature                      | Status     | Notes                                   |
|-----------------------------|------------|-----------------------------------------|
| **/health**                 | COMPLETE   |                                         |
| **/auth/register**          | COMPLETE   | field validation + duplicate checks     |
| **/auth/login**             | COMPLETE   | returns JWT + short token               |
| **/auth/verify**            | COMPLETE   | blacklist + expiry enforced             |
| **/auth/logout**            | COMPLETE   | JWT jti blacklist; idempotent           |
| **/auth/exists**            | COMPLETE   | normalized email check                  |
| **/auth/user-by-short**     | COMPLETE   | 404 on unknown                          |
| **/auth/delete-account**    | COMPLETE   | revokes then deletes user               |
| **Blacklist prune**         | COMPLETE   | startup + verify/logout                 |
