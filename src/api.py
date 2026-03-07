from flask import Flask, request, jsonify
import sqlite3
import os
import bcrypt
import jwt
import datetime

DB_PATH = "scheduler.db"
JWT_SECRET = "your-secret-key-change-this-in-production"
JWT_ALGORITHM = "HS256"

app = Flask(__name__)


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def ensure_is_published_column():
    conn = get_conn()
    try:
        cur = conn.execute("PRAGMA table_info(weeks)")
        cols = [row['name'] for row in cur.fetchall()]
        if 'is_published' not in cols:
            conn.execute("ALTER TABLE weeks ADD COLUMN is_published INTEGER DEFAULT 0")
            conn.commit()
    except Exception:
        pass
    finally:
        conn.close()

ensure_is_published_column()

def require_token(f):
    """Decorator to verify JWT token and extract user_id."""
    from functools import wraps

    @wraps(f)
    def wrapper(*args, **kwargs):
        token = None
        if request.headers.get('Authorization'):
            try:
                auth_header = request.headers.get('Authorization')
                if auth_header.startswith('Bearer '):
                    token = auth_header[7:]
            except:
                pass
        
        if not token:
            return jsonify({'error': 'token required'}), 401
        
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            user_id = payload.get('user_id')
            role = payload.get('role')
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'invalid token'}), 401
        
        # Store in request context for the handler to use
        request.user_id = user_id
        request.user_role = role
        return f(*args, **kwargs)

    return wrapper


def require_admin_token(f):
    """Decorator to verify JWT token and ensure user is admin."""
    from functools import wraps

    @wraps(f)
    def wrapper(*args, **kwargs):
        token = None
        if request.headers.get('Authorization'):
            try:
                auth_header = request.headers.get('Authorization')
                if auth_header.startswith('Bearer '):
                    token = auth_header[7:]
            except:
                pass
        
        if not token:
            return jsonify({'error': 'token required'}), 401
        
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            user_id = payload.get('user_id')
            role = payload.get('role')
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'invalid token'}), 401
        
        if role != 'admin':
            return jsonify({'error': 'admin privileges required'}), 403
        
        request.user_id = user_id
        request.user_role = role
        return f(*args, **kwargs)

    return wrapper


# USER REGISTRATION
@app.route("/register", methods=["POST"])
def register():
    data = request.json or {}

    required = [
        "first_name", "last_name", "username",
        "address", "phone", "password", "confirm_password"
    ]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"Missing field: {field}"}), 400

    if data["password"] != data["confirm_password"]:
        return jsonify({"error": "Passwords do not match"}), 400

    try:
        # Hash the password
        hashed_password = bcrypt.hashpw(data["password"].encode('utf-8'), bcrypt.gensalt())
        
        conn = get_conn()
        role = data.get("role", "volunteer")
        volunteer_type = data.get("volunteer_type", "regular")
        conn.execute("""
            INSERT INTO user_profiles
            (first_name, last_name, username, address, phone, password, role, volunteer_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["first_name"],
            data["last_name"],
            data["username"],
            data["address"],
            data["phone"],
            hashed_password,
            role,
            volunteer_type,
        ))
        conn.commit()
        conn.close()
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username already taken"}), 400

    return jsonify({"success": True}), 201


# LOGIN
@app.route("/login", methods=["POST"])
def login():
    data = request.json or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    conn = get_conn()
    cur = conn.execute("""
        SELECT id, first_name, last_name, username, password, role, volunteer_type
        FROM user_profiles
        WHERE username=?
    """, (username,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "Invalid username or password"}), 401

    # Verify password
    stored_password = row["password"]
    # Handle both hashed (bytes) and plain text (string) passwords for backward compatibility
    if isinstance(stored_password, bytes):
        if not bcrypt.checkpw(password.encode('utf-8'), stored_password):
            return jsonify({"error": "Invalid username or password"}), 401
    else:
        # Old plain text password (for backward compatibility)
        if stored_password != password:
            return jsonify({"error": "Invalid username or password"}), 401

    # Generate JWT token
    payload = {
        'user_id': row['id'],
        'username': row['username'],
        'role': row['role'] if row['role'] else 'volunteer',
        'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return jsonify({
        "token": token,
        "id": row["id"],
        "first_name": row["first_name"],
        "last_name": row["last_name"],
        "username": row["username"],
        "role": row["role"] if row["role"] else "volunteer",
        "volunteer_type": row["volunteer_type"] if row["volunteer_type"] else "regular",
    }), 200


# WEEKS
@app.route("/weeks", methods=["POST"])
@require_admin_token
def create_week():
    data = request.json or {}
    week_start = data.get("week_start")
    deadline = data.get("finalization_deadline")

    if not week_start or not deadline:
        return jsonify({"error": "Missing week_start or finalization_deadline"}), 400

    conn = get_conn()
    conn.execute("""
        INSERT INTO weeks (week_start, finalization_deadline)
        VALUES (?, ?)
    """, (week_start, deadline))
    conn.commit()
    conn.close()

    return jsonify({"success": True}), 201


@app.route("/weeks", methods=["GET"])
def get_weeks():
    is_admin = False
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        try:
            token = auth_header[7:]
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            if payload.get('role') == 'admin':
                is_admin = True
        except:
            pass

    conn = get_conn()
    if is_admin:
        cur = conn.execute("SELECT * FROM weeks ORDER BY id DESC")
    else:
        cur = conn.execute("SELECT * FROM weeks WHERE is_published=1 ORDER BY id DESC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify(rows), 200


@app.route('/weeks/<int:week_id>/finalize', methods=['POST'])
@require_admin_token
def finalize_week(week_id):
    conn = get_conn()
    conn.execute("UPDATE weeks SET is_finalized=1 WHERE id=?", (week_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True}), 200

@app.route('/weeks/<int:week_id>/publish', methods=['POST'])
@require_admin_token
def publish_week(week_id):
    conn = get_conn()
    conn.execute("UPDATE weeks SET is_published=1 WHERE id=?", (week_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True}), 200


# SITES
@app.route("/sites", methods=["GET"])
def get_sites():
    conn = get_conn()
    cur = conn.execute("SELECT * FROM sites ORDER BY site_name")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify(rows), 200


# SHIFTS - list all or open
@app.route("/shifts", methods=["GET"])
@require_token
def list_shifts():
    only_open = request.args.get('open') == '1'
    conn = get_conn()
    if only_open:
        cur = conn.execute("""
            SELECT s.*, sites.site_name,
                   (SELECT COUNT(*) FROM shift_signups WHERE shift_signups.shift_id = s.id) AS current_signups
            FROM shifts s
            JOIN sites ON s.site_id = sites.id
            WHERE (SELECT COUNT(*) FROM shift_signups WHERE shift_signups.shift_id = s.id) < s.max_volunteers
            ORDER BY s.date, s.start_time
        """)
    else:
        cur = conn.execute("""
            SELECT s.*, sites.site_name,
                   (SELECT COUNT(*) FROM shift_signups WHERE shift_signups.shift_id = s.id) AS current_signups
            FROM shifts s
            JOIN sites ON s.site_id = sites.id
            ORDER BY s.date, s.start_time
        """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify(rows), 200


# SHIFTS
@app.route("/shifts", methods=["POST"])
@require_admin_token
def create_shift():
    data = request.json or {}

    required = ["week_id", "site_id", "date", "start_time", "end_time", "max_volunteers"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"Missing field: {field}"}), 400

    shift_role = data.get("role", "any")
    conn = get_conn()
    conn.execute("""
        INSERT INTO shifts (week_id, site_id, role, date, start_time, end_time, max_volunteers)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        data["week_id"],
        data["site_id"],
        shift_role,
        data["date"],
        data["start_time"],
        data["end_time"],
        data["max_volunteers"]
    ))
    conn.commit()
    conn.close()

    return jsonify({"success": True}), 201


@app.route("/weeks/<int:week_id>/shifts", methods=["GET"])
@require_token
def get_shifts_for_week(week_id):
    conn = get_conn()
    cur = conn.execute("""
        SELECT shifts.*, sites.site_name,
               (SELECT COUNT(*) FROM shift_signups WHERE shift_signups.shift_id = shifts.id) AS current_signups
        FROM shifts
        JOIN sites ON shifts.site_id = sites.id
        WHERE week_id=?
        ORDER BY date, start_time
    """, (week_id,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify(rows), 200


# SHIFT SIGNUPS (original)
@app.route("/shifts/<int:shift_id>/signups", methods=["POST"])
@require_token
def signup_for_shift(shift_id):
    data = request.json or {}
    volunteer_id = data.get("volunteer_id")

    if not volunteer_id:
        return jsonify({"error": "Missing volunteer_id"}), 400

    conn = get_conn()

    cur = conn.execute("""
        SELECT COUNT(shift_signups.id) AS count, max_volunteers
        FROM shifts
        LEFT JOIN shift_signups ON shifts.id = shift_signups.shift_id
        WHERE shifts.id=?
    """, (shift_id,))
    row = cur.fetchone()

    if row["count"] >= row["max_volunteers"]:
        conn.close()
        return jsonify({"error": "Shift is full"}), 400

    conn.execute("""
        INSERT INTO shift_signups (shift_id, volunteer_id, status)
        VALUES (?, ?, 'pending')
    """, (shift_id, volunteer_id))
    conn.commit()
    conn.close()

    return jsonify({"success": True}), 201


# LIST PENDING SIGNUPS (for admin)
@app.route("/signups/pending", methods=["GET"])
@require_admin_token
def get_pending_signups():
    conn = get_conn()
    cur = conn.execute("""
        SELECT
            shift_signups.id AS signup_id,
            shift_signups.shift_id,
            shift_signups.volunteer_id,
            user_profiles.username AS volunteer_username,
            shifts.date,
            shifts.start_time,
            shifts.end_time,
            shifts.site_id,
            sites.site_name,
            shifts.week_id,
            shift_signups.status
        FROM shift_signups
        JOIN user_profiles ON shift_signups.volunteer_id = user_profiles.id
        JOIN shifts ON shift_signups.shift_id = shifts.id
        LEFT JOIN sites ON shifts.site_id = sites.id
        WHERE shift_signups.status = 'pending'
        ORDER BY shifts.date, shifts.start_time
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify(rows), 200


# SHIFT REQUESTS (volunteer GUI)
@app.route("/shift_requests", methods=["POST"])
@require_token
def create_shift_request():
    data = request.json or {}
    volunteer_id = data.get("volunteer_id")
    shift_id = data.get("shift_id")
    status = data.get("status", "pending")

    if not volunteer_id or not shift_id:
        return jsonify({"error": "volunteer_id and shift_id are required"}), 400

    conn = get_conn()
    # Check shift capacity and week finalization/deadline
    cur = conn.execute("SELECT s.*, w.finalization_deadline, w.is_finalized FROM shifts s JOIN weeks w ON s.week_id = w.id WHERE s.id=?", (shift_id,))
    shift_row = cur.fetchone()
    if not shift_row:
        conn.close()
        return jsonify({"error": "Shift not found"}), 404

    # check finalized
    if shift_row["is_finalized"]:
        conn.close()
        return jsonify({"error": "Week finalized - no new requests allowed"}), 400
    
    ddl_str = shift_row["finalization_deadline"]
    if ddl_str:
        try:
            deadline_date = datetime.datetime.strptime(ddl_str, "%Y-%m-%d").date()
            if datetime.datetime.now().date() > deadline_date:
                conn.close()
                return jsonify({"error": "Finalization deadline passed - no new requests allowed"}), 400
        except (ValueError, TypeError):
            pass # Ignore if format is wrong or ddl_str is None

    cur = conn.execute("SELECT COUNT(*) AS count FROM shift_signups WHERE shift_id=?", (shift_id,))
    cnt = cur.fetchone()["count"]
    if cnt >= shift_row["max_volunteers"]:
        conn.close()
        return jsonify({"error": "Shift is full"}), 400

    # Enforce teen volunteer time restrictions
    cur = conn.execute("SELECT volunteer_type FROM user_profiles WHERE id=?", (volunteer_id,))
    vrow = cur.fetchone()
    volunteer_type = vrow["volunteer_type"] if vrow else "regular"

    end_time = shift_row["end_time"]
    if end_time and volunteer_type == 'teen':
        try:
            hh, mm = map(int, end_time.split(":"))
            if hh >= 21:
                conn.close()
                return jsonify({"error": "Teen volunteers cannot be assigned to late shifts"}), 400
        except Exception:
            pass

    conn.execute("""
        INSERT INTO shift_signups (shift_id, volunteer_id, status)
        VALUES (?, ?, ?)
    """, (shift_id, volunteer_id, status))
    conn.commit()
    conn.close()

    return jsonify({"success": True}), 201


# APPROVE SIGNUP (now updates weekly_hours)
@app.route("/signups/<int:signup_id>/approve", methods=["POST"])
@require_admin_token
def approve_signup(signup_id):
    conn = get_conn()

    conn.execute("""
        UPDATE shift_signups
        SET status='approved'
        WHERE id=?
    """, (signup_id,))

    cur = conn.execute("""
        SELECT shift_signups.volunteer_id,
               shifts.week_id,
               shifts.date,
               shifts.start_time,
               shifts.end_time
        FROM shift_signups
        JOIN shifts ON shift_signups.shift_id = shifts.id
        WHERE shift_signups.id=?
    """, (signup_id,))
    row = cur.fetchone()

    volunteer_id = row["volunteer_id"]
    week_id = row["week_id"]

    cur = conn.execute("""
        SELECT (julianday(date || ' ' || end_time) -
                julianday(date || ' ' || start_time)) * 24 AS hours
        FROM shifts
        WHERE week_id=? AND date=? AND start_time=? AND end_time=?
    """, (week_id, row["date"], row["start_time"], row["end_time"]))
    hours = cur.fetchone()["hours"] or 0

    cur = conn.execute("""
        SELECT id, total_hours
        FROM weekly_hours
        WHERE volunteer_id=? AND week_id=?
    """, (volunteer_id, week_id))
    existing = cur.fetchone()

    if existing:
        conn.execute("""
            UPDATE weekly_hours
            SET total_hours = total_hours + ?
            WHERE id=?
        """, (hours, existing["id"]))
    else:
        conn.execute("""
            INSERT INTO weekly_hours (volunteer_id, week_id, total_hours)
            VALUES (?, ?, ?)
        """, (volunteer_id, week_id, hours))

    conn.commit()
    conn.close()

    return jsonify({"success": True}), 200


@app.route("/signups/<int:signup_id>/deny", methods=["POST"])
@require_admin_token
def deny_signup(signup_id):
    conn = get_conn()
    conn.execute("""
        UPDATE shift_signups
        SET status='denied'
        WHERE id=?
    """, (signup_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True}), 200


# CHANGE REQUESTS
@app.route("/change_requests", methods=["POST"])
@require_token
def submit_change_request():
    data = request.json or {}

    if "change_type" in data:
        required = ["volunteer_id", "change_type", "from_shift_id"]
        for field in required:
            if not data.get(field):
                return jsonify({"error": f"Missing field: {field}"}), 400

        change_type = data["change_type"]
        from_shift_id = data["from_shift_id"]
        to_shift_id = data.get("to_shift_id")
        new_start_time = data.get("new_start_time")
        new_end_time = data.get("new_end_time")
        reason = data.get("reason")

    else:
        if not data.get("volunteer_id") or not data.get("shift_id") or not data.get("reason"):
            return jsonify({"error": "volunteer_id, shift_id, and reason are required"}), 400

        change_type = "general"
        from_shift_id = data["shift_id"]
        to_shift_id = None
        new_start_time = None
        new_end_time = None
        reason = data["reason"]

    conn = get_conn()
    conn.execute("""
        INSERT INTO change_requests
        (volunteer_id, change_type, from_shift_id, to_shift_id,
         new_start_time, new_end_time, reason, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
    """, (
        data["volunteer_id"],
        change_type,
        from_shift_id,
        to_shift_id,
        new_start_time,
        new_end_time,
        reason
    ))
    conn.commit()
    conn.close()

    return jsonify({"success": True}), 201


@app.route("/change_requests/<int:req_id>/approve", methods=["POST"])
@require_admin_token
def approve_change_request(req_id):
    conn = get_conn()
    conn.execute("""
        UPDATE change_requests
        SET status='approved'
        WHERE id=?
    """, (req_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True}), 200


@app.route("/change_requests/pending", methods=["GET"])
@require_admin_token
def get_pending_change_requests():
    conn = get_conn()
    cur = conn.execute("""
        SELECT cr.id AS request_id,
               cr.volunteer_id,
               u.username AS volunteer_username,
               cr.change_type,
               cr.from_shift_id,
               cr.to_shift_id,
               cr.new_start_time,
               cr.new_end_time,
               cr.reason,
               cr.status
        FROM change_requests cr
        JOIN user_profiles u ON cr.volunteer_id = u.id
        WHERE cr.status = 'pending'
        ORDER BY cr.id DESC
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify(rows), 200


@app.route("/change_requests/<int:req_id>/deny", methods=["POST"])
@require_admin_token
def deny_change_request(req_id):
    conn = get_conn()
    conn.execute("""
        UPDATE change_requests
        SET status='denied'
        WHERE id=?
    """, (req_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True}), 200


# WEEKLY HOURS (volunteer GUI)
@app.route("/volunteers/<int:volunteer_id>/hours", methods=["GET"])
@require_token
def get_hours(volunteer_id):
    week_id = request.args.get("week_id", type=int)
    if not week_id:
        return jsonify({"error": "week_id query parameter is required"}), 400

    conn = get_conn()
    cur = conn.execute("""
        SELECT total_hours
        FROM weekly_hours
        WHERE volunteer_id=? AND week_id=?
    """, (volunteer_id, week_id))
    row = cur.fetchone()
    conn.close()

    return jsonify({"total_hours": row["total_hours"] if row else 0}), 200


@app.route("/volunteers", methods=["GET"])
@require_admin_token
def list_volunteers():
    conn = get_conn()
    cur = conn.execute("SELECT id, first_name, last_name, username, role, volunteer_type, availability FROM user_profiles ORDER BY username")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify(rows), 200


@app.route("/volunteers/<int:volunteer_id>", methods=["GET"])
@require_token
def get_volunteer(volunteer_id):
    conn = get_conn()
    cur = conn.execute("SELECT id, first_name, last_name, username, role, volunteer_type, availability FROM user_profiles WHERE id=?", (volunteer_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Volunteer not found"}), 404
    return jsonify(dict(row)), 200


@app.route("/volunteers/<int:volunteer_id>/availability", methods=["POST"])
@require_token
def update_availability(volunteer_id):
    data = request.json or {}
    availability = data.get('availability')
    if availability is None:
        return jsonify({"error": "availability field required"}), 400
    conn = get_conn()
    conn.execute("UPDATE user_profiles SET availability=? WHERE id=?", (availability, volunteer_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True}), 200


# APPROVED SHIFTS
@app.route("/volunteers/<int:volunteer_id>/approved_shifts", methods=["GET"])
@require_token
def get_approved_shifts(volunteer_id):
    conn = get_conn()
    cur = conn.execute("""
        SELECT
            shifts.id AS shift_id,
            shifts.date,
            shifts.start_time,
            shifts.end_time,
            shifts.site_id,
            weeks.week_start
        FROM shift_signups
        JOIN shifts ON shift_signups.shift_id = shifts.id
        JOIN weeks ON shifts.week_id = weeks.id
        WHERE shift_signups.volunteer_id=?
          AND shift_signups.status='approved'
        ORDER BY shifts.date, shifts.start_time
    """, (volunteer_id,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify(rows), 200


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    app.run(debug=True)