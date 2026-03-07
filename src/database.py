"""
Database Module

Initializes and manages the SQLite database for the Volunteer Scheduler system.
Handles schema creation, migrations, and seed data.

Tables:
- user_profiles: Admin and volunteer user accounts
- weeks: Weekly schedules with finalization status
- sites: Work site locations
- shifts: Individual shift assignments
- shift_signups: Volunteer requests to work shifts
- change_requests: Volunteer requests to modify shifts
- weekly_hours: Tracking of hours worked per week
"""

import sqlite3
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

DB_PATH = "scheduler.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # USER PROFILES (include role for multi-admin support)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        username TEXT UNIQUE NOT NULL,
        address TEXT NOT NULL,
        phone TEXT NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'volunteer',
        volunteer_type TEXT NOT NULL DEFAULT 'regular'
    );
    """)

    # If older DB exists without 'role' column, add it.
    try:
        cur.execute("PRAGMA table_info(user_profiles);")
        cols = [r[1] for r in cur.fetchall()]
        if 'role' not in cols:
            cur.execute("ALTER TABLE user_profiles ADD COLUMN role TEXT NOT NULL DEFAULT 'volunteer';")
        if 'volunteer_type' not in cols:
            cur.execute("ALTER TABLE user_profiles ADD COLUMN volunteer_type TEXT NOT NULL DEFAULT 'regular';")
        if 'availability' not in cols:
            cur.execute("ALTER TABLE user_profiles ADD COLUMN availability TEXT DEFAULT NULL;")
    except Exception:
        pass

    # WEEKS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS weeks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        week_start TEXT NOT NULL,
        finalization_deadline TEXT NOT NULL,
        is_finalized INTEGER NOT NULL DEFAULT 0
    );
    """)

    # Ensure 'is_finalized' exists on older weeks table
    try:
        cur.execute("PRAGMA table_info(weeks);")
        cols = [r[1] for r in cur.fetchall()]
        if 'is_finalized' not in cols:
            cur.execute("ALTER TABLE weeks ADD COLUMN is_finalized INTEGER NOT NULL DEFAULT 0;")
    except Exception:
        pass

    # SITES
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        site_name TEXT NOT NULL
    );
    """)

    # SHIFTS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS shifts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        week_id INTEGER NOT NULL,
        site_id INTEGER NOT NULL,
        role TEXT NOT NULL DEFAULT 'any',
        date TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        max_volunteers INTEGER NOT NULL,
        FOREIGN KEY (week_id) REFERENCES weeks(id),
        FOREIGN KEY (site_id) REFERENCES sites(id)
    );
    """)

    # SHIFT SIGNUPS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS shift_signups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shift_id INTEGER NOT NULL,
        volunteer_id INTEGER NOT NULL,
        status TEXT NOT NULL,
        FOREIGN KEY (shift_id) REFERENCES shifts(id),
        FOREIGN KEY (volunteer_id) REFERENCES user_profiles(id)
    );
    """)

    # CHANGE REQUESTS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS change_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        volunteer_id INTEGER NOT NULL,
        change_type TEXT NOT NULL,
        from_shift_id INTEGER NOT NULL,
        to_shift_id INTEGER,
        new_start_time TEXT,
        new_end_time TEXT,
        reason TEXT,
        status TEXT NOT NULL,
        FOREIGN KEY (volunteer_id) REFERENCES user_profiles(id),
        FOREIGN KEY (from_shift_id) REFERENCES shifts(id),
        FOREIGN KEY (to_shift_id) REFERENCES shifts(id)
    );
    """)

    # WEEKLY HOURS (now used by API)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS weekly_hours (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        volunteer_id INTEGER NOT NULL,
        week_id INTEGER NOT NULL,
        total_hours REAL NOT NULL,
        FOREIGN KEY (volunteer_id) REFERENCES user_profiles(id),
        FOREIGN KEY (week_id) REFERENCES weeks(id)
    );
    """)

    # SEED SITES
    cur.execute("SELECT COUNT(*) FROM sites")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO sites (site_name) VALUES (?)",
            [
                ("Main Building",),
                ("Driver - Pickup",),
                ("Driver - Dropoff to Appointments",),
                ("Driver - Dropoff to Home",),
                ("Driver - Pickup from Appointments",)
            ]
        )

    # Ensure at least one admin account exists
    try:
        cur.execute("SELECT COUNT(*) FROM user_profiles WHERE role='admin'")
        if cur.fetchone()[0] == 0:
            try:
                cur.execute(
                    "INSERT INTO user_profiles (first_name, last_name, username, address, phone, password, role) VALUES (?, ?, ?, ?, ?, ?, 'admin')",
                    ("Default", "Admin", "admin", "", "", "admin")
                )
            except Exception:
                pass
    except Exception:
        pass

    conn.commit()
    conn.close()


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    init_db()
    print("Database initialized successfully.")
