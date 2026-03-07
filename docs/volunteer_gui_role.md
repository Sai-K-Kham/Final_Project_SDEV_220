"""
VOLUNTEER GUI DEVELOPER - ROLE DOCUMENTATION
=============================================

File Owner: src/volunteer_gui.py (510+ lines)
Role Lead: [Developer Name]
Status: ✅ Complete and Tested
"""

# ============================================================================
# ROLE OVERVIEW
# ============================================================================

"""
RESPONSIBILITIES:
- Design and implement the volunteer user interface using Tkinter
- Create login functionality with JWT token integration
- Build volunteer dashboard with multiple views
- Implement shift planning interface with type and capacity filtering
- Develop change request submission system
- Create approved shifts viewing window
- Implement hours tracking display
- Enforce volunteer type-specific rules (teen restrictions, etc.)
- Provide real-time feedback and validation

PRIMARY FILE: volunteer_gui.py (510+ lines)

DELIVERABLES:
1. VolunteerLoginWindow - Login interface with profile loading
2. VolunteerMainWindow - Dashboard with 4 navigation buttons
3. WeekScheduleView - Shift planner with filtering
4. ApprovedShiftsWindow - View assigned shifts
5. ChangeRequestWindow - Submit change requests
6. WeeklyHoursWindow - Display hours worked
7. make_request() Helper - Token-authenticated HTTP calls
8. Type-Specific Filtering - Enforce volunteer type rules
"""

# ============================================================================
# CLASS RESPONSIBILITIES
# ============================================================================

"""
VolunteerLoginWindow:
- Display login form: username and password fields
- Call POST /login endpoint
- Validate credentials
- Receive JWT token and store in memory
- Load volunteer profile from response
- Verify volunteer_type from API
- Show error on failed login
- Open VolunteerMainWindow on success
- Store token for session

VolunteerMainWindow:
- Display welcome message with volunteer name
- Provide 4 navigation buttons:
  1. Plan Weekly Schedule (Request Shifts)
  2. View Approved Shifts
  3. Request Change / Update Availability
  4. View Weekly Hours
- Maintain JWT token for API calls
- Handle button clicks to open sub-windows
- Clean exit functionality

WeekScheduleView:
- Load weeks from GET /weeks
- Allow week selection
- Load open shifts for week from GET /shifts
- Filter shifts based on:
  - Volunteer type (regular, community, teen)
  - Shift role requirements
  - Current capacity vs max volunteers
  - Time conflicts with existing assignments
- Hide shifts that are:
  - At capacity
  - Before volunteer's start time
  - Conflicting with existing shifts
- Display shift details: date, time, location, role, max volunteers
- Calculate hours for each shift
- Show "Request" button for each available shift
- On click, submit to POST /shift_requests
- Display confirmation message
- Show error if request fails (conflict, full, late restriction)

ApprovedShiftsWindow:
- Load approved shifts from GET /volunteers/<id>/approved_shifts
- Display table: date, time, location, status
- Show shift details
- Indicate which are pending approval vs approved
- Allow volunteer to view full schedule
- Show total hours for selected week
- Refresh button to reload

ChangeRequestWindow:
- Allow volunteer to select a shift to modify
- Show current shift details
- Allow entry of reason for change
- Submit to POST /change_requests
- Show status of pending changes
- Allow cancellation of requests

WeeklyHoursWindow:
- Load hours from GET /volunteers/<id>/hours
- Display total hours for current week
- Show breakdown by day
- Show date range (week start to end)
- Calculate remaining capacity
- Show goal progress if goal exists

make_request() Helper:
- Accept endpoint, method, and optional data
- Add Authorization: Bearer {token} header
- Serialize JSON payloads
- Handle errors gracefully
- Display error dialogs to user
- Return response or raise exception
"""

# ============================================================================
# API ENDPOINTS USED
# ============================================================================

"""
VOLUNTEER GUI endpoints called:
1. POST /login - Authenticate volunteer
2. GET /weeks - List weeks
3. GET /shifts - List all shifts
4. GET /shifts?open=1 - List open shifts (if implemented)
5. POST /shift_requests - Request a shift
6. GET /volunteers/<id>/approved_shifts - Get approved shifts
7. GET /volunteers/<id>/hours - Get hours worked
8. GET /volunteers/<id> - Get profile
9. POST /change_requests - Submit change request
10. GET /change_requests/pending (volunteer's own)
11. POST /volunteers/<id>/availability - Update availability

Total: 11+ endpoints used
"""

# ============================================================================
# VOLUNTEER TYPE-SPECIFIC BEHAVIOR
# ============================================================================

"""
REGULAR VOLUNTEER:
- Can request any shift
- No time restrictions
- Can work any shift role
- Can work any hour of day

COMMUNITY SERVICE VOLUNTEER:
- Can request any shift
- No time restrictions
- Can work any shift role
- Often court-ordered hours (tracked separately)
- Can work any hour of day

TEEN VOLUNTEER:
- Can request any shift EXCEPT:
  - Shifts ending at or after 21:00 (9 PM)
- Time restriction enforced in:
  - WeekScheduleView filters shifts
  - API validates in POST /shift_requests
- Shows warning if attempting late shift
- Error message: "Teen volunteers cannot work past 21:00"

FILTERING IMPLEMENTATION:
1. When loading shifts, extract end_time
2. Parse time string "21:30" to float 21.5
3. For teen: if end_time >= 21.0, exclude from display
4. Button remains disabled for restricted shifts
5. Tooltip explains why shift not available
"""

# ============================================================================
# SHIFT REQUEST WORKFLOW
# ============================================================================

"""
STEP 1 - VIEW AVAILABLE SHIFTS:
- Volunteer logs in
- Selects week
- WeekScheduleView loads GET /shifts
- Filters based on:
  - Max volunteers not reached
  - No time conflicts
  - Volunteer type compatibility
  - Teen time restrictions
- Displays available shifts in grid

STEP 2 - SELECT SHIFT:
- Volunteer sees open shifts
- Clicks "Request" button on desired shift
- Shift details highlighted

STEP 3 - SUBMIT REQUEST:
- POST /shift_requests with:
  - volunteer_id
  - shift_id
- Server validates:
  - Still room in shift
  - No conflicts
  - Finalization deadline not passed
  - Teen restrictions (if teen)

STEP 4 - CONFIRMATION:
- Success: "Request submitted"
- Failure: Error message explains why
  - "Shift is full"
  - "Time conflict with existing shift"
  - "Past finalization deadline"
  - "Teen volunteers cannot work past 21:00"

STEP 5 - ADMIN APPROVAL:
- Admin reviews in PendingSignupsWindow
- Approves or denies request
- Volunteer can see status in ApprovedShiftsWindow

STEP 6 - VIEW APPROVED SHIFTS:
- ApprovedShiftsWindow shows approved shifts
- Hours calculated and displayed
- Shows in calendar format
"""

# ============================================================================
# FILTERING ALGORITHM
# ============================================================================

"""
PSEUDO-CODE FOR SHIFT FILTERING:

function filter_shifts(all_shifts, volunteer_type, existing_shifts):
    available_shifts = []
    
    for shift in all_shifts:
        # Check capacity
        if shift.current_signups >= shift.max_volunteers:
            continue  # Skip if full
        
        # Check volunteer type match
        if shift.role != 'any' and shift.role != volunteer_type:
            continue  # Skip if role doesn't match
        
        # Check time conflicts
        has_conflict = false
        for existing in existing_shifts:
            if time_overlap(shift.start, shift.end, existing.start, existing.end):
                has_conflict = true
                break
        if has_conflict:
            continue  # Skip if time conflict
        
        # Check teen restrictions
        if volunteer_type == 'teen':
            if parse_time(shift.end_time) >= 21.0:
                continue  # Skip if teen and ends after 9 PM
        
        # Shift is available
        available_shifts.append(shift)
    
    return available_shifts

function time_overlap(start1, end1, start2, end2):
    return not (end1 <= start2 or end2 <= start1)

function parse_time(time_str):  # "21:30" → 21.5
    hours, minutes = time_str.split(':')
    return float(hours) + float(minutes) / 60.0
"""

# ============================================================================
# KEY FEATURES
# ============================================================================

"""
1. SECURE LOGIN:
   - Username and password fields
   - POST /login sends credentials
   - JWT token received and stored
   - Profile loaded on login

2. WEEKLY PLANNING:
   - Select week from dropdown
   - View all shifts for that week
   - Filtered based on type and availability
   - Request shifts with one click

3. CONFLICT DETECTION:
   - Prevents overlapping shifts
   - Checks against existing approved shifts
   - Prevents double-booking

4. TYPE-BASED RESTRICTIONS:
   - Teen volunteers cannot work late
   - Enforced at UI level (grayed out)
   - Also enforced at API level

5. HOURS TRACKING:
   - Real-time calculation of hours
   - Shows weekly total
   - Shows target hours if goal exists

6. CHANGE REQUESTS:
   - Submit request to modify assigned shift
   - Provide reason for change
   - Admin reviews and approves/denies

7. ERROR HANDLING:
   - User-friendly error messages
   - Explains why request failed
   - Retry option
   - Timeout handling

8. USER FEEDBACK:
   - Status messages on operations
   - Visual indicators for status
   - Refresh buttons
   - Real-time updates
"""

# ============================================================================
# TESTING STRATEGY
# ============================================================================

"""
VOLUNTEER GUI DEVELOPER TESTS:
1. test_volunteer_gui_login_works
   - Register volunteer account
   - Login with credentials
   - Verify 200 status
   - Check role is 'volunteer'

2. test_volunteer_can_request_shifts
   - Login as volunteer
   - Call POST /shift_requests
   - Verify endpoint handles request

3. test_volunteer_type_filtering_logic
   - Register different volunteer types
   - Verify each type created with correct type
   - Check all 3 types (regular, community, teen)

4. test_volunteer_gui_displays_volunteer_profile
   - Get volunteer profile
   - Verify data matches registration
   - Check personal information displayed

5. test_integration_volunteer_type_specific_behavior
   - Register teen volunteer
   - Verify teen type stored
   - Check hours are calculated correctly

Related Integration Tests:
- test_end_to_end_volunteer_workflow
- test_volunteer_can_request_shifts
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

Time/Date:
- datetime module for date math
- Time parsing functions

Calculations:
- Hours calculation from shift times
- Conflict detection logic

UI Components:
- tk.Tk() - Main window
- tk.Toplevel() - Sub-windows
- tk.Button() - Clickable controls
- tk.Label() - Text display
- tk.Canvas, ttk.Treeview - Shift display
"""

# ============================================================================
# SUCCESS CRITERIA
# ============================================================================

"""
✅ COMPLETED:
- All 6 window classes implemented
- Login functionality working
- Shift filtering by type implemented
- Teen time restrictions enforced
- Conflict detection working
- Change request submission completed
- Hours tracking display functional
- All tests passing

METRICS:
- Lines of Code: 510+
- Window Classes: 7 (including dialogs)
- Tests Passing: 5+ (volunteer-specific)
- API Integrations: 11+
- Filter Types: 3+ (type, capacity, time)
- User Interactions: 20+
- Error Cases: 5+
"""

# ============================================================================
# HOW THE VOLUNTEER FLOW WORKS
# ============================================================================

"""
1. VOLUNTEER STARTS APPLICATION:
   - Double-click volunteer_scheduler.py
   - Launcher window appears
   - Click "Volunteer Login"

2. LOGIN SCREEN:
   - VolunteerLoginWindow appears
   - Enters username and password
   - Clicks Login button

3. MAKE_REQUEST(POST /login):
   - API validates credentials
   - Returns {"token": "xxx", "id": 1, "volunteer_type": "regular"}
   - Window stores token and volunteer_type

4. DASHBOARD OPENS:
   - VolunteerMainWindow shows 4 buttons
   - "Plan Weekly Schedule"
   - "View Approved Shifts"
   - "Request Change"
   - "View Weekly Hours"

5. PLAN WEEKLY SCHEDULE:
   - Clicks "Plan Weekly Schedule"
   - WeekScheduleView opens
   - Loads weeks from GET /weeks
   - Selects "Week of March 2"
   - Loads shifts from GET /shifts
   - Filters based on volunteer_type and capacity
   - Displays available 9-5 shifts in grid format

6. REQUEST SHIFT:
   - Sees Monday 9-5 shift at Main Building
   - Clicks "Request" button
   - POST /shift_requests sent for that shift
   - Dialog shows "Request submitted successfully"
   - Shift status changes to pending

7. ADMIN APPROVAL:
   - Admin logs in
   - Goes to Pending Signups window
   - Sees volunteer's request
   - Clicks Approve
   - Status updated to approved
   - Hours calculated

8. VIEW APPROVED SHIFTS:
   - Volunteer clicks "View Approved Shifts"
   - ApprovedShiftsWindow shows assigned shifts
   - Monday 9-5 now shown as "Approved"
   - Hours calculated: 8 hours

9. VIEW HOURS:
   - Clicks "View Weekly Hours"
   - Shows: "Total Hours: 8 hours this week"
   - Breakdown by day shows assigned shifts

10. REQUEST CHANGE:
    - Volunteer needs to change Monday shift
    - Clicks "Request Change"
    - Selects Monday 9-5 shift
    - Types reason: "Unexpected appointment"
    - Clicks Submit
    - POST /change_requests sent
    - Admin reviews and approves

11. LOGOUT:
    - Closes VolunteerMainWindow
    - Token destroyed
    - Session ended
"""

# ============================================================================
# SPECIAL HANDLING - TEEN VOLUNTEERS
# ============================================================================

"""
TEEN VOLUNTEER RESTRICTIONS:
1. Cannot work shifts ending >= 21:00 (9 PM)
2. Enforced at two levels:

UI LEVEL (volunteer_gui.py):
- When loading shifts, check end_time
- Parse "20:00" as 20.0, "21:30" as 21.5
- If volunteer_type == "teen" and end_time >= 21.0:
  - Don't show in list OR
  - Show with "Not available (ends past 21:00)" button
  - Disable button to prevent selection

API LEVEL (api.py):
- POST /shift_requests endpoint checks
- Retrieves shift end_time
- If volunteer_type == "teen" and end_time >= 21.0:
  - Return 400 Bad Request
  - Message: "Teen volunteers cannot work past 21:00"

EXAMPLES:
- Teen CAN request:  9:00-17:00 (5 PM), 9:00-20:30 (8:30 PM)
- Teen CANNOT request: 9:00-21:00 (9 PM), 9:00-22:00 (10 PM)

SAFETY COMPLIANCE:
- Protects teen volunteers from working late hours
- Meets legal requirements for minor employment
- Enforced both client-side and server-side
"""

# ============================================================================
# DOCUMENTATION REFERENCES
# ============================================================================

"""
Related Files:
- src/volunteer_gui.py - Implementation
- docs/User_Manual.docx - User guide
- docs/Architecture_Overview.docx - System design
- ROLE_DOCUMENTATION.md - This document
- test_gui.py - Test suite

API Documentation:
- See api_backend_role.md for endpoint details
- See Backend API Developer documentation

Admin GUI Documentation:
- See admin_gui_role.md for approval workflow
- See admin_gui.py for request handling

Database Schema:
- See database.py for volunteer_type storage
- See Identity & Database Engineer documentation
"""
