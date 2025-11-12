#!/usr/bin/env python3
"""
Auth Microservice - HTTP Test Program

Covers end-to-end HTTP communication with the running microservice:
- Health check
- Register (happy + errors)
- Login (happy + errors)
- Verify (happy + errors, tampered, missing bearer)
- Logout (idempotent)
- Exists (availability + errors)
- User by short token (happy + 404)
- Delete account flow (happy + follow-up failures)

Run while the service is up:  python auth_app.py  (listens on http://localhost:5001)

Requirements: pip install requests
"""

import os
import sys
import json
import time
from datetime import datetime

try:
    import requests
except ImportError:
    print("This test script requires the 'requests' package. Install it with:\n\n  python -m pip install requests\n")
    sys.exit(1)


# ----------------------------
#   Configuration
# ----------------------------
BASE_URL = os.getenv("AUTH_BASE_URL", "http://localhost:5001")
DEFAULT_EMAIL = os.getenv("AUTH_TEST_EMAIL", "bob@example.com")
DEFAULT_PASS  = os.getenv("AUTH_TEST_PASS",  "pass1234")
DEFAULT_NAME  = os.getenv("AUTH_TEST_NAME",  "Bob")

TIMEOUT = 10


def p(header):
    print("\n" + header)
    print("-" * len(header))


def pretty(obj):
    return json.dumps(obj, indent=2, ensure_ascii=False)


def request_json(method, url, *, headers=None, params=None, json_body=None, expect_status=None):
    """Thin wrapper around requests to standardize logging + errors"""
    headers = headers or {}
    try:
        resp = requests.request(method, url, headers=headers, params=params, json=json_body, timeout=TIMEOUT)
    except Exception as e:
        print(f"REQUEST ERROR: {e}")
        raise

    # basic log line
    print(f"{method} {url}  ->  {resp.status_code}")
    if resp.headers.get("Content-Type", "").startswith("application/json"):
        try:
            data = resp.json()
        except Exception:
            data = {"_raw": resp.text}
    else:
        data = {"_raw": resp.text}

    if expect_status is not None and resp.status_code != expect_status:
        print("Unexpected status code")
        print("Response:", pretty(data))
        raise AssertionError(f"Expected {expect_status} but got {resp.status_code}")

    return resp, data


def run():
    print("=" * 72)
    print("AUTH MICROSERVICE - HTTP COMMUNICATION TESTS")
    print("=" * 72)
    print(f"Target: {BASE_URL}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # ---------------- Health ----------------
    p("Health")
    _, data = request_json("GET", f"{BASE_URL}/health", expect_status=200)
    assert data.get("status") == "ok" and data.get("service") == "auth-microservice"

    # ---------------- Register ----------------
    p("Register (happy path; 201 on first run, 409 on repeats)")
    payload = {"email": DEFAULT_EMAIL, "password": DEFAULT_PASS, "name": DEFAULT_NAME}
    resp, data = request_json("POST", f"{BASE_URL}/auth/register", json_body=payload)
    assert resp.status_code in (201, 409), f"Expected 201/409 for register, got {resp.status_code}"

    # Missing fields -> 400
    p("Register (missing fields -> 400)")
    _, _ = request_json("POST", f"{BASE_URL}/auth/register", json_body={"email":"", "password":"", "name":""}, expect_status=400)

    # Short password -> 400
    p("Register (short password -> 400)")
    _, _ = request_json("POST", f"{BASE_URL}/auth/register", json_body={"email":"short@example.com", "password":"123", "name":"Short"}, expect_status=400)

    # ---------------- Login ----------------
    p("Login (happy path -> 200)")
    login_resp, login_data = request_json("POST", f"{BASE_URL}/auth/login", json_body={"email": DEFAULT_EMAIL, "password": DEFAULT_PASS}, expect_status=200)
    token = login_data.get("token")
    short_token = login_data.get("short_token")
    assert token and isinstance(token, str), "Missing JWT token in login response"

    # Wrong password -> 401
    p("Login (wrong password -> 401)")
    _, _ = request_json("POST", f"{BASE_URL}/auth/login", json_body={"email": DEFAULT_EMAIL, "password": "wrongpass"}, expect_status=401)

    # Nonexistent user -> 401
    p("Login (nonexistent user -> 401)")
    _, _ = request_json("POST", f"{BASE_URL}/auth/login", json_body={"email": "nouser@example.com", "password": "AnyPass123"}, expect_status=401)

    # ---------------- Verify / Short Lookup ----------------
    p("Verify (valid -> 200)")
    _, data = request_json("GET", f"{BASE_URL}/auth/verify", headers={"Authorization": f"Bearer {token}"}, expect_status=200)
    assert data.get("valid") is True and data.get("user", {}).get("email"), "Verify missing expected fields"

    p("User by short (valid -> 200)")
    _, _ = request_json("GET", f"{BASE_URL}/auth/user-by-short/{short_token}", expect_status=200)

    p("Verify (missing header -> 401)")
    _, _ = request_json("GET", f"{BASE_URL}/auth/verify", expect_status=401)

    p("Verify (tampered token -> 401)")
    tampered = "X" + token[1:]
    _, _ = request_json("GET", f"{BASE_URL}/auth/verify", headers={"Authorization": f"Bearer {tampered}"}, expect_status=401)

    p("Logout (missing Bearer prefix -> 401)")
    _, _ = request_json("POST", f"{BASE_URL}/auth/logout", headers={"Authorization": token}, expect_status=401)

    # ---------------- Exists ----------------
    p("Exists (taken -> 200)")
    _, data = request_json("GET", f"{BASE_URL}/auth/exists", params={"email": DEFAULT_EMAIL}, expect_status=200)
    assert data.get("message") in ("email taken", "email available")

    p("Exists (missing email -> 400)")
    _, _ = request_json("GET", f"{BASE_URL}/auth/exists", params={"email": ""}, expect_status=400)

    p("User by short (404 for bad token)")
    _, _ = request_json("GET", f"{BASE_URL}/auth/user-by-short/NOT_A_TOKEN", expect_status=404)

    # ---------------- Logout (idempotent) ----------------
    p("Logout (valid -> 200)")
    _, _ = request_json("POST", f"{BASE_URL}/auth/logout", headers={"Authorization": f"Bearer {token}"}, expect_status=200)

    p("Verify after logout (-> 401)")
    _, _ = request_json("GET", f"{BASE_URL}/auth/verify", headers={"Authorization": f"Bearer {token}"}, expect_status=401)

    p("Logout again (idempotent -> 200 'Already logged out')")
    _, data = request_json("POST", f"{BASE_URL}/auth/logout", headers={"Authorization": f"Bearer {token}"}, expect_status=200)
    assert data.get("message") in ("Already logged out", "Logout successful")

    # ---------------- Delete Account Flow ----------------
    p("Delete account flow (create → login → delete → verify 401 → login 401)")
    # a) create temp
    del_email = f"deleteme+{int(time.time())}@example.com"
    _ , _ = request_json("POST", f"{BASE_URL}/auth/register", json_body={"email": del_email, "password": "Temp123!", "name": "ToDelete"})
    # b) login
    _, del_login = request_json("POST", f"{BASE_URL}/auth/login", json_body={"email": del_email, "password": "Temp123!"}, expect_status=200)
    del_token = del_login["token"]
    # c) delete
    _, _ = request_json("POST", f"{BASE_URL}/auth/delete-account", headers={"Authorization": f"Bearer {del_token}"}, expect_status=200)
    # d) verify -> 401
    _, _ = request_json("GET", f"{BASE_URL}/auth/verify", headers={"Authorization": f"Bearer {del_token}"}, expect_status=401)
    # e) login again -> 401
    _, _ = request_json("POST", f"{BASE_URL}/auth/login", json_body={"email": del_email, "password": "Temp123!"}, expect_status=401)

    print("\n" + "=" * 72)
    print("HTTP COMMUNICATION SUCCESSFULLY DEMONSTRATED")
    print("=" * 72)
    print("All primary and negative-path scenarios passed.")
    return True


if __name__ == "__main__":
    ok = run()
    sys.exit(0 if ok else 1)
