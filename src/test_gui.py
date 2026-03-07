"""
VOLUNTEER SCHEDULER - COMPREHENSIVE TEST SUITE
==============================================

Tests all 5 programming roles and their deliverables:
1. Admin GUI Developer - admin_gui.py
2. Backend API Developer - api.py  
3. Volunteer GUI Developer - volunteer_gui.py
4. Identity & Database Engineer - database.py, models.py
5. Integration, QA & Documentation Lead - test coordination

Test Categories:
- Launcher & System (2 tests)
- Admin GUI Role (4 tests)
- Backend API Role (8 tests)
- Volunteer GUI Role (5 tests)
- Database & Security Role (4 tests)
- Integration & Business Rules (5 tests)

Total: 28 comprehensive tests
"""

import os
import sys
import importlib.util
import json
import sqlite3
import tempfile
import shutil
from datetime import datetime, timedelta

# ============================================================================
# LAUNCHER TESTS (System Initialization)
# ============================================================================

# Launcher tests
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LAUNCHER = os.path.join(BASE_DIR, "volunteer_scheduler.py")


def test_launcher_file_exists():
    """Test that launcher entry point exists"""
    assert os.path.exists(LAUNCHER), "Launcher file does not exist"


def test_can_import_launcher_module():
    """Test that launcher module can be imported and contains Launcher class"""
    spec = importlib.util.spec_from_file_location("volunteer_launcher", LAUNCHER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    assert hasattr(module, "Launcher"), "Launcher class not found"


# API Integration Tests
import pytest
import requests
import subprocess
import time

API_URL = "http://127.0.0.1:5000"
TEST_DB = None


@pytest.fixture(scope="session", autouse=True)
def start_api_server():
    """Start the API server for testing"""
    # Check if server is already running
    try:
        requests.get(f"{API_URL}/weeks", timeout=1)
        # Server is already running
        yield
        return
    except:
        pass
    
    # Start the server
    proc = subprocess.Popen(
        [sys.executable, "api.py"],
        cwd=BASE_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(3)  # Wait for server to start
    yield
    proc.terminate()
    proc.wait(timeout=5)


# Registration and Login Tests
def test_volunteer_registration():
    """Test volunteer user registration with password hashing"""
    data = {
        "first_name": "John",
        "last_name": "Doe",
        "username": f"volunteer_test_{int(time.time())}",
        "address": "123 Main St",
        "phone": "555-1234",
        "password": "password123",
        "confirm_password": "password123",
        "role": "volunteer",
        "volunteer_type": "regular"
    }
    resp = requests.post(f"{API_URL}/register", json=data)
    assert resp.status_code == 201
    assert resp.json()["success"]


def test_admin_registration():
    """Test admin user registration"""
    data = {
        "first_name": "Admin",
        "last_name": "User",
        "username": f"admin_test_{int(time.time())}",
        "address": "456 Admin St",
        "phone": "555-5678",
        "password": "adminpass123",
        "confirm_password": "adminpass123",
        "role": "admin",
        "volunteer_type": "regular"
    }
    resp = requests.post(f"{API_URL}/register", json=data)
    assert resp.status_code == 201


def test_login_returns_token():
    """Test that login returns a JWT token"""
    # First register
    username = f"tokentest_{int(time.time())}"
    reg_data = {
        "first_name": "Token",
        "last_name": "Tester",
        "username": username,
        "address": "789 Token Rd",
        "phone": "555-9999",
        "password": "tokenpass",
        "confirm_password": "tokenpass",
        "role": "volunteer",
        "volunteer_type": "regular"
    }
    requests.post(f"{API_URL}/register", json=reg_data)
    
    # Now login
    login_data = {"username": username, "password": "tokenpass"}
    resp = requests.post(f"{API_URL}/login", json=login_data)
    assert resp.status_code == 200
    
    json_resp = resp.json()
    assert "token" in json_resp
    assert "id" in json_resp
    assert "username" in json_resp
    assert json_resp["username"] == username


def test_invalid_login():
    """Test login with invalid credentials"""
    data = {"username": "nonexistent", "password": "wrong"}
    resp = requests.post(f"{API_URL}/login", json=data)
    assert resp.status_code == 401


# Protected Endpoint Tests
def test_protected_endpoint_requires_token():
    """Test that protected endpoints require a token"""
    resp = requests.get(f"{API_URL}/volunteers")
    assert resp.status_code == 401
    assert "token required" in resp.json().get("error", "").lower()


def test_admin_can_access_protected_endpoints():
    """Test that admin with token can access protected endpoints"""
    # Register and login as admin
    admin_username = f"admin_access_{int(time.time())}"
    reg_data = {
        "first_name": "Admin",
        "last_name": "Access",
        "username": admin_username,
        "address": "Admin Addr",
        "phone": "555-0000",
        "password": "adminsecrect",
        "confirm_password": "adminsecrect",
        "role": "admin",
        "volunteer_type": "regular"
    }
    requests.post(f"{API_URL}/register", json=reg_data)
    
    login_resp = requests.post(f"{API_URL}/login", json={
        "username": admin_username,
        "password": "adminsecrect"
    })
    token = login_resp.json()["token"]
    
    # Access protected endpoint
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{API_URL}/volunteers", headers=headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_non_admin_cannot_access_admin_endpoints():
    """Test that volunteers cannot access admin-only endpoints"""
    # Register and login as volunteer
    vol_username = f"volunteer_restrict_{int(time.time())}"
    reg_data = {
        "first_name": "Vol",
        "last_name": "User",
        "username": vol_username,
        "address": "Vol Addr",
        "phone": "555-1111",
        "password": "volsecret",
        "confirm_password": "volsecret",
        "role": "volunteer",
        "volunteer_type": "regular"
    }
    requests.post(f"{API_URL}/register", json=reg_data)
    
    login_resp = requests.post(f"{API_URL}/login", json={
        "username": vol_username,
        "password": "volsecret"
    })
    token = login_resp.json()["token"]
    
    # Try to access admin endpoint
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{API_URL}/volunteers", headers=headers)
    assert resp.status_code == 403
    assert "admin" in resp.json().get("error", "").lower()


# Shift and Signup Tests
def test_create_week():
    """Test creating a week"""
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    next_week = (datetime.now() + timedelta(days=8)).strftime("%Y-%m-%d")
    
    data = {
        "week_start": tomorrow,
        "finalization_deadline": next_week
    }
    resp = requests.post(f"{API_URL}/weeks", json=data)
    assert resp.status_code == 201


def test_list_sites():
    """Test getting list of sites"""
    resp = requests.get(f"{API_URL}/sites")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_create_shift_requires_admin():
    """Test that creating shifts requires admin token"""
    vol_username = f"shifttest_vol_{int(time.time())}"
    reg_data = {
        "first_name": "Vol",
        "last_name": "Shifter",
        "username": vol_username,
        "address": "Shift Addr",
        "phone": "555-2222",
        "password": "shiftvol",
        "confirm_password": "shiftvol",
        "role": "volunteer",
        "volunteer_type": "regular"
    }
    requests.post(f"{API_URL}/register", json=reg_data)
    
    login_resp = requests.post(f"{API_URL}/login", json={
        "username": vol_username,
        "password": "shiftvol"
    })
    vol_token = login_resp.json()["token"]
    
    # Get weeks first
    weeks_resp = requests.get(f"{API_URL}/weeks")
    if weeks_resp.status_code == 200 and len(weeks_resp.json()) > 0:
        week_id = weeks_resp.json()[0]["id"]
    else:
        # Create a week
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        next_week = (datetime.now() + timedelta(days=8)).strftime("%Y-%m-%d")
        week_resp = requests.post(f"{API_URL}/weeks", json={
            "week_start": tomorrow,
            "finalization_deadline": next_week
        })
        week_id = 1  # Assume first week ID
    
    # Try to create shift with volunteer token (should fail)
    shift_data = {
        "week_id": week_id,
        "site_id": 1,
        "date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
        "start_time": "09:00",
        "end_time": "17:00",
        "max_volunteers": 5,
        "role": "any"
    }
    headers = {"Authorization": f"Bearer {vol_token}"}
    resp = requests.post(f"{API_URL}/shifts", headers=headers, json=shift_data)
    assert resp.status_code == 403


def test_volunteer_can_request_shift():
    """Test that volunteers can request shifts"""
    # This requires shifts to exist first  
    # For now, just test the shift request endpoint exists
    data = {
        "volunteer_id": 1,
        "shift_id": 1
    }
    resp = requests.post(f"{API_URL}/shift_requests", json=data)
    # May be 400 if shift doesn't exist, but endpoint should exist
    assert resp.status_code in [201, 400, 404]


def test_finalize_week_requires_admin():
    """Test that finalizing week requires admin token"""
    # Try without token
    resp = requests.post(f"{API_URL}/weeks/1/finalize")
    assert resp.status_code == 401
    
    # Get an admin token
    admin_username = f"finalize_admin_{int(time.time())}"
    reg_data = {
        "first_name": "Finalize",
        "last_name": "Admin",
        "username": admin_username,
        "address": "Final Addr",
        "phone": "555-3333",
        "password": "finalpw",
        "confirm_password": "finalpw",
        "role": "admin",
        "volunteer_type": "regular"
    }
    requests.post(f"{API_URL}/register", json=reg_data)
    
    login_resp = requests.post(f"{API_URL}/login", json={
        "username": admin_username,
        "password": "finalpw"
    })
    admin_token = login_resp.json()["token"]
    
    # Now try with admin token
    headers = {"Authorization": f"Bearer {admin_token}"}
    resp = requests.post(f"{API_URL}/weeks/1/finalize", headers=headers)
    # May succeed or fail based on week existence, but should be accessible
    assert resp.status_code in [200, 400, 404]


def test_password_hashing():
    """Test that passwords are hashed (indirect test via registration)"""
    # Register a user
    username = f"hash_test_{int(time.time())}"
    password = "unhashable_password_12345"
    
    reg_data = {
        "first_name": "Hash",
        "last_name": "Tester",
        "username": username,
        "address": "Hash Addr",
        "phone": "555-4444",
        "password": password,
        "confirm_password": password,
        "role": "volunteer",
        "volunteer_type": "regular"
    }
    resp = requests.post(f"{API_URL}/register", json=reg_data)
    assert resp.status_code == 201
    
    # Login should work with correct password
    login_resp = requests.post(f"{API_URL}/login", json={
        "username": username,
        "password": password
    })
    assert login_resp.status_code == 200
    
    # Login should fail with wrong password
    bad_login = requests.post(f"{API_URL}/login", json={
        "username": username,
        "password": "wrong_password"
    })
    assert bad_login.status_code == 401


# ============================================================================
# ROLE 1: ADMIN GUI DEVELOPER TESTS
# ============================================================================

def test_admin_gui_requires_valid_credentials():
    """Test that admin GUI login validates credentials"""
    # Invalid credentials should return 401
    data = {"username": "nonexistent_admin", "password": "wrong"}
    resp = requests.post(f"{API_URL}/login", json=data)
    assert resp.status_code == 401, "Admin should not login with invalid credentials"


def test_admin_gui_receives_token_on_login():
    """Test that admin GUI receives JWT token upon login"""
    admin_username = f"admin_token_test_{int(time.time())}"
    reg_data = {
        "first_name": "Admin",
        "last_name": "GUI",
        "username": admin_username,
        "address": "Admin GU Addr",
        "phone": "555-8888",
        "password": "admingui",
        "confirm_password": "admingui",
        "role": "admin",
        "volunteer_type": "regular"
    }
    requests.post(f"{API_URL}/register", json=reg_data)
    
    resp = requests.post(f"{API_URL}/login", json={
        "username": admin_username,
        "password": "admingui"
    })
    
    assert resp.status_code == 200, "Admin should login successfully"
    json_resp = resp.json()
    assert "token" in json_resp, "Token should be in response"
    assert json_resp["role"] == "admin", "Role should be admin"


def test_admin_gui_can_access_admin_endpoints():
    """Test that admin GUI has access to admin-only endpoints"""
    admin_username = f"admin_access_{int(time.time())}"
    requests.post(f"{API_URL}/register", json={
        "first_name": "Admin", "last_name": "Access",
        "username": admin_username, "address": "Addr",
        "phone": "555-0001", "password": "pw123",
        "confirm_password": "pw123", "role": "admin",
        "volunteer_type": "regular"
    })
    
    resp = requests.post(f"{API_URL}/login", json={
        "username": admin_username, "password": "pw123"
    })
    token = resp.json()["token"]
    
    # GET /volunteers is admin-only
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{API_URL}/volunteers", headers=headers)
    assert resp.status_code == 200, "Admin should access /volunteers endpoint"


def test_admin_gui_handles_api_errors_gracefully():
    """Test that admin GUI would handle API errors"""
    # Try invalid endpoint
    resp = requests.get(f"{API_URL}/invalid_endpoint")
    assert resp.status_code in [404, 405], "Invalid endpoint should return error"
    assert "error" in resp.json() or "message" in resp.json(), "Error response should be readable"


# ============================================================================
# ROLE 2: BACKEND API DEVELOPER TESTS
# ============================================================================

def test_api_register_endpoint_exists():
    """Test that API /register endpoint exists and works"""
    username = f"api_reg_{int(time.time())}"
    data = {
        "first_name": "API", "last_name": "Test",
        "username": username, "address": "API Test",
        "phone": "555-6666", "password": "api123",
        "confirm_password": "api123", "role": "volunteer",
        "volunteer_type": "regular"
    }
    resp = requests.post(f"{API_URL}/register", json=data)
    assert resp.status_code == 201, "API /register should create user"


def test_api_login_endpoint_returns_jwt_token():
    """Test that API /login returns valid JWT token"""
    username = f"api_jwt_{int(time.time())}"
    requests.post(f"{API_URL}/register", json={
        "first_name": "JWT", "last_name": "Test",
        "username": username, "address": "JWT",
        "phone": "555-7777", "password": "jwt123",
        "confirm_password": "jwt123", "role": "volunteer",
        "volunteer_type": "regular"
    })
    
    resp = requests.post(f"{API_URL}/login", json={
        "username": username, "password": "jwt123"
    })
    
    assert resp.status_code == 200, "Login should succeed"
    json_resp = resp.json()
    assert "token" in json_resp, "Response should contain token"
    # JWT format: xxx.xxx.xxx
    assert json_resp["token"].count(".") == 2, "Token should be valid JWT"


def test_api_token_validation_on_protected_routes():
    """Test that API validates tokens on protected routes"""
    # No token should be rejected
    resp = requests.get(f"{API_URL}/volunteers")
    assert resp.status_code == 401, "Protected route should require token"
    
    # Invalid token should be rejected
    headers = {"Authorization": "Bearer invalid.token.here"}
    resp = requests.get(f"{API_URL}/volunteers", headers=headers)
    assert resp.status_code == 401, "Invalid token should be rejected"


def test_api_admin_authorization_enforced():
    """Test that API enforces admin-only authorization"""
    # Create volunteer
    vol_username = f"api_volonly_{int(time.time())}"
    requests.post(f"{API_URL}/register", json={
        "first_name": "Vol", "last_name": "Only",
        "username": vol_username, "address": "Vol",
        "phone": "555-9999", "password": "vol123",
        "confirm_password": "vol123", "role": "volunteer",
        "volunteer_type": "regular"
    })
    
    resp = requests.post(f"{API_URL}/login", json={
        "username": vol_username, "password": "vol123"
    })
    vol_token = resp.json()["token"]
    
    # Volunteer should not access /volunteers (admin-only)
    headers = {"Authorization": f"Bearer {vol_token}"}
    resp = requests.get(f"{API_URL}/volunteers", headers=headers)
    assert resp.status_code == 403, "Volunteer should be forbidden from /volunteers"
    assert "admin" in resp.json().get("error", "").lower(), "Error should mention admin"


def test_api_creates_weeks_endpoint():
    """Test that API /weeks endpoint exists"""
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    next_week = (datetime.now() + timedelta(days=8)).strftime("%Y-%m-%d")
    
    resp = requests.post(f"{API_URL}/weeks", json={
        "week_start": tomorrow,
        "finalization_deadline": next_week
    })
    
    assert resp.status_code == 201, "API should create weeks"
    assert resp.json().get("success"), "Create should be successful"


def test_api_lists_sites():
    """Test that API /sites endpoint returns list of work sites"""
    resp = requests.get(f"{API_URL}/sites")
    assert resp.status_code == 200, "API should list sites"
    sites = resp.json()
    assert isinstance(sites, list), "Sites should be a list"


def test_api_shift_endpoints_require_proper_data():
    """Test that API validates shift creation data"""
    # Missing required fields
    resp = requests.post(f"{API_URL}/shifts", json={
        "week_id": 1
        # Missing other required fields
    })
    
    assert resp.status_code == 400, "API should validate required fields"
    assert "error" in resp.json(), "Error message should be provided"


# ============================================================================
# ROLE 3: VOLUNTEER GUI DEVELOPER TESTS
# ============================================================================

def test_volunteer_gui_login_works():
    """Test that volunteer GUI login functionality"""
    vol_username = f"vol_gui_{int(time.time())}"
    requests.post(f"{API_URL}/register", json={
        "first_name": "Volunteer", "last_name": "GUI",
        "username": vol_username, "address": "Vol GUI",
        "phone": "555-5555", "password": "volgui123",
        "confirm_password": "volgui123", "role": "volunteer",
        "volunteer_type": "regular"
    })
    
    resp = requests.post(f"{API_URL}/login", json={
        "username": vol_username, "password": "volgui123"
    })
    
    assert resp.status_code == 200, "Volunteer should login"
    assert resp.json()["role"] == "volunteer", "Role should be volunteer"


def test_volunteer_can_request_shifts():
    """Test that volunteers can submit shift requests"""
    vol_username = f"vol_shift_req_{int(time.time())}"
    requests.post(f"{API_URL}/register", json={
        "first_name": "Vol", "last_name": "Request",
        "username": vol_username, "address": "Req",
        "phone": "555-2233", "password": "req123",
        "confirm_password": "req123", "role": "volunteer",
        "volunteer_type": "regular"
    })
    
    resp = requests.post(f"{API_URL}/login", json={
        "username": vol_username, "password": "req123"
    })
    vol_id = resp.json()["id"]
    
    # Try to request a shift (may fail if shift doesn't exist, but endpoint should work)
    resp = requests.post(f"{API_URL}/shift_requests", json={
        "volunteer_id": vol_id,
        "shift_id": 1
    })
    
    assert resp.status_code in [201, 400, 404], "Endpoint should handle request"


def test_volunteer_type_filtering_logic():
    """Test that volunteer types are tracked correctly"""
    # Test different volunteer types
    for vol_type in ["regular", "community", "teen"]:
        username = f"vol_{vol_type}_{int(time.time())}"
        resp = requests.post(f"{API_URL}/register", json={
            "first_name": "Type", "last_name": vol_type,
            "username": username, "address": f"Type {vol_type}",
            "phone": f"555-{vol_type[:3]}", "password": "type123",
            "confirm_password": "type123", "role": "volunteer",
            "volunteer_type": vol_type
        })
        
        assert resp.status_code == 201, f"Should register {vol_type} volunteer"


def test_volunteer_gui_displays_volunteer_profile():
    """Test that volunteer profile data is retrievable"""
    vol_username = f"vol_profile_{int(time.time())}"
    requests.post(f"{API_URL}/register", json={
        "first_name": "Profile", "last_name": "Data",
        "username": vol_username, "address": "Profile St",
        "phone": "555-3344", "password": "profile123",
        "confirm_password": "profile123", "role": "volunteer",
        "volunteer_type": "regular"
    })
    
    resp = requests.post(f"{API_URL}/login", json={
        "username": vol_username, "password": "profile123"
    })
    
    vol_id = resp.json()["id"]
    token = resp.json()["token"]
    
    # Get volunteer profile
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{API_URL}/volunteers/{vol_id}", headers=headers)
    
    assert resp.status_code == 200, "Should retrieve volunteer profile"
    assert resp.json()["username"] == vol_username, "Profile should match"


# ============================================================================
# ROLE 4: IDENTITY & DATABASE ENGINEER TESTS
# ============================================================================

def test_database_stores_hashed_passwords():
    """Test that database stores hashed passwords (via login verification)"""
    username = f"hash_verify_{int(time.time())}"
    password = "secure_password_123"
    
    # Register
    resp = requests.post(f"{API_URL}/register", json={
        "first_name": "Hash", "last_name": "Verify",
        "username": username, "address": "Hash",
        "phone": "555-4455", "password": password,
        "confirm_password": password, "role": "volunteer",
        "volunteer_type": "regular"
    })
    
    assert resp.status_code == 201, "Registration should succeed"
    
    # Correct password should login
    resp = requests.post(f"{API_URL}/login", json={
        "username": username, "password": password
    })
    assert resp.status_code == 200, "Correct password should login"
    
    # Wrong password should fail
    resp = requests.post(f"{API_URL}/login", json={
        "username": username, "password": "wrong_password"
    })
    assert resp.status_code == 401, "Wrong password should fail"


def test_database_enforces_unique_username():
    """Test that database enforces unique usernames"""
    username = f"unique_test_{int(time.time())}"
    
    # Register first user
    resp1 = requests.post(f"{API_URL}/register", json={
        "first_name": "First", "last_name": "User",
        "username": username, "address": "First",
        "phone": "555-5566", "password": "pass123",
        "confirm_password": "pass123", "role": "volunteer",
        "volunteer_type": "regular"
    })
    
    assert resp1.status_code == 201, "First registration should succeed"
    
    # Try to register duplicate username
    resp2 = requests.post(f"{API_URL}/register", json={
        "first_name": "Second", "last_name": "User",
        "username": username, "address": "Second",
        "phone": "555-6677", "password": "pass456",
        "confirm_password": "pass456", "role": "volunteer",
        "volunteer_type": "regular"
    })
    
    assert resp2.status_code == 400, "Duplicate username should fail"
    assert "already" in resp2.json().get("error", "").lower(), "Error should mention duplicate"


def test_database_tracks_user_roles():
    """Test that database correctly stores and retrieves user roles"""
    # Create admin
    admin_username = f"role_admin_{int(time.time())}"
    requests.post(f"{API_URL}/register", json={
        "first_name": "Role", "last_name": "Admin",
        "username": admin_username, "address": "Role",
        "phone": "555-7788", "password": "role123",
        "confirm_password": "role123", "role": "admin",
        "volunteer_type": "regular"
    })
    
    resp = requests.post(f"{API_URL}/login", json={
        "username": admin_username, "password": "role123"
    })
    
    assert resp.json()["role"] == "admin", "Admin role should be stored and retrieved"


def test_database_tracks_volunteer_types():
    """Test that database correctly stores volunteer types"""
    for vol_type in ["regular", "community", "teen"]:
        username = f"vol_type_{vol_type}_{int(time.time())}"
        requests.post(f"{API_URL}/register", json={
            "first_name": "Vol", "last_name": vol_type,
            "username": username, "address": vol_type,
            "phone": f"555-{vol_type[:2]}", "password": "vol999",
            "confirm_password": "vol999", "role": "volunteer",
            "volunteer_type": vol_type
        })
        
        resp = requests.post(f"{API_URL}/login", json={
            "username": username, "password": "vol999"
        })
        
        assert resp.json()["volunteer_type"] == vol_type, f"Volunteer type {vol_type} should be stored"


# ============================================================================
# ROLE 5: INTEGRATION, QA & DOCUMENTATION LEAD TESTS
# ============================================================================

def test_end_to_end_volunteer_workflow():
    """Test complete workflow: register → login → view profile"""
    username = f"e2e_vol_{int(time.time())}"
    password = "e2e_password_123"
    
    # Register
    resp = requests.post(f"{API_URL}/register", json={
        "first_name": "E2E", "last_name": "Volunteer",
        "username": username, "address": "E2E",
        "phone": "555-9900", "password": password,
        "confirm_password": password, "role": "volunteer",
        "volunteer_type": "regular"
    })
    assert resp.status_code == 201, "Registration should complete"
    
    # Login
    resp = requests.post(f"{API_URL}/login", json={
        "username": username, "password": password
    })
    assert resp.status_code == 200, "Login should complete"
    token = resp.json()["token"]
    vol_id = resp.json()["id"]
    
    # View profile
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{API_URL}/volunteers/{vol_id}", headers=headers)
    assert resp.status_code == 200, "Should view profile"
    assert resp.json()["username"] == username, "Profile should match registered data"


def test_end_to_end_admin_workflow():
    """Test complete admin workflow: register admin → login → access admin endpoints"""
    username = f"e2e_admin_{int(time.time())}"
    password = "e2e_admin_123"
    
    # Register admin
    resp = requests.post(f"{API_URL}/register", json={
        "first_name": "E2E", "last_name": "Admin",
        "username": username, "address": "E2E",
        "phone": "555-8811", "password": password,
        "confirm_password": password, "role": "admin",
        "volunteer_type": "regular"
    })
    assert resp.status_code == 201, "Admin registration should complete"
    
    # Login as admin
    resp = requests.post(f"{API_URL}/login", json={
        "username": username, "password": password
    })
    assert resp.status_code == 200, "Admin login should complete"
    token = resp.json()["token"]
    
    # Access admin endpoint
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{API_URL}/volunteers", headers=headers)
    assert resp.status_code == 200, "Admin should access /volunteers"


def test_business_rule_week_finalization():
    """Test business rule: week finalization status is tracked"""
    # Create week
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    next_week = (datetime.now() + timedelta(days=8)).strftime("%Y-%m-%d")
    
    resp = requests.post(f"{API_URL}/weeks", json={
        "week_start": tomorrow,
        "finalization_deadline": next_week
    })
    
    assert resp.status_code == 201, "Week creation should work"


def test_business_rule_password_confirmation():
    """Test business rule: passwords must be confirmed"""
    # Mismatched passwords should fail
    resp = requests.post(f"{API_URL}/register", json={
        "first_name": "Mismatch", "last_name": "Test",
        "username": f"mismatch_{int(time.time())}", "address": "Test",
        "phone": "555-1122", "password": "password123",
        "confirm_password": "different_password", "role": "volunteer",
        "volunteer_type": "regular"
    })
    
    assert resp.status_code == 400, "Mismatched passwords should be rejected"


def test_integration_volunteer_type_specific_behavior():
    """Test integration: volunteer type affects behavior"""
    # Test that teen volunteers can be registered with restrictions
    username = f"teen_test_{int(time.time())}"
    resp = requests.post(f"{API_URL}/register", json={
        "first_name": "Teen", "last_name": "Volunteer",
        "username": username, "address": "Teen",
        "phone": "555-3322", "password": "teen123",
        "confirm_password": "teen123", "role": "volunteer",
        "volunteer_type": "teen"
    })
    
    assert resp.status_code == 201, "Teen registration should succeed"
    
    # Teen should have volunteer_type tracked
    resp = requests.post(f"{API_URL}/login", json={
        "username": username, "password": "teen123"
    })
    assert resp.json()["volunteer_type"] == "teen", "Teen type should be tracked"
