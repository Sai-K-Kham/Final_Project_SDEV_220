"""
BACKEND API DEVELOPER - ROLE DOCUMENTATION
===========================================

File Owner: src/api.py (720+ lines), src/scheduler.py (325 lines)
Role Lead: [Developer Name]
Status: ✅ Complete and Tested
"""

# ============================================================================
# ROLE OVERVIEW
# ============================================================================

"""
RESPONSIBILITIES:
- Design and implement Flask REST API with 23+ endpoints
- Implement JWT token authentication and authorization
- Create bcrypt password hashing integration
- Enforce business rules through API layer validation
- Implement role-based access control (RBAC) via decorators
- Design efficient database queries
- Handle errors with proper HTTP status codes
- Implement scheduling logic and business rules

PRIMARY FILES:
- api.py (720+ lines) - Flask REST API server
- scheduler.py (325 lines) - Business logic and scheduling

DELIVERABLES:
1. Flask App Setup - Application initialization
2. Authentication Endpoints - /register, /login
3. JWT Token System - Token generation and validation
4. RBAC Decorators - @require_token, @require_admin_token
5. Shift Management Endpoints - Create, read, update shifts
6. Request Handling Endpoints - Shift and change request processing
7. Business Rules Engine - Validation for constraints
8. Error Handling - Proper HTTP responses
"""

# ============================================================================
# API ENDPOINTS (23+)
# ============================================================================

"""
AUTHENTICATION ENDPOINTS (2):
1. POST /register - Create new user account
   Input: first_name, last_name, username, address, phone, password, confirm_password, role, volunteer_type
   Output: {"success": true}
   Status: 201 Created

2. POST /login - Authenticate and get JWT token
   Input: username, password
   Output: {"token": "xxx.xxx.xxx", "id": 1, "username": "admin", "role": "admin", "volunteer_type": "regular"}
   Status: 200 OK (success) or 401 Unauthorized (failure)

SHIFT MANAGEMENT ENDPOINTS (7):
3. POST /weeks - Create new week
   Admin-only
   Input: week_start, finalization_deadline
   Output: {"success": true, "id": 1}

4. GET /weeks - List all weeks
   Input: None
   Output: [{"id": 1, "week_start": "2026-03-02", "is_finalized": false}, ...]

5. GET /weeks/<id>/shifts - Get shifts for specific week
   Input: week_id
   Output: [{"id": 1, "date": "2026-03-02", "start_time": "09:00", ...}, ...]

6. POST /shifts - Create new shift
   Admin-only
   Input: week_id, site_id, date, start_time, end_time, max_volunteers, role
   Output: {"success": true, "id": 1}

7. DELETE /shifts/<id> - Delete shift
   Admin-only
   Input: shift_id
   Output: {"success": true}

8. GET /sites - List work sites
   Input: None
   Output: [{"id": 1, "site_name": "Main Building"}, ...]

9. POST /weeks/<id>/finalize - Finalize week
   Admin-only
   Input: week_id
   Output: {"success": true}

SHIFT SIGNUP/REQUEST ENDPOINTS (6):
10. POST /shift_requests - Submit shift request
    Input: volunteer_id, shift_id
    Output: {"success": true, "id": 1}

11. GET /signups/pending - Get pending signup requests
    Admin-only
    Output: [{"id": 1, "volunteer_id": 1, "shift_id": 5, "status": "pending"}, ...]

12. POST /signups/<id>/approve - Approve shift request
    Admin-only
    Input: signup_id
    Output: {"success": true}
    Also: Updates weekly_hours, sends notification

13. POST /signups/<id>/deny - Deny shift request
    Admin-only
    Input: signup_id
    Output: {"success": true}

14. POST /change_requests - Submit change request
    Input: volunteer_id, shift_id, reason
    Output: {"success": true, "id": 1}

15. GET /change_requests/pending - Get pending change requests
    Admin-only
    Output: [...]

CHANGE REQUEST ENDPOINTS (3):
16. POST /change_requests/<id>/approve - Approve change request
    Admin-only
    Input: request_id
    Output: {"success": true}

17. POST /change_requests/<id>/deny - Deny change request
    Admin-only
    Input: request_id
    Output: {"success": true}

18. DELETE /change_requests/<id> - Delete change request
    Admin-only
    Input: request_id
    Output: {"success": true}

VOLUNTEER ENDPOINTS (5):
19. GET /volunteers - List all volunteers
    Admin-only
    Output: [{"id": 1, "name": "John Doe", "type": "regular", "hours": 40}, ...]

20. GET /volunteers/<id> - Get volunteer profile
    Output: {"id": 1, "username": "john", "name": "John Doe", "type": "regular", ...}

21. GET /volunteers/<id>/approved_shifts - Get volunteer's approved shifts
    Output: [{"shift_id": 1, "date": "2026-03-02", "start_time": "09:00", ...}, ...]

22. GET /volunteers/<id>/hours - Get volunteer's hours
    Output: {"total_hours": 40, "weekly_breakdown": {...}}

23. POST /volunteers/<id>/availability - Update availability
    Input: availability (calendar data)
    Output: {"success": true}

Total: 23+ fully functional endpoints
"""

# ============================================================================
# AUTHENTICATION & AUTHORIZATION
# ============================================================================

"""
JWT TOKEN SYSTEM:
1. User registers with POST /register
2. User logs in with POST /login (username + password)
3. Password verified using bcrypt.checkpw()
4. If valid, JWT token created: jwt.encode(payload, SECRET, algorithm)
5. Payload includes: user_id, role, volunteer_type, expiration (7 days)
6. Token returned to client in JSON response

TOKEN USAGE:
1. Client stores token in memory
2. For protected endpoints, client sends: Authorization: Bearer {token}
3. API extracts token from header
4. Calls jwt.decode(token, SECRET, algorithm) to verify
5. If valid and not expired, request proceeds
6. If invalid or expired, return 401 Unauthorized

RBAC DECORATORS (2):
@require_token:
- Validates that token is present and valid
- Extracts user_id and role
- Allows endpoint to proceed
- Stores user_id in request context

@require_admin_token:
- Same as @require_token
- Also checks that role == 'admin'
- Returns 403 Forbidden if not admin
- Only allows admins to proceed

EXAMPLE:
@app.route("/volunteers", methods=["GET"])
@require_admin_token
def get_volunteers():
    # Only admin can reach here
    # request.user_id is available
    # request.user_role is "admin"
    ...
"""

# ============================================================================
# BUSINESS RULES ENFORCED BY API
# ============================================================================

"""
1. FINALIZATION DEADLINE:
   - Volunteers can only request shifts 3+ days before week start
   - Checked in POST /shift_requests endpoint
   - Returns 400 if past deadline

2. SHIFT CAPACITY:
   - Maximum volunteers per shift enforced
   - Checked in POST /shift_requests endpoint
   - Returns 400 if shift is full

3. VOLUNTEER TYPE RESTRICTIONS:
   - Teen volunteers cannot work shifts ending after 21:00
   - Checked in POST /shift_requests endpoint
   - Returns 400 if restriction violated

4. TIME CONFLICT DETECTION:
   - Volunteer cannot be assigned overlapping shifts
   - Checked in POST /shift_requests endpoint
   - Returns 400 if conflict exists

5. DUPLICATE PREVENTION:
   - Usernames must be unique
   - Email addresses unique (if used)
   - Enforced in POST /register endpoint
   - Returns 400 if duplicate

6. PASSWORD MATCHING:
   - confirm_password must match password
   - Checked in POST /register endpoint
   - Returns 400 if mismatch

7. STATUS VALIDATION:
   - Request status values: pending, approved, denied
   - Enforced in database constraints
   - API validates status transitions

8. ROLE VALIDATION:
   - Role values: admin, volunteer
   - Volunteer type values: regular, community, teen
   - Enforced in database and API
"""

# ============================================================================
# DATABASE INTEGRATION
# ============================================================================

"""
API interacts with SQLite database through these functions:

1. get_conn() - Create database connection
   - Opens scheduler.db
   - Sets row_factory = sqlite3.Row
   - Returns connection object

2. Parameterized Queries - Prevent SQL injection:
   conn.execute("SELECT * FROM user_profiles WHERE username=?", (username,))
   NOT: f"SELECT * FROM user_profiles WHERE username='{username}'"

3. Transaction Management:
   - conn.execute() for statements
   - conn.commit() to save changes
   - conn.close() to release connection

4. Data Types:
   - INTEGER for IDs
   - TEXT for strings
   - REAL for floats/hours
   - Stored dates as ISO format strings (YYYY-MM-DD)

5. Foreign Keys:
   - All tables with relationships use FOREIGN KEY clauses
   - Database enforces referential integrity
   - API respects relationships when deleting
"""

# ============================================================================
# ERROR HANDLING
# ============================================================================

"""
HTTP STATUS CODES:
- 200 OK - Request succeeded
- 201 Created - Resource created successfully
- 400 Bad Request - Invalid input, validation failed
- 401 Unauthorized - Missing or invalid token
- 403 Forbidden - Token valid but not authorized (not admin)
- 404 Not Found - Resource not found
- 409 Conflict - Constraint violation (duplicate, etc)
- 500 Internal Server Error - Server error

ERROR RESPONSE FORMAT:
{"error": "Error message describing what went wrong"}

EXAMPLES:
400 Bad Request - {"error": "Missing field: username"}
401 Unauthorized - {"error": "token required"}
403 Forbidden - {"error": "admin access required"}
404 Not Found - {"error": "shift not found"}
409 Conflict - {"error": "Username already taken"}

TRY-EXCEPT BLOCKS:
- sqlite3.IntegrityError - Database constraint violated
- jwt.ExpiredSignatureError - Token has expired
- jwt.InvalidTokenError - Token is invalid
- KeyError - Required field missing
- json.JSONDecodeError - Bad JSON in request
"""

# ============================================================================
# SECURITY IMPLEMENTATION
# ============================================================================

"""
PASSWORD SECURITY:
1. User registration: password sent to API
2. API uses bcrypt.hashpw() to hash password
3. Hashed password stored in database
4. Plaintext password discarded

Login:
1. User sends username + password
2. API queries db for user's hashed password
3. Uses bcrypt.checkpw(password_bytes, hashed) to verify
4. If match, generate JWT token
5. If no match, return 401 Unauthorized

JWT TOKEN SECURITY:
1. Token includes payload: {user_id, role, volunteer_type, exp}
2. Payload is SIGNED with SECRET_KEY
3. Anyone can read payload (base64 decoded)
4. Only server can create valid signatures (knows SECRET_KEY)
5. If payload modified, signature becomes invalid
6. Always verify signature before trusting token

HTTPS IN PRODUCTION:
1. All communication encrypted with SSL/TLS
2. Tokens transmitted securely
3. Passwords transmitted securely
4. Cookies/tokens not susceptible to interception

CORS (Cross-Origin Resource Sharing):
1. Configured to allow requests from GUI
2. gui.py accesses api.py on localhost:5000
3. CORS headers allow cross-origin requests
"""

# ============================================================================
# TESTING STRATEGY
# ============================================================================

"""
BACKEND API DEVELOPER TESTS:
1. test_api_register_endpoint_exists
   - Verify POST /register works
   - Check 201 status code

2. test_api_login_endpoint_returns_jwt_token
   - Verify login returns JWT token
   - Check token format (xxx.xxx.xxx)

3. test_api_token_validation_on_protected_routes
   - No token → 401 response
   - Invalid token → 401 response

4. test_api_admin_authorization_enforced
   - Volunteer token on admin endpoint → 403
   - Admin token on admin endpoint → 200

5. test_api_creates_weeks_endpoint
   - POST /weeks should create week
   - Check 201 status and success

6. test_api_lists_sites
   - GET /sites returns list
   - Check 200 status and list format

7. test_api_shift_endpoints_require_proper_data
   - Missing fields → 400 Bad Request
   - Error message provided

8. test_business_rule_password_confirmation
   - Mismatched passwords → 400
   - Error message clear

Related Integration Tests:
- test_end_to_end_volunteer_workflow
- test_end_to_end_admin_workflow
- test_integration_volunteer_type_specific_behavior
"""

# ============================================================================
# PERFORMANCE CONSIDERATIONS
# ============================================================================

"""
QUERY OPTIMIZATION:
- Indexes on frequently queried columns (id, username)
- Foreign keys for efficient joins
- Parameterized queries prevent SQL injection

CACHING:
- Site list could be cached (changes infrequently)
- User profiles could be cached per session
- API returns raw queries (stateless)

RESPONSE TIMES:
- Most queries return in <100ms
- Batch operations could be added for bulk approvals
- Pagination could be added for large lists

SCALABILITY:
- Single-server API suitable for organization size
- SQLite adequate for 1000s of users
- Could migrate to PostgreSQL for larger scale

LOAD TESTING:
- Current implementation handles test load
- No special performance tuning needed yet
- Could add query logging for monitoring
"""

# ============================================================================
# SUCCESS CRITERIA
# ============================================================================

"""
✅ COMPLETED:
- All 23+ endpoints implemented
- JWT authentication working
- Bcrypt password hashing integrated
- RBAC decorators protecting endpoints
- Business rules enforced
- Error handling comprehensive
- Database integration complete
- All tests passing

METRICS:
- Lines of Code: 720+ (api.py) + 325 (scheduler.py)
- Endpoints: 23+
- Decorators: 2 (@require_token, @require_admin_token)
- Business Rules: 8 enforced
- HTTP Status Codes: 8 used
- Tests Passing: 8+ (API-specific)
- Error Scenarios: 10+
"""

# ============================================================================
# DEPLOYMENT & RUNNING THE API
# ============================================================================

"""
TO RUN API:
1. cd src/
2. python api.py
3. Server starts on http://127.0.0.1:5000
4. Press Ctrl+C to stop

ENDPOINTS AVAILABLE:
- POST http://127.0.0.1:5000/register
- POST http://127.0.0.1:5000/login
- GET http://127.0.0.1:5000/shifts
- POST http://127.0.0.1:5000/shifts
- ... (see full list above)

TESTING WITH CURL:
curl -X POST http://127.0.0.1:5000/login \\
  -H "Content-Type: application/json" \\
  -d '{"username": "admin", "password": "admin"}'

curl -X GET http://127.0.0.1:5000/volunteers \\
  -H "Authorization: Bearer {token}"

PRODUCTION DEPLOYMENT:
1. Use WSGI server (Gunicorn, uWSGI, IIS)
2. Use HTTPS (SSL/TLS certificates)
3. Set JWT_SECRET to strong random value
4. Use PostgreSQL instead of SQLite
5. Add request logging and monitoring
6. Rate limit API calls
7. Add request validation/sanitization
"""

# ============================================================================
# DOCUMENTATION REFERENCES
# ============================================================================

"""
Related Files:
- src/api.py - Implementation
- src/scheduler.py - Business logic
- docs/Architecture_Overview.docx - System design
- ROLE_DOCUMENTATION.md - Role overview
- test_gui.py - Test suite

Admin GUI Documentation:
- See admin_gui_role.md for endpoint usage
- See admin_gui.py for request/response handling

Volunteer GUI Documentation:
- See volunteer_gui_role.md for endpoint usage
- See volunteer_gui.py for request handling

Database Schema:
- See database.py for table structure
- See Identity & Database Engineer documentation
"""
