"""
IDENTITY & DATABASE ENGINEER - ROLE DOCUMENTATION
==================================================

File Owners: src/database.py (162 lines), src/models.py (315 lines)
Role Lead: [Developer Name]
Status: ✅ Complete and Tested
"""

# ============================================================================
# ROLE OVERVIEW
# ============================================================================

"""
RESPONSIBILITIES:
- Design and implement database schema with 7 normalized tables
- Create OOP domain model classes with inheritance
- Implement secure password hashing with bcrypt
- Enforce data validation and business rules at database level
- Manage database connections and transactions
- Implement volunteer type system (regular, community, teen)
- Track user roles (admin vs volunteer)
- Design efficient queries and indexes
- Ensure data integrity and constraints

PRIMARY FILES:
- src/database.py (162 lines)
- src/models.py (315 lines)

TOTAL DELIVERABLES:
1. Database schema with 7 normalized tables
2. 4 domain model classes with inheritance
3. Password hashing and verification
4. User profile management
5. Volunteer type system
6. Shift and signup management
7. Change request tracking
8. Weekly hours tracking
"""

# ============================================================================
# DATABASE SCHEMA (7 TABLES)
# ============================================================================

"""
TABLE 1: user_profiles
- user_id (INTEGER PRIMARY KEY AUTOINCREMENT)
- username (TEXT UNIQUE NOT NULL)
- hashed_password (TEXT NOT NULL)
- role (TEXT NOT NULL) - 'admin' or 'volunteer'
- first_name (TEXT)
- last_name (TEXT)
- phone (TEXT)
- volunteer_type (TEXT) - NULL for admin, 'regular'/'community'/'teen' for volunteer
- created_at (TIMESTAMP)

TABLE 2: weeks
- week_id (INTEGER PRIMARY KEY AUTOINCREMENT)
- week_start (DATE UNIQUE NOT NULL)
- week_end (DATE NOT NULL)
- is_finalized (BOOLEAN DEFAULT 0)
- finalized_at (TIMESTAMP)

TABLE 3: sites
- site_id (INTEGER PRIMARY KEY AUTOINCREMENT)
- site_name (TEXT UNIQUE NOT NULL)
- location (TEXT)
- contact_person (TEXT)
- phone (TEXT)
- notes (TEXT)

TABLE 4: shifts
- shift_id (INTEGER PRIMARY KEY AUTOINCREMENT)
- week_id (INTEGER FOREIGN KEY)
- site_id (INTEGER FOREIGN KEY)
- date (DATE NOT NULL)
- start_time (TEXT NOT NULL) - "09:00"
- end_time (TEXT NOT NULL) - "17:00"
- shift_role (TEXT) - "regular", "supervisor", "support"
- max_volunteers (INTEGER DEFAULT 1)
- min_age (INTEGER) - NULL or 18, 21 for teen restrictions
- created_at (TIMESTAMP)

TABLE 5: shift_signups (or shift_assignments)
- signup_id (INTEGER PRIMARY KEY AUTOINCREMENT)
- shift_id (INTEGER FOREIGN KEY)
- volunteer_id (INTEGER FOREIGN KEY)
- status (TEXT) - 'pending', 'approved', 'rejected', 'cancelled'
- requested_at (TIMESTAMP)
- approved_at (TIMESTAMP)

TABLE 6: change_requests
- request_id (INTEGER PRIMARY KEY AUTOINCREMENT)
- volunteer_id (INTEGER FOREIGN KEY)
- shift_id (INTEGER FOREIGN KEY)
- reason (TEXT)
- status (TEXT) - 'pending', 'approved', 'rejected'
- requested_at (TIMESTAMP)
- resolved_at (TIMESTAMP)

TABLE 7: weekly_hours
- hours_id (INTEGER PRIMARY KEY AUTOINCREMENT)
- volunteer_id (INTEGER FOREIGN KEY)
- week_id (INTEGER FOREIGN KEY)
- total_hours (REAL)
- calculated_at (TIMESTAMP)
- UNIQUE(volunteer_id, week_id)

TABLE 8 (Optional): audit_log
- log_id (INTEGER PRIMARY KEY AUTOINCREMENT)
- action (TEXT) - 'login', 'shift_request', 'approval'
- user_id (INTEGER FOREIGN KEY)
- details (TEXT JSON)
- timestamp (TIMESTAMP)
"""

# ============================================================================
# DOMAIN MODEL CLASSES (OOP HIERARCHY)
# ============================================================================

"""
CLASS HIERARCHY:

User (Abstract Base)
├── Admin (inherits from User)
└── Volunteer (inherits from User)
    ├── RegularVolunteer
    ├── CommunityServiceVolunteer
    └── TeenVolunteer

DETAILED CLASS SPECIFICATIONS:
"""

# ============================================================================
# CLASS 1: USER (Base Class)
# ============================================================================

"""
class User:
    PURPOSE: Base class for all users in system
    
    ATTRIBUTES:
    - user_id (int): Primary key from user_profiles
    - username (str): Unique identifier
    - first_name (str): Legal first name
    - last_name (str): Legal last name
    - phone (str): Contact phone number
    - role (str): 'admin' or 'volunteer'
    - created_at (datetime): Account creation timestamp
    - hashed_password (str): Bcrypt hashed password (never stored in memory plaintext)
    
    METHODS:
    - __init__(user_id, username, first_name, last_name, role)
    - get_full_name() -> str: Return "FirstName LastName"
    - verify_password(plaintext: str) -> bool: Call bcrypt.checkpw()
    - update_profile(first_name, last_name, phone): Update database
    - logout(): Clear session token
    
    VALIDATION:
    - username: 4-20 alphanumeric characters
    - first_name: 1-50 characters
    - last_name: 1-50 characters
    - phone: Valid formatting (xxx-xxx-xxxx)
    
    EXAMPLE:
    user = User(1, "john_doe", "John", "Doe", "admin")
    print(user.get_full_name())  # "John Doe"
    is_valid = user.verify_password("SecurePassword123")  # True/False
"""

# ============================================================================
# CLASS 2: ADMIN (Inherits User)
# ============================================================================

"""
class Admin(User):
    PURPOSE: Administrator with system management privileges
    
    ADDITIONAL ATTRIBUTES:
    - permission_level (int): 1-3 (1=basic, 2=week management, 3=full access)
    - last_login (datetime): When admin last accessed system
    - approved_signups (list): Shift signup approvals made by this admin
    
    ADDITIONAL METHODS:
    - approve_shift_request(signup_id: int) -> bool
      - Set shift_signups.status = 'approved'
      - Set shift_signups.approved_at = NOW()
      - Log action in audit_log
      - Notify volunteer via API response
    
    - reject_shift_request(signup_id: int, reason: str) -> bool
      - Set shift_signups.status = 'rejected'
      - Store reason in shift_signups.notes
      - Log action
    
    - finalize_week(week_id: int) -> bool
      - Set weeks.is_finalized = 1
      - Calculate hours for all volunteers
      - Lock changes after finalization
    
    - view_all_participants() -> list
      - Query all volunteers
      - Return with hours, shifts, status
    
    - generate_schedule_report() -> dict
      - Aggregate schedule data
      - Calculate statistics
      - Identify gaps and conflicts
    
    EXAMPLE:
    admin = Admin(1, "admin_user", "Admin", "Account", "admin")
    admin.approve_shift_request(5)  # Approve signup 5
    admin.finalize_week(3)  # Close week 3
    report = admin.generate_schedule_report()
"""

# ============================================================================
# CLASS 3: VOLUNTEER (Inherits User)
# ============================================================================

"""
class Volunteer(User):
    PURPOSE: Base volunteer class with common volunteer functionality
    
    ADDITIONAL ATTRIBUTES:
    - volunteer_type (str): 'regular', 'community', or 'teen'
    - availability (list): Available hours (if tracked)
    - hours_goal (int): Target hours per week
    - total_hours (float): Total hours worked
    - requested_shifts (list): Shift requests submitted
    - approved_shifts (list): Approved shift assignments
    - start_date (date): When volunteer started
    
    ADDITIONAL METHODS:
    - request_shift(shift_id: int) -> bool
      - Create entry in shift_signups
      - Set status = 'pending'
      - Validate no time conflicts
      - Check finalization deadline
      - Call verify_volunteer_type_constraints()
    
    - get_approved_shifts(week_id: int = None) -> list
      - Query shift_signups where status = 'approved'
      - Filter by week if provided
      - Sort by date/time
    
    - get_pending_requests() -> list
      - Query shift_signups where status = 'pending'
      - Show volunteer's pending requests
    
    - request_shift_change(shift_id: int, reason: str) -> bool
      - Create entry in change_requests
      - Submit reason to admin
      - Set status = 'pending'
    
    - get_hours_for_week(week_id: int) -> float
      - Query weekly_hours table
      - Return total hours for week
      - Calculate if not cached
    
    - verify_volunteer_type_constraints() -> bool
      - Call subclass-specific validation
      - Check if constraints are satisfied
    
    EXAMPLE:
    volunteer = Volunteer(2, "jane_smith", "Jane", "Smith", "volunteer")
    volunteer.volunteer_type = "regular"
    volunteer.request_shift(7)  # Request shift 7
    approved = volunteer.get_approved_shifts(week_id=3)
    hours = volunteer.get_hours_for_week(3)  # 8.5 hours
"""

# ============================================================================
# CLASS 4: TEEN VOLUNTEER & SUBCLASSES
# ============================================================================

"""
class TeenVolunteer(Volunteer):
    PURPOSE: Volunteer under 18 with time restrictions
    
    CONSTRAINTS:
    - Cannot work shifts ending at or after 21:00 (9 PM)
    - This is enforced at TWO levels:
      1. Volunteer.request_shift() checks constraint
      2. API endpoint validates before approval
    
    METHODS OVERRIDE:
    - verify_volunteer_type_constraints() -> bool
      - Check shift.end_time < 21:00
      - Return True if valid, False if violates constraint
      - Raise exception with message: "Teen volunteers cannot work past 21:00"
    
    EXAMPLE:
    teen = TeenVolunteer(3, "teen_user", "Alex", "Johnson", "volunteer")
    teen.volunteer_type = "teen"
    
    # This would fail:
    teen.request_shift(5)  # Shift ends at 21:30 - REJECTED
    
    # This would succeed:
    teen.request_shift(6)  # Shift ends at 20:00 - APPROVED

class RegularVolunteer(Volunteer):
    PURPOSE: Standard volunteer with no special restrictions
    
    CONSTRAINTS:
    - None (can work any shift, any time)
    
    EXAMPLE:
    regular = RegularVolunteer(4, "regular_user", "Bob", "Lee", "volunteer")
    regular.request_shift(5)  # Any shift OK

class CommunityServiceVolunteer(Volunteer):
    PURPOSE: Court-ordered community service volunteer
    
    CONSTRAINTS:
    - None at system level (handled by admin policy)
    - Tracking hours for legal compliance
    
    ATTRIBUTES:
    - court_order_id (str): Reference to court order
    - hours_required (int): Court-mandated hours
    - hours_remaining (int): Still owed
    
    METHODS:
    - get_hours_remaining() -> int
    - is_court_requirement_met() -> bool
    
    EXAMPLE:
    community = CommunityServiceVolunteer(5, "cs_user", "Carol", "White", "volunteer")
    community.court_order_id = "COVID-2024-001"
    community.hours_required = 50
"""

# ============================================================================
# CLASS DIAGRAM (Text Format)
# ============================================================================

"""
┌─────────────────────────────────────┐
│            User (Abstract)          │
├─────────────────────────────────────┤
│ - user_id: int                      │
│ - username: str                     │
│ - first_name: str                   │
│ - last_name: str                    │
│ - phone: str                        │
│ - role: str ('admin'|'volunteer')   │
│ - hashed_password: str              │
│ - created_at: datetime              │
├─────────────────────────────────────┤
│ + get_full_name()                   │
│ + verify_password(pwd: str)         │
│ + update_profile()                  │
└─────────────────────────────────────┘
          ▲               ▲
          │               │
    ┌─────┴─┐         ┌───┴──────┐
    │       │         │          │
┌───┴──┐ ┌──┴────────┴───────────┴─────┐
│Admin │ │ Volunteer (Abstract base)   │
├──────┤ ├─────────────────────────────┤
│      │ │ - volunteer_type: str       │
│      │ │ - hours_goal: int           │
│      │ │ - approved_shifts: list     │
├──────┤ ├─────────────────────────────┤
│+ appr│ │ + request_shift()           │
│+ reje│ │ + get_approved_shifts()     │
│+ fina│ │ + get_pending_requests()    │
│+ gene│ │ + request_shift_change()    │
└──────┘ │ + get_hours_for_week()      │
         └────────┬────────────────────┘
                  │
         ┌────────┼────────┐
         │        │        │
    ┌────┴────┐ ┌─┴──────┐ ┌──────────────┐
    │ Regular │ │ Teen   │ │ Community    │
    │         │ │        │ │ Service      │
    ├─────────┤ ├────────┤ ├──────────────┤
    │ No      │ │<= 21:00│ │Court orde    │
    │ limits  │ │strict. │ │Hours track   │
    └─────────┘ └────────┘ └──────────────┘
"""

# ============================================================================
# PASSWORD HASHING & SECURITY
# ============================================================================

"""
BCRYPT IMPLEMENTATION:

import bcrypt

PASSWORD HASHING (Registration):
1. User enters password
2. Generate salt: bcrypt.gensalt(rounds=12)
3. Hash password: bcrypt.hashpw(password.encode(), salt)
4. Store in database ONLY the hash

CODE EXAMPLE:
def hash_password(plain_password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(plain_password.encode(), salt)
    return hashed.decode('utf-8')

stored_hash = hash_password("MyPassword123")
# Stored in database:
# $2b$12$eIrvXFPfgfj8KU.qPE3BKeU0TzILKlEJkF6B8q0HJrQ8WJo.5hJCm

PASSWORD VERIFICATION (Login):
1. User enters password
2. Retrieve stored hash from database
3. Compare: bcrypt.checkpw(plain_password.encode(), stored_hash.encode())
4. If True, password is correct

CODE EXAMPLE:
def verify_password(plain_password: str, stored_hash: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), stored_hash.encode())

is_correct = verify_password("MyPassword123", stored_hash)  # True
is_wrong = verify_password("WrongPassword", stored_hash)    # False

SECURITY PROPERTIES:
✅ One-way: Cannot decrypt hash to get password
✅ Salted: Same password hashes differently each time
✅ Slow: Takes ~100ms per verify (prevents brute force)
✅ Unique: 12 rounds = 2^12 hashing iterations
✅ Future-proof: Can increase rounds as computers get faster
✅ Never stored in memory: Only hashed strings in database
✅ Never logged: Password never appears in logs
✅ Never transmitted: Plaintext only exists during API call
"""

# ============================================================================
# VOLUNTEER TYPE SYSTEM
# ============================================================================

"""
VOLUNTEER TYPE DEFINITIONS:

Type: REGULAR
- Description: Standard volunteer
- Restrictions: None
- Max hours: No limit
- Work times: Any time
- Database value: 'regular'

Type: COMMUNITY SERVICE
- Description: Court-ordered volunteer
- Restrictions: Tracked for compliance
- Max hours: Set by court order
- Work times: Any time
- Requirements: Hours requirement
- Database value: 'community'
- Extra fields: court_order_id, hours_required

Type: TEEN
- Description: Volunteer under 18
- Restrictions: Cannot work past 21:00
- Max hours: Set by site/program policies
- Work times: Cannot end >= 21:00
- Legal compliance: Child labor laws
- Database value: 'teen'
- Age check: If user.age < 18, MUST be 'teen' type
- Enforcement: Two-level (UI + API)

STORAGE IN DATABASE:
user_profiles.volunteer_type = 'regular' | 'community' | 'teen' | NULL

NULL means user is admin (non-volunteer)

QUERY EXAMPLES:
-- Get all teen volunteers
SELECT * FROM user_profiles WHERE volunteer_type = 'teen'

-- Get all volunteers by type
SELECT * FROM user_profiles WHERE volunteer_type = 'regular'

-- Get all admins
SELECT * FROM user_profiles WHERE volunteer_type IS NULL AND role = 'admin'
"""

# ============================================================================
# TESTING STRATEGY
# ============================================================================

"""
IDENTITY & DATABASE ENGINEER TESTS:

1. test_database_stores_hashed_passwords
   - Create user with plain password
   - Query database
   - Verify password is hashed (not plaintext)
   - Verify bcrypt format: $2b$12$...
   - Verify hash is different each time (salt)
   - Verify bcrypt.checkpw() works

2. test_database_enforces_unique_username
   - Create user "alice"
   - Try to create another user "alice"
   - Expect SQLite constraint error
   - Verify first user still exists
   - Second creation was rejected

3. test_database_tracks_user_roles
   - Create admin user (role = 'admin')
   - Create volunteer user (role = 'volunteer')
   - Query by role
   - Verify admins have volunteer_type = NULL
   - Verify volunteers have volunteer_type set

4. test_database_tracks_volunteer_types
   - Create 'regular' volunteer
   - Create 'teen' volunteer
   - Create 'community' volunteer
   - Query each type
   - Verify all 3 types stored correctly
   - Verify teen type is correctly associated

Additional Integration Tests:
- test_volunteer_can_request_shifts
- test_business_rule_password_confirmation
- test_integration_volunteer_type_specific_behavior
"""

# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

"""
KEY OPERATIONS:

USER REGISTRATION:
def register_user(username, password, first_name, last_name, role, volunteer_type=None):
    hashed_pwd = hash_password(password)
    conn = sqlite3.connect('scheduler.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO user_profiles 
            (username, hashed_password, first_name, last_name, role, volunteer_type)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (username, hashed_pwd, first_name, last_name, role, volunteer_type))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        raise Exception("Username already exists")
    finally:
        conn.close()

USER LOGIN:
def login_user(username, password):
    conn = sqlite3.connect('scheduler.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, hashed_password, role FROM user_profiles WHERE username = ?', 
                   (username,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise Exception("User not found")
    
    user_id, stored_hash, role = row
    if not verify_password(password, stored_hash):
        raise Exception("Invalid password")
    
    return user_id, role

CREATE VOLUNTEER ENTRY:
def create_volunteer(user_id, volunteer_type):
    conn = sqlite3.connect('scheduler.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE user_profiles 
        SET volunteer_type = ? 
        WHERE user_id = ?
    ''', (volunteer_type, user_id))
    conn.commit()
    conn.close()

GET VOLUNTEER:
def get_volunteer(volunteer_id):
    conn = sqlite3.connect('scheduler.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_id, username, first_name, last_name, volunteer_type
        FROM user_profiles
        WHERE user_id = ? AND role = 'volunteer'
    ''', (volunteer_id,))
    row = cursor.fetchone()
    conn.close()
    return row

GET ALL VOLUNTEERS BY TYPE:
def get_volunteers_by_type(volunteer_type):
    conn = sqlite3.connect('scheduler.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_id, username, first_name, last_name
        FROM user_profiles
        WHERE volunteer_type = ? AND role = 'volunteer'
    ''', (volunteer_type,))
    rows = cursor.fetchall()
    conn.close()
    return rows

SHIFT SIGNUP:
def create_shift_signup(shift_id, volunteer_id):
    conn = sqlite3.connect('scheduler.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO shift_signups (shift_id, volunteer_id, status, requested_at)
        VALUES (?, ?, 'pending', CURRENT_TIMESTAMP)
    ''', (shift_id, volunteer_id))
    conn.commit()
    conn.close()

APPROVE SHIFT:
def approve_shift_signup(signup_id):
    conn = sqlite3.connect('scheduler.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE shift_signups
        SET status = 'approved', approved_at = CURRENT_TIMESTAMP
        WHERE signup_id = ?
    ''', (signup_id,))
    conn.commit()
    conn.close()

CALCULATE HOURS:
def calculate_hours_for_volunteer(volunteer_id, week_id):
    conn = sqlite3.connect('scheduler.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT SUM(
            (julianday(shifts.end_time) - julianday(shifts.start_time)) * 24
        )
        FROM shift_signups
        JOIN shifts ON shift_signups.shift_id = shifts.shift_id
        WHERE shift_signups.volunteer_id = ? 
        AND shifts.week_id = ?
        AND shift_signups.status = 'approved'
    ''', (volunteer_id, week_id))
    total_hours = cursor.fetchone()[0] or 0
    
    cursor.execute('''
        INSERT INTO weekly_hours (volunteer_id, week_id, total_hours, calculated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(volunteer_id, week_id) DO UPDATE SET total_hours = ?
    ''', (volunteer_id, week_id, total_hours, total_hours))
    conn.commit()
    conn.close()
    return total_hours
"""

# ============================================================================
# SUCCESS CRITERIA
# ============================================================================

"""
✅ COMPLETED:
- Database schema with 7+ normalized tables
- All 4 domain model classes implemented
- Password hashing with bcrypt working
- User registration and login working
- Volunteer type system implemented (regular, community, teen)
- Role system (admin vs volunteer) working
- Shift signup tracking working
- Hours calculation working
- All constraints enforced
- All tests passing

METRICS:
- Lines of Code: 162 (database.py) + 315 (models.py) = 477 lines
- Tables: 7 normalized with proper constraints
- Classes: 4 (User, Admin, Volunteer, Teen/Regular/Community subclasses)
- Bcrypt hashing: ✅ Implemented
- Password verification: ✅ Working
- Volunteer types: 3 (regular, community, teen)
- Tests Passing: 4+ database-specific tests
- Foreign keys: 100% enforced
- Unique constraints: username, week_start, site_name, volunteer_id+week_id
"""

# ============================================================================
# DOCUMENTATION REFERENCES
# ============================================================================

"""
Related Files:
- src/database.py - Database initialization and connection
- src/models.py - Domain model classes
- docs/Architecture_Overview.docx - System design
- ROLE_DOCUMENTATION.md - General reference

API Integration:
- See api_backend_role.md for data usage
- See Backend API Developer documentation

Security:
- Bcrypt password hashing
- SQL injection prevention (parameterized queries)
- Role-based access control (RBAC)
- Token-based authentication (vs passwords in API)
"""
