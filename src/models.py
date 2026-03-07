"""
Domain Model Classes

This module defines the core domain objects for the Volunteer Scheduling System:
- Volunteer (superclass) with subclasses: RegularVolunteer, CommunityServiceVolunteer, TeenVolunteer
- Shift: represents a scheduled work period
- Admin: administrator user class
"""


class Volunteer:
    """
    Base Volunteer superclass.
    
    Attributes:
        volunteer_id (int): Unique identifier
        name (str): Volunteer name
        email (str): Email address
        phone (str): Phone number
        volunteer_type (str): Type of volunteer (regular, community, teen)
        availability (str): Weekly availability schedule
    
    Methods:
        request_shift(): Submit request to work a shift
        request_change(): Submit request to change assigned shift
        view_schedule(): View personal schedule
    """
    
    def __init__(self, volunteer_id, name, email, phone, volunteer_type, availability=""):
        self.volunteer_id = volunteer_id
        self.name = name
        self.email = email
        self.phone = phone
        self.volunteer_type = volunteer_type
        self.availability = availability
        self.assigned_shifts = []
    
    def request_shift(self, shift_id, api_client=None):
        """Submit request to work a shift."""
        if api_client:
            return api_client.post('/shift_requests', {
                'volunteer_id': self.volunteer_id,
                'shift_id': shift_id
            })
        return None
    
    def request_change(self, shift_id, new_time, reason="", api_client=None):
        """Submit request to change assigned shift."""
        if api_client:
            return api_client.post('/change_requests', {
                'volunteer_id': self.volunteer_id,
                'shift_id': shift_id,
                'new_time': new_time,
                'reason': reason
            })
        return None
    
    def view_schedule(self, api_client=None):
        """View personal schedule."""
        if api_client:
            return api_client.get(f'/volunteers/{self.volunteer_id}/approved_shifts')
        return []
    
    def __repr__(self):
        return f"Volunteer({self.volunteer_id}, {self.name}, {self.volunteer_type})"


class RegularVolunteer(Volunteer):
    """
    Regular volunteer with standard availability constraints.
    Can work any shift type and time.
    """
    
    def __init__(self, volunteer_id, name, email, phone, availability=""):
        super().__init__(volunteer_id, name, email, phone, "regular", availability)
    
    def __repr__(self):
        return f"RegularVolunteer({self.volunteer_id}, {self.name})"


class CommunityServiceVolunteer(Volunteer):
    """
    Community service volunteer, often working to complete court-ordered hours.
    Can work any shift type and time.
    """
    
    def __init__(self, volunteer_id, name, email, phone, availability=""):
        super().__init__(volunteer_id, name, email, phone, "community", availability)
    
    def __repr__(self):
        return f"CommunityServiceVolunteer({self.volunteer_id}, {self.name})"


class TeenVolunteer(Volunteer):
    """
    Teen volunteer with time-of-day restrictions.
    Cannot work shifts ending at or after 21:00 (9 PM).
    """
    
    MAX_END_TIME = 21.0  # 9 PM in 24-hour format
    
    def __init__(self, volunteer_id, name, email, phone, availability=""):
        super().__init__(volunteer_id, name, email, phone, "teen", availability)
    
    def can_work_shift(self, end_time_hour):
        """Check if teen can work a shift ending at given hour."""
        return end_time_hour < self.MAX_END_TIME
    
    def __repr__(self):
        return f"TeenVolunteer({self.volunteer_id}, {self.name})"


class Shift:
    """
    Represents a scheduled work period.
    
    Attributes:
        shift_id (int): Unique identifier
        date (str): Date in YYYY-MM-DD format
        start_time (str): Start time (HH:MM)
        end_time (str): End time (HH:MM)
        role (str): Role type (any, regular, community, teen)
        site (str): Work site location
        max_volunteers (int): Maximum volunteer capacity
        assigned_volunteer (int): ID of assigned volunteer
        status (str): Shift status (pending, approved, denied, denied)
    
    Methods:
        assign_volunteer(): Assign volunteer to shift
        approve_request(): Approve shift request
        deny_request(): Deny shift request
    """
    
    def __init__(self, shift_id, date, start_time, end_time, role, site, max_volunteers=1):
        self.shift_id = shift_id
        self.date = date
        self.start_time = start_time
        self.end_time = end_time
        self.role = role
        self.site = site
        self.max_volunteers = max_volunteers
        self.assigned_volunteer = None
        self.status = "pending"
        self.signups = []  # List of signup IDs
    
    def assign_volunteer(self, volunteer_id, api_client=None):
        """Assign volunteer to shift."""
        self.assigned_volunteer = volunteer_id
        self.status = "assigned"
        if api_client:
            return api_client.post(f'/shifts/{self.shift_id}/assign', {
                'volunteer_id': volunteer_id
            })
        return True
    
    def approve_request(self, request_id, api_client=None):
        """Approve volunteer's shift request."""
        if api_client:
            return api_client.post(f'/signups/{request_id}/approve', {})
        return True
    
    def deny_request(self, request_id, api_client=None):
        """Deny volunteer's shift request."""
        if api_client:
            return api_client.post(f'/signups/{request_id}/deny', {})
        return True
    
    def __repr__(self):
        return f"Shift({self.shift_id}, {self.date} {self.start_time}-{self.end_time}, {self.site})"


class Admin:
    """
    Administrator user class with full system control.
    
    Attributes:
        admin_id (int): Unique identifier
        username (str): Login username
        password (str): Hashed password (bcrypt)
        name (str): Full name
    
    Methods:
        create_shift(): Create new shift
        edit_shift(): Edit existing shift
        approve_shift_request(): Approve volunteer's shift request
        approve_change_request(): Approve volunteer's change request
        view_all_schedules(): View all schedules
        finalize_week(): Lock week from further requests
    """
    
    def __init__(self, admin_id, username, name, password=""):
        self.admin_id = admin_id
        self.username = username
        self.name = name
        self.password = password  # Should be hashed
    
    def create_shift(self, date, start_time, end_time, role, site, max_vol, api_client=None):
        """Create new shift."""
        if api_client:
            return api_client.post('/shifts', {
                'date': date,
                'start_time': start_time,
                'end_time': end_time,
                'role': role,
                'site': site,
                'max_volunteers': max_vol
            })
        return None
    
    def edit_shift(self, shift_id, updates, api_client=None):
        """Edit existing shift."""
        if api_client:
            return api_client.put(f'/shifts/{shift_id}', updates)
        return None
    
    def approve_shift_request(self, request_id, api_client=None):
        """Approve volunteer's request to work shift."""
        if api_client:
            return api_client.post(f'/signups/{request_id}/approve', {})
        return True
    
    def approve_change_request(self, request_id, api_client=None):
        """Approve volunteer's request to change shift."""
        if api_client:
            return api_client.post(f'/change_requests/{request_id}/approve', {})
        return True
    
    def view_all_schedules(self, week_id=None, api_client=None):
        """View all schedules, optionally filtered by week."""
        if api_client:
            if week_id:
                return api_client.get(f'/weeks/{week_id}/shifts')
            else:
                return api_client.get('/shifts')
        return []
    
    def finalize_week(self, week_id, api_client=None):
        """Lock week from further shift requests."""
        if api_client:
            return api_client.post(f'/weeks/{week_id}/finalize', {})
        return True
    
    def __repr__(self):
        return f"Admin({self.admin_id}, {self.username})"
