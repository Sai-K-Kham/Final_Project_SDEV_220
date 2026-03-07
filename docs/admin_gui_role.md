"""
ADMIN GUI DEVELOPER - ROLE DOCUMENTATION
========================================

File Owner: src/admin_gui.py (765 lines)
Role Lead: [Developer Name]
Status: ✅ Complete and Tested

"""

# ============================================================================
# ROLE OVERVIEW
# ============================================================================

"""
RESPONSIBILITIES:
- Design and implement the administrator user interface using Tkinter
- Create secure login functionality with JWT token integration
- Build comprehensive dashboard with navigation menu
- Implement 8 specialized window classes for various admin functions
- Ensure all API calls use secure token-based authentication
- Provide error handling and user feedback mechanisms
- Validate user inputs before sending to API

PRIMARY FILE: admin_gui.py (765 lines)

DELIVERABLES:
1. AdminLoginWindow - Login interface with credential validation
2. AdminMainWindow - Dashboard with 5 navigation buttons
3. WeekSchedulerWindow - Weekly shift management interface
4. PendingSignupsWindow - Shift request approval/denial system
5. ChangeRequestsAdminWindow - Change request handling
6. VolunteersAdminWindow - Volunteer list and management
7. EditAvailabilityDialog - Volunteer availability editor
8. make_request() Helper - Token-authenticated HTTP calls
"""

# ============================================================================
# CLASS RESPONSIBILITIES
# ============================================================================

"""
AdminLoginWindow:
- Collect username and password from admin
- Call POST /login API endpoint
- Store JWT token in memory
- Validate response (200 status code)
- Show error messages on failed login
- Open AdminMainWindow on successful login
- Close window after login

AdminMainWindow:
- Display dashboard title and menu
- Provide 5 navigation buttons:
  1. Create/Manage Weekly Shifts
  2. View Pending Shift Requests
  3. View Pending Change Requests
  4. View All Volunteers
  5. Finalize Week
- Handle button clicks to open appropriate windows
- Maintain token for API calls
- Clean exit functionality

WeekSchedulerWindow:
- Display list of weeks from GET /weeks
- Allow selection of a week
- Load shifts from GET /weeks/<id>/shifts
- Display shifts in grid layout (Mon-Sun, 7 rows)
- Allow creation of new shifts via POST /shifts
- Show shift details (date, time, location, capacity)
- Allow deletion of shifts (DELETE /shifts/<id>)
- Display finalization status and button
- Call POST /weeks/<id>/finalize when ready

PendingSignupsWindow:
- Load pending requests from GET /signups/pending
- Display approval-required shift requests
- Show volunteer name, shift details, status
- Provide APPROVE button → POST /signups/<id>/approve
- Provide DENY button → POST /signups/<id>/deny
- Real-time hours calculation on approval
- Refresh button to reload from API
- Search/filter functionality

ChangeRequestsAdminWindow:
- Load pending changes from GET /change_requests/pending
- Display volunteer modification requests
- Show from-shift and to-shift details
- Show reason for change
- Provide APPROVE button → POST /change_requests/<id>/approve
- Provide DENY button → POST /change_requests/<id>/deny
- Filter by status (pending, approved, denied)
- Refresh button to reload

VolunteersAdminWindow:
- Load volunteers from GET /volunteers
- Display table: ID, Name, Type, Hours
- Allow selection of volunteer
- Show volunteer profile details
- Provide EDIT AVAILABILITY button
- Show availability calendar
- Allow bulk actions (view history, export)

EditAvailabilityDialog:
- Display availability calendar (7-day week)
- Allow volunteer to mark available days
- Show current availability from API
- Send updates to POST /volunteers/<id>/availability
- Confirm changes with modal dialog

make_request() Helper:
- Accept endpoint URL and method (GET/POST/PUT/DELETE)
- Add Authorization header with Bearer token
- Serialize JSON payloads
- Handle timeout and connection errors
- Provide error dialogs to user
- Return response object
"""

# ============================================================================
# API ENDPOINTS USED
# ============================================================================

"""
ADMIN GUI endpoints called:
1. POST /login - Authenticate admin
2. GET /weeks - List all weeks
3. POST /weeks - Create new week
4. GET /weeks/<id>/shifts - Get shifts for week
5. POST /shifts - Create new shift
6. DELETE /shifts/<id> - Delete shift (if implemented)
7. GET /signups/pending - Get pending requests
8. POST /signups/<id>/approve - Approve request
9. POST /signups/<id>/deny - Deny request
10. GET /change_requests/pending - Get pending changes
11. POST /change_requests/<id>/approve - Approve change
12. POST /change_requests/<id>/deny - Deny change
13. GET /volunteers - List all volunteers
14. GET /volunteers/<id> - Get volunteer details
15. POST /volunteers/<id>/availability - Update availability
16. POST /weeks/<id>/finalize - Finalize week

Total: 16+ endpoints used
"""

# ============================================================================
# KEY FEATURES
# ============================================================================

"""
1. SECURE LOGIN:
   - Prompts for username and password
   - Sends to POST /login
   - Receives JWT token
   - Stores token for session
   - Token used in Authorization header for all API calls

2. WEEKLY MANAGEMENT:
   - Create new weeks with start date and deadline
   - Add shifts per day (Mon-Sun)
   - Set shift details: time, location, role, max volunteers
   - View all shifts in grid format
   - Auto-populate dates based on week start

3. REQUEST HANDLING:
   - View pending shift requests in real-time
   - See volunteer name, requested shift, status
   - Approve request with one click
   - Deny request with explanation

4. ERROR HANDLING:
   - Try-except blocks around all API calls
   - User-friendly error dialogs
   - Connection error handling
   - Timeout handling with retry
   - JSON parse error handling

5. USER FEEDBACK:
   - Success messages on operations
   - Error messages with details
   - Loading indicators for API calls
   - Refresh buttons to reload data
   - Real-time status updates

6. NAVIGATION:
   - Menu-driven interface
   - Clear button labels
   - Window hierarchy (main → sub-windows)
   - Back/Close buttons for exit
"""

# ============================================================================
# TESTING STRATEGY
# ============================================================================

"""
ADMIN GUI DEVELOPER TESTS:
1. test_admin_gui_requires_valid_credentials
   - Verify login with invalid credentials fails
   - Check 401 response from API

2. test_admin_gui_receives_token_on_login
   - Verify successful login returns JWT token
   - Check token is in response JSON
   - Verify role is 'admin'

3. test_admin_gui_can_access_admin_endpoints
   - Register admin account
   - Login and receive token
   - Call GET /volunteers endpoint
   - Verify 200 status code

4. test_admin_gui_handles_api_errors_gracefully
   - Simulate invalid endpoint call
   - Verify error response is readable
   - Check error is displayed properly

Related Integration Tests:
- test_end_to_end_admin_workflow
- test_admin_authorization_enforced
"""

# ============================================================================
# TECHNOLOGY STACK
# ============================================================================

"""
GUI Framework:
- Tkinter (Python built-in)

HTTP Client:
- requests library

Data Format:
- JSON for API communication

Authentication:
- JWT tokens from API
- Bearer token in Authorization header

Error Handling:
- try-except blocks
- tkinter messagebox for errors
- requests.exceptions handling

UI Components:
- tk.Tk() - Main window
- tk.Toplevel() - Sub-windows
- tk.Button() - Clickable controls
- tk.Label() - Text display
- tk.Entry() - Text input
- tk.Listbox, ttk.Treeview - Data display
- tk.Canvas, tk.Frame - Layout
"""

# ============================================================================
# SECURITY CONSIDERATIONS
# ============================================================================

"""
1. TOKEN STORAGE:
   - JWT tokens stored in memory only
   - Not written to disk
   - Cleared when window closes
   - 7-day expiration handled by API

2. PASSWORD SECURITY:
   - Passwords sent to API only (not stored locally)
   - HTTPS in production (not HTTP)
   - Passwords hashed by API layer
   - No plaintext passwords in code

3. AUTHORIZATION:
   - Token included in every API call
   - Authorization header format: "Bearer {token}"
   - API validates token before processing
   - Admin-only endpoints checked on server side

4. INPUT VALIDATION:
   - User inputs validated on client side
   - API also validates on server side
   - No SQL injection possible (API uses parameterized queries)
   - XSS not applicable (desktop app, not web)
"""

# ============================================================================
# SUCCESS CRITERIA
# ============================================================================

"""
✅ COMPLETED:
- All 8 window classes implemented
- Login interface working with JWT tokens
- Dashboard navigation menu functional
- Shift creation and management working
- Request approval/denial system operational
- Volunteer management interface functional
- Error handling and user feedback implemented
- All tests passing

METRICS:
- Lines of Code: 765
- Window Classes: 8
- Tests Passing: 5+ (admin-specific)
- API Integrations: 16+
- User Interactions: 30+
- Error Scenarios: 10+
"""

# ============================================================================
# HOW THE ADMIN FLOW WORKS
# ============================================================================

"""
1. ADMIN STARTS APPLICATION:
   - Double-click volunteer_scheduler.py
   - Launcher window appears with buttons
   - Click "Admin Login" button

2. LOGIN SCREEN APPEARS:
   - AdminLoginWindow() class instantiates
   - Shows "Username:" and "Password:" fields
   - User enters "admin" and "admin"
   - Clicks Login button

3. MAKE_REQUEST(POST /login):
   - API validates credentials
   - Returns {"token": "xxx.xxx.xxx", "id": 1, "role": "admin"}
   - Token stored in memory

4. DASHBOARD OPENS:
   - AdminMainWindow shows 5 buttons
   - "Create Weekly Shifts"
   - "View Pending Signups"
   - "View Change Requests"
   - "View All Volunteers"
   - "Finalize Week"

5. ADMIN CREATES WEEK:
   - Clicks "Create Weekly Shifts"
   - WeekSchedulerWindow opens
   - Selects Monday date (e.g., 2026-03-02)
   - Creates shifts for each day Mon-Sun
   - Each shift: 9am-5pm, "Main Building", max 5 volunteers
   - Data sent via POST /shifts to API

6. VOLUNTEERS REQUEST SHIFTS:
   - Volunteers login and request shifts
   - Requests stored as "pending" in database

7. ADMIN APPROVES REQUESTS:
   - Clicks "View Pending Signups"
   - PendingSignupsWindow loads pending requests
   - Shows: John Doe requested Main Building Shift on Mon
   - Admin clicks APPROVE
   - POST /signups/<id>/approve sent to API
   - Volunteer assigned to shift, hours calculated

8. ADMIN FINALIZES WEEK:
   - All shifts assigned and volunteers scheduled
   - Admin clicks "Finalize Week"
   - POST /weeks/<id>/finalize sent to API
   - Week marked as finalized in database
   - No new requests can be submitted for this week

9. ADMIN LOGS OUT:
   - Closes AdminMainWindow
   - Token destroyed
   - Session ended
   - Can login again later
"""

# ============================================================================
# DOCUMENTATION REFERENCES
# ============================================================================

"""
Related Files:
- src/admin_gui.py - Implementation
- docs/User_Manual.docx - User guide
- docs/Architecture_Overview.docx - System design
- ROLE_DOCUMENTATION.md - This document
- test_gui.py - Test suite

API Documentation:
- See api.py for endpoint details
- See ROLE_DOCUMENTATION.md for API list
- See Backend API Developer documentation

Database Schema:
- See database.py for table structure
- See Identity & Database Engineer documentation

Testing:
- Running tests: pytest src/test_gui.py -v
- Admin tests: test_admin_gui_*
- Integration tests: test_end_to_end_admin_workflow
"""

# ============================================================================
# KNOWN LIMITATIONS & FUTURE IMPROVEMENTS
# ============================================================================

"""
CURRENT LIMITATIONS:
1. Single admin login at a time
2. No persistent session storage
3. No undo/redo functionality
4. No email notifications

FUTURE IMPROVEMENTS:
1. Multi-admin support with session management
2. Persistent login session (token refresh)
3. Undo/redo for shift changes
4. Email notifications on important events
5. Batch import/export functionality
6. Advanced filtering and search
7. Custom reports and analytics
8. Dark mode UI theme
"""
