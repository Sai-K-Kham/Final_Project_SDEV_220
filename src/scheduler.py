"""
Scheduler Module

This module provides scheduling utilities and business logic for managing shifts,
requests, and volunteer assignments.
"""

from datetime import datetime, timedelta
from models import Shift, Volunteer, TeenVolunteer


class ScheduleManager:
    """
    Manages shift scheduling, requests, and approvals.
    
    Provides methods for:
    - Generating shift requests
    - Validating shift capacity and conflicts
    - Enforcing business rules (teen restrictions, finalization, etc.)
    - Calculating volunteer hours
    """
    
    # Business rule constraints
    TEEN_MAX_END_TIME = 21.0  # 9 PM
    WEEK_FINALIZATION_DAYS = 3  # Days before week start to accept requests
    
    def __init__(self, db_connection=None):
        """
        Initialize scheduler with optional database connection.
        
        Args:
            db_connection: SQLite connection for data persistence
        """
        self.db = db_connection
        self.shifts = {}  # shift_id -> Shift object
        self.requests = {}  # request_id -> request data
    
    @staticmethod
    def parse_time(time_str):
        """
        Parse time string to float hours (24-hour format).
        
        Args:
            time_str (str): Time in HH:MM format
        
        Returns:
            float: Hours in 24-hour format (e.g., 14.5 for 2:30 PM)
        """
        if ':' not in time_str:
            return float(time_str)
        
        hours, minutes = time_str.split(':')
        return float(hours) + float(minutes) / 60
    
    @staticmethod
    def time_to_string(hours):
        """
        Convert float hours to HH:MM string format.
        
        Args:
            hours (float): Hours in 24-hour format
        
        Returns:
            str: Time in HH:MM format
        """
        hour = int(hours)
        minute = int((hours - hour) * 60)
        return f"{hour:02d}:{minute:02d}"
    
    @staticmethod
    def is_time_conflict(shift1_start, shift1_end, shift2_start, shift2_end):
        """
        Check if two shifts have a time conflict.
        
        Args:
            shift1_start (float): Start time of shift 1
            shift1_end (float): End time of shift 1
            shift2_start (float): Start time of shift 2
            shift2_end (float): End time of shift 2
        
        Returns:
            bool: True if shifts overlap, False otherwise
        """
        return not (shift1_end <= shift2_start or shift2_end <= shift1_start)
    
    def can_volunteer_work_shift(self, volunteer, shift, existing_shifts=None):
        """
        Check if volunteer can work given shift based on constraints.
        
        Args:
            volunteer (Volunteer): Volunteer object or volunteer_type string
            shift (Shift): Shift object or dict with shift details
            existing_shifts (list): Optional list of existing shifts for conflict check
        
        Returns:
            tuple: (bool, str) - (can_work, reason_if_not)
        """
        # Extract volunteer type
        if isinstance(volunteer, str):
            vol_type = volunteer
        elif hasattr(volunteer, 'volunteer_type'):
            vol_type = volunteer.volunteer_type
        else:
            vol_type = "regular"
        
        # Extract shift details
        if isinstance(shift, dict):
            shift_role = shift.get('role', 'any')
            end_time_hour = self.parse_time(shift.get('end_time', '17:00'))
        else:
            shift_role = shift.role
            end_time_hour = self.parse_time(shift.end_time)
        
        # Check role compatibility
        if shift_role != 'any' and shift_role != vol_type:
            return False, f"Shift requires {shift_role} volunteer"
        
        # Check teen time restrictions
        if vol_type == 'teen' and end_time_hour >= self.TEEN_MAX_END_TIME:
            return False, "Teen volunteers cannot work shifts ending after 21:00"
        
        # Check for time conflicts
        if existing_shifts:
            if isinstance(shift, dict):
                shift_start = self.parse_time(shift.get('start_time', '0:00'))
                shift_end = self.parse_time(shift.get('end_time', '17:00'))
            else:
                shift_start = self.parse_time(shift.start_time)
                shift_end = self.parse_time(shift.end_time)
            
            for existing_shift in existing_shifts:
                existing_start = self.parse_time(existing_shift.get('start_time', '0:00'))
                existing_end = self.parse_time(existing_shift.get('end_time', '17:00'))
                
                if self.is_time_conflict(shift_start, shift_end, existing_start, existing_end):
                    return False, "Time conflict with existing shift"
        
        return True, ""
    
    def calculate_volunteer_hours(self, shifts):
        """
        Calculate total hours from list of shifts.
        
        Args:
            shifts (list): List of shift dicts with 'start_time' and 'end_time'
        
        Returns:
            float: Total hours worked
        """
        total_hours = 0.0
        
        for shift in shifts:
            start = self.parse_time(shift.get('start_time', '0:00'))
            end = self.parse_time(shift.get('end_time', '0:00'))
            total_hours += (end - start)
        
        return round(total_hours, 2)
    
    def is_week_finalized(self, week_start_date, db=None):
        """
        Check if given week is finalized (no new requests allowed).
        
        Args:
            week_start_date (str): Week start date in YYYY-MM-DD format
            db: Optional database connection
        
        Returns:
            bool: True if week is finalized
        """
        if db:
            # Query database for finalization status
            cursor = db.cursor()
            cursor.execute("""
                SELECT is_finalized FROM weeks 
                WHERE week_start = ?
            """, (week_start_date,))
            result = cursor.fetchone()
            return result[0] == 1 if result else False
        
        return False
    
    def is_past_finalization_deadline(self, week_start_date, current_date=None):
        """
        Check if request deadline has passed for given week.
        
        Args:
            week_start_date (str): Week start date in YYYY-MM-DD format
            current_date (str): Optional current date (defaults to today)
        
        Returns:
            bool: True if past deadline
        """
        if not current_date:
            current_date = datetime.now().date()
        elif isinstance(current_date, str):
            current_date = datetime.strptime(current_date, '%Y-%m-%d').date()
        
        if isinstance(week_start_date, str):
            week_start = datetime.strptime(week_start_date, '%Y-%m-%d').date()
        else:
            week_start = week_start_date
        
        # Requests must be 3+ days before week start
        deadline = week_start - timedelta(days=self.WEEK_FINALIZATION_DAYS)
        
        return current_date > deadline
    
    def get_week_start(self, date_str):
        """
        Get the Monday of the week containing given date.
        
        Args:
            date_str (str): Date in YYYY-MM-DD format
        
        Returns:
            str: Monday's date in YYYY-MM-DD format
        """
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        # Monday is weekday 0
        monday = date - timedelta(days=date.weekday())
        return monday.strftime('%Y-%m-%d')
    
    def get_week_end(self, date_str):
        """
        Get the Sunday of the week containing given date.
        
        Args:
            date_str (str): Date in YYYY-MM-DD format
        
        Returns:
            str: Sunday's date in YYYY-MM-DD format
        """
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        # Sunday is 6 days after Monday
        sunday = date + timedelta(days=6 - date.weekday())
        return sunday.strftime('%Y-%m-%d')


def generate_week_dates(week_start_str):
    """
    Generate list of dates for all 7 days of a week.
    
    Args:
        week_start_str (str): Monday's date in YYYY-MM-DD format
    
    Returns:
        list: List of 7 date strings (Mon-Sun)
    """
    week_start = datetime.strptime(week_start_str, '%Y-%m-%d').date()
    dates = []
    for i in range(7):
        date = week_start + timedelta(days=i)
        dates.append(date.strftime('%Y-%m-%d'))
    return dates


def get_current_week_start():
    """
    Get the Monday of the current week.
    
    Returns:
        str: Monday's date in YYYY-MM-DD format
    """
    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())
    return monday.strftime('%Y-%m-%d')
