import tkinter as tk
from tkinter import messagebox, ttk
import requests
from datetime import datetime, timedelta

API_BASE = "http://127.0.0.1:5000"


def make_request(method, endpoint, token=None, json=None, params=None):
    """Helper function to make API requests with Authorization header"""
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    url = f"{API_BASE}{endpoint}"
    
    if method == 'GET':
        return requests.get(url, headers=headers, params=params)
    elif method == 'POST':
        return requests.post(url, headers=headers, json=json)
    elif method == 'PUT':
        return requests.put(url, headers=headers, json=json)
    elif method == 'DELETE':
        return requests.delete(url, headers=headers)
    else:
        raise ValueError(f"Unsupported method: {method}")


class AdminLoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Admin Login")

        tk.Label(self, text="Admin Login", font=("Arial", 16, "bold")).grid(
            row=0, column=0, columnspan=2, pady=10
        )

        tk.Label(self, text="Username:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        tk.Label(self, text="Password:").grid(row=2, column=0, sticky="e", padx=5, pady=5)

        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()

        tk.Entry(self, textvariable=self.username_var).grid(row=1, column=1, padx=5, pady=5)
        tk.Entry(self, textvariable=self.password_var, show="*").grid(row=2, column=1, padx=5, pady=5)

        tk.Button(self, text="Login", width=12, command=self.login).grid(
            row=3, column=0, padx=5, pady=10
        )
        tk.Button(self, text="Create Account", width=12, command=self.open_register).grid(
            row=3, column=1, padx=5, pady=10
        )

    def login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()

        if not username or not password:
            messagebox.showerror("Error", "Username and password are required.")
            return

        data = {"username": username, "password": password}

        try:
            resp = requests.post(f"{API_BASE}/login", json=data)
            if resp.status_code == 200:
                user = resp.json()
                self.open_dashboard(user)
            else:
                messagebox.showerror("Error", resp.json().get("error", "Login failed."))
        except Exception as e:
            messagebox.showerror("Error", f"Server error: {e}")

    def open_register(self):
        AdminRegisterDialog(self)

    def open_dashboard(self, admin_user):
        self.withdraw()
        dashboard = AdminMainWindow(self, admin_user)
        dashboard.protocol("WM_DELETE_WINDOW", self.on_dashboard_close)

    def on_dashboard_close(self):
        self.destroy()


class AdminRegisterDialog(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Admin Registration")

        labels = [
            "First Name:",
            "Last Name:",
            "Username:",
            "Address:",
            "Phone:",
            "Password:",
            "Confirm Password:",
        ]
        self.vars = [tk.StringVar() for _ in labels]

        for i, text in enumerate(labels):
            tk.Label(self, text=text).grid(row=i, column=0, sticky="e", padx=5, pady=5)
            show = "*" if "Password" in text else None
            tk.Entry(self, textvariable=self.vars[i], show=show).grid(row=i, column=1, padx=5, pady=5)

        tk.Button(self, text="Create Account", command=self.create_account).grid(
            row=len(labels), column=0, columnspan=2, pady=10
        )

    def create_account(self):
        first_name, last_name, username, address, phone, password, confirm = [
            v.get().strip() for v in self.vars
        ]

        if not all([first_name, last_name, username, address, phone, password, confirm]):
            messagebox.showerror("Error", "All fields are required.")
            return

        if password != confirm:
            messagebox.showerror("Error", "Passwords do not match.")
            return

        data = {
            "first_name": first_name,
            "last_name": last_name,
            "username": username,
            "address": address,
            "phone": phone,
            "password": password,
            "confirm_password": confirm,
            "role": "admin",
            "volunteer_type": "regular",
        }

        try:
            resp = requests.post(f"{API_BASE}/register", json=data)
            if resp.status_code == 201:
                messagebox.showinfo("Success", "Admin account created.")
                self.destroy()
            else:
                messagebox.showerror("Error", resp.json().get("error", "Registration failed."))
        except Exception as e:
            messagebox.showerror("Error", f"Server error: {e}")


class AdminMainWindow(tk.Toplevel):
    def __init__(self, master, admin_user):
        super().__init__(master)
        self.title(f"Admin Dashboard - {admin_user['username']}")
        self.admin_user = admin_user
        self.token = admin_user.get('token')  # Extract token from login response

        tk.Label(self, text="Admin Dashboard", font=("Arial", 16, "bold")).pack(pady=10)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)

        tk.Button(
            btn_frame,
            text="Manage Weekly Schedule",
            width=22,
            command=self.open_week_scheduler,
        ).grid(row=0, column=0, padx=5, pady=5)

        # Placeholders for later features (approvals, change requests)
        tk.Button(
            btn_frame,
            text="View Pending Signups",
            width=22,
            command=self.open_pending_signups,
        ).grid(row=1, column=0, padx=5, pady=5)
        tk.Button(
            btn_frame,
            text="View Change Requests",
            width=22,
            command=self.open_change_requests,
        ).grid(row=2, column=0, padx=5, pady=5)
        tk.Button(
            btn_frame,
            text="View All Volunteers",
            width=22,
            command=self.open_volunteers,
        ).grid(row=3, column=0, padx=5, pady=5)

        tk.Button(self, text="Close", command=self.close_all).pack(pady=10)

    def open_week_scheduler(self):
        WeekSchedulerWindow(self, self.token)

    def open_pending_signups(self):
        PendingSignupsWindow(self, self.token)

    def close_all(self):
        self.master.destroy()

    def open_change_requests(self):
        ChangeRequestsAdminWindow(self, self.token)

    def open_volunteers(self):
        VolunteersAdminWindow(self, self.token)


class WeekSchedulerWindow(tk.Toplevel):
    def __init__(self, master, token):
        super().__init__(master)
        self.title("Weekly Scheduler")
        self.token = token

        self.days = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        self.day_frames = {}
        self.shift_lists = {}
        self.start_vars = {}
        self.end_vars = {}
        self.site_vars = {}
        self.site_menus = {}
        self.role_vars = {}
        self.add_buttons = {}

        tk.Label(self, text="Select Week:", font=("Arial", 12)).pack(pady=5)
        self.week_combo = ttk.Combobox(self, state="readonly", width=25)
        self.week_combo.pack(pady=5)
        self.week_combo.bind("<<ComboboxSelected>>", self.load_week_shifts)

        top_frame = tk.Frame(self)
        top_frame.pack(pady=5)

        tk.Button(top_frame, text="Create New Week", command=self.create_new_week).pack(
            side=tk.LEFT, padx=5
        )
        tk.Button(top_frame, text="Publish Week", command=self.publish_selected_week).pack(
            side=tk.LEFT, padx=5
        )
        tk.Button(top_frame, text="Finalize Week", command=self.finalize_selected_week).pack(
            side=tk.LEFT, padx=5
        )

        self.grid_frame = tk.Frame(self)
        self.grid_frame.pack(pady=10)

        for i, day in enumerate(self.days):
            frame = tk.LabelFrame(self.grid_frame, text=day, padx=5, pady=5)
            frame.grid(row=0, column=i, padx=5, pady=5)
            self.day_frames[day] = frame

            shift_list = tk.Listbox(frame, width=22, height=10)
            shift_list.pack()
            self.shift_lists[day] = shift_list

            # Site dropdown
            tk.Label(frame, text="Site:").pack()
            site_var = tk.StringVar()
            site_menu = ttk.Combobox(frame, textvariable=site_var, state="readonly", width=20)
            site_menu.pack()
            self.site_vars[day] = site_var
            self.site_menus[day] = site_menu

            # Start time
            tk.Label(frame, text="Start:").pack()
            start_var = tk.StringVar()
            start_menu = ttk.Combobox(
                frame, textvariable=start_var, values=self.generate_times(), width=10
            )
            start_menu.pack()
            self.start_vars[day] = start_var

            # End time
            tk.Label(frame, text="End:").pack()
            end_var = tk.StringVar()
            end_menu = ttk.Combobox(
                frame, textvariable=end_var, values=self.generate_times(), width=10
            )
            end_menu.pack()
            self.end_vars[day] = end_var

            # Role required for this shift
            tk.Label(frame, text="Role:").pack()
            role_var = tk.StringVar()
            role_menu = ttk.Combobox(
                frame,
                textvariable=role_var,
                values=["any", "regular", "community", "teen"],
                state="readonly",
                width=18,
            )
            role_menu.set("any")
            role_menu.pack()
            self.role_vars[day] = role_var

            btn = tk.Button(frame, text="Add Shift", command=lambda d=day: self.add_shift(d))
            btn.pack(pady=5)
            self.add_buttons[day] = btn

        self.weeks = []
        self.sites = []
        self.load_weeks()
        self.load_sites()

    def generate_times(self):
        times = []
        for h in range(6, 23):
            times.append(f"{h:02d}:00")
            times.append(f"{h:02d}:30")
        return times

    def load_weeks(self):
        try:
            resp = make_request('GET', '/weeks', token=self.token)
            if resp.status_code == 200:
                self.weeks = resp.json()
                self.week_combo["values"] = [
                    f"{w['id']} - {w['week_start']}{' (Finalized)' if w.get('is_finalized') else ''}" for w in self.weeks
                ]
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load weeks: {e}")

    def load_sites(self):
        try:
            resp = make_request('GET', '/sites', token=self.token)
            if resp.status_code == 200:
                self.sites = resp.json()
                site_names = [f"{s['id']} - {s['site_name']}" for s in self.sites]
                for menu in self.site_menus.values():
                    menu["values"] = site_names
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load sites: {e}")

    def create_new_week(self):
        WeekCreateDialog(self, token=self.token, on_created=self.on_week_created)

    def on_week_created(self):
        self.load_weeks()

    def load_week_shifts(self, event=None):
        for lst in self.shift_lists.values():
            lst.delete(0, tk.END)

        if not self.week_combo.get():
            return

        week_id = int(self.week_combo.get().split(" - ")[0])
        # find week metadata
        week_obj = next((w for w in self.weeks if w.get('id') == week_id), None)
        is_final = bool(week_obj.get('is_finalized')) if week_obj else False
        # enable/disable add buttons depending on finalization
        for d, b in self.add_buttons.items():
            try:
                b['state'] = 'disabled' if is_final else 'normal'
            except Exception:
                pass

        try:
            resp = make_request('GET', f'/weeks/{week_id}/shifts', token=self.token)
            if resp.status_code == 200:
                shifts = resp.json()
                for shift in shifts:
                    day_name = self.days[
                        datetime.strptime(shift["date"], "%Y-%m-%d").weekday()
                    ]
                    role = shift.get("role", "any")
                    entry = (
                        f"{shift['start_time']} - {shift['end_time']} "
                        f"(Site {shift['site_id']}) [{role}]"
                    )
                    self.shift_lists[day_name].insert(tk.END, entry)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load shifts: {e}")

    def add_shift(self, day):
        if not self.week_combo.get():
            messagebox.showerror("Error", "Select a week first.")
            return

        week_id = int(self.week_combo.get().split(" - ")[0])
        # Clean the week string to remove "(Finalized)" text before parsing
        week_start_str_full = self.week_combo.get().split(" - ")[1]
        week_start_str = week_start_str_full.split(" (")[0]

        try:
            week_start = datetime.strptime(week_start_str.strip(), "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Error", "Invalid week start date format.")
            return

        day_index = self.days.index(day)
        date = (week_start + timedelta(days=day_index)).strftime("%Y-%m-%d")

        start = self.start_vars[day].get()
        end = self.end_vars[day].get()

        if not start or not end:
            messagebox.showerror("Error", "Select start and end times.")
            return

        # Get selected site for this day
        site_choice = self.site_vars[day].get()
        if not site_choice:
            messagebox.showerror("Error", "Select a site.")
            return

        site_id = int(site_choice.split(" - ")[0])

        data = {
            "week_id": week_id,
            "site_id": site_id,
            "role": self.role_vars[day].get() or "any",
            "date": date,
            "start_time": start,
            "end_time": end,
            "max_volunteers": 5,
        }

        try:
            resp = make_request('POST', '/shifts', token=self.token, json=data)
            if resp.status_code == 201:
                self.shift_lists[day].insert(
                    tk.END, f"{start} - {end} (Site {site_id})"
                )
            else:
                messagebox.showerror(
                    "Error", resp.json().get("error", "Failed to add shift.")
                )
        except Exception as e:
            messagebox.showerror("Error", f"Server error: {e}")

    def publish_selected_week(self):
        if not self.week_combo.get():
            messagebox.showerror("Error", "Select a week first.")
            return
        
        week_id = int(self.week_combo.get().split(" - ")[0])
        
        if messagebox.askyesno("Confirm", "Are you sure you want to publish this week? Volunteers will be able to view it."):
            try:
                resp = make_request('POST', f'/weeks/{week_id}/publish', token=self.token)
                if resp.status_code == 200:
                    messagebox.showinfo("Success", "Week published successfully.")
                    self.load_weeks()
                else:
                    messagebox.showerror("Error", resp.json().get("error", "Failed to publish week."))
            except Exception as e:
                messagebox.showerror("Error", f"Server error: {e}")

    def finalize_selected_week(self):
        if not self.week_combo.get():
            messagebox.showerror("Error", "Select a week first.")
            return
        
        week_id = int(self.week_combo.get().split(" - ")[0])
        
        if messagebox.askyesno("Confirm", "Are you sure you want to finalize this week? No further changes will be allowed."):
            try:
                resp = make_request('POST', f'/weeks/{week_id}/finalize', token=self.token)
                if resp.status_code == 200:
                    messagebox.showinfo("Success", "Week finalized successfully.")
                    self.load_weeks()
                else:
                    messagebox.showerror("Error", resp.json().get("error", "Failed to finalize week."))
            except Exception as e:
                messagebox.showerror("Error", f"Server error: {e}")


class WeekCreateDialog(tk.Toplevel):
    def __init__(self, master, token=None, on_created=None):
        super().__init__(master)
        self.title("Create Week")
        self.token = token
        self.on_created = on_created

        tk.Label(self, text="Week Start (YYYY-MM-DD):").grid(
            row=0, column=0, sticky="e", padx=5, pady=5
        )
        tk.Label(self, text="Finalization Deadline (YYYY-MM-DD):").grid(
            row=1, column=0, sticky="e", padx=5, pady=5
        )

        self.week_start_var = tk.StringVar()
        self.deadline_var = tk.StringVar()

        tk.Entry(self, textvariable=self.week_start_var).grid(
            row=0, column=1, padx=5, pady=5
        )
        tk.Entry(self, textvariable=self.deadline_var).grid(
            row=1, column=1, padx=5, pady=5
        )

        tk.Button(self, text="Create Week", command=self.create_week).grid(
            row=2, column=0, columnspan=2, pady=10
        )

    def create_week(self):
        week_start = self.week_start_var.get().strip()
        deadline = self.deadline_var.get().strip()

        if not week_start or not deadline:
            messagebox.showerror("Error", "Both fields are required.")
            return

        data = {"week_start": week_start, "finalization_deadline": deadline}

        try:
            resp = make_request('POST', '/weeks', token=self.token, json=data)
            if resp.status_code == 201:
                messagebox.showinfo("Success", "Week created successfully.")
                if self.on_created:
                    self.on_created()
                self.destroy()
            else:
                messagebox.showerror(
                    "Error", resp.json().get("error", "Failed to create week.")
                )
        except Exception as e:
            messagebox.showerror("Error", f"Server error: {e}")


class PendingSignupsWindow(tk.Toplevel):
    def __init__(self, master, token=None):
        super().__init__(master)
        self.title("Pending Signups")
        self.token = token

        self.tree = ttk.Treeview(
            self,
            columns=("signup", "volunteer", "date", "start", "end", "site", "status"),
            show="headings",
            height=12,
        )
        self.tree.heading("signup", text="Signup ID")
        self.tree.heading("volunteer", text="Volunteer")
        self.tree.heading("date", text="Date")
        self.tree.heading("start", text="Start")
        self.tree.heading("end", text="End")
        self.tree.heading("site", text="Site")
        self.tree.heading("status", text="Status")

        for col in ("signup", "volunteer", "date", "start", "end", "site", "status"):
            self.tree.column(col, width=100)

        self.tree.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=5)

        tk.Button(btn_frame, text="Approve", command=self.approve_selected).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Deny", command=self.deny_selected).grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="Refresh", command=self.load_pending).grid(row=0, column=2, padx=5)

        self.load_pending()

    def load_pending(self):
        for r in self.tree.get_children():
            self.tree.delete(r)

        try:
            resp = make_request('GET', '/signups/pending', token=self.token)
            if resp.status_code == 200:
                rows = resp.json()
                for row in rows:
                    sid = row.get("signup_id")
                    volunteer = row.get("volunteer_username") or row.get("volunteer_id")
                    date = row.get("date")
                    start = row.get("start_time") or row.get("start") or row.get("start_time")
                    end = row.get("end_time") or row.get("end") or row.get("end_time")
                    site = row.get("site_name") or f"Site {row.get('site_id')}"
                    status = row.get("status")
                    self.tree.insert("", tk.END, iid=str(sid), values=(sid, volunteer, date, start, end, site, status))
            else:
                messagebox.showerror("Error", resp.json().get("error", "Failed to load pending signups."))
        except Exception as e:
            messagebox.showerror("Error", f"Server error: {e}")

    def approve_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showerror("Error", "Select a signup to approve.")
            return
        signup_id = int(sel[0])
        try:
            resp = make_request('POST', f'/signups/{signup_id}/approve', token=self.token)
            if resp.status_code == 200:
                messagebox.showinfo("Success", "Signup approved.")
                self.load_pending()
            else:
                messagebox.showerror("Error", resp.json().get("error", "Failed to approve signup."))
        except Exception as e:
            messagebox.showerror("Error", f"Server error: {e}")

    def deny_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showerror("Error", "Select a signup to deny.")
            return
        signup_id = int(sel[0])
        try:
            resp = make_request('POST', f'/signups/{signup_id}/deny', token=self.token)
            if resp.status_code == 200:
                messagebox.showinfo("Success", "Signup denied.")
                self.load_pending()
            else:
                messagebox.showerror("Error", resp.json().get("error", "Failed to deny signup."))
        except Exception as e:
            messagebox.showerror("Error", f"Server error: {e}")


class ChangeRequestsAdminWindow(tk.Toplevel):
    def __init__(self, master, token=None):
        super().__init__(master)
        self.title("Change Requests")
        self.token = token

        cols = (
            "id",
            "volunteer",
            "type",
            "from_shift",
            "to_shift",
            "new_start",
            "new_end",
            "reason",
            "status",
        )

        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=14)
        headings = {
            "id": "Req ID",
            "volunteer": "Volunteer",
            "type": "Type",
            "from_shift": "From Shift",
            "to_shift": "To Shift",
            "new_start": "New Start",
            "new_end": "New End",
            "reason": "Reason",
            "status": "Status",
        }
        for c in cols:
            self.tree.heading(c, text=headings[c])
            self.tree.column(c, width=100)

        self.tree.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=6)

        tk.Button(btn_frame, text="Approve", command=self.approve_selected).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Deny", command=self.deny_selected).grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="Refresh", command=self.load_requests).grid(row=0, column=2, padx=5)

        self.load_requests()

    def load_requests(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        try:
            resp = make_request('GET', '/change_requests/pending', token=self.token)
            if resp.status_code == 200:
                rows = resp.json()
                for row in rows:
                    rid = row.get("request_id")
                    vol = row.get("volunteer_username") or row.get("volunteer_id")
                    ctype = row.get("change_type")
                    from_shift = row.get("from_shift_id")
                    to_shift = row.get("to_shift_id")
                    ns = row.get("new_start_time")
                    ne = row.get("new_end_time")
                    reason = (row.get("reason") or "")[:80]
                    status = row.get("status")
                    self.tree.insert("", tk.END, iid=str(rid), values=(rid, vol, ctype, from_shift, to_shift, ns, ne, reason, status))
            else:
                messagebox.showerror("Error", resp.json().get("error", "Failed to load change requests."))
        except Exception as e:
            messagebox.showerror("Error", f"Server error: {e}")

    def approve_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showerror("Error", "Select a request to approve.")
            return
        req_id = int(sel[0])
        try:
            resp = make_request('POST', f'/change_requests/{req_id}/approve', token=self.token)
            if resp.status_code == 200:
                messagebox.showinfo("Success", "Change request approved.")
                self.load_requests()
            else:
                messagebox.showerror("Error", resp.json().get("error", "Failed to approve request."))
        except Exception as e:
            messagebox.showerror("Error", f"Server error: {e}")

    def deny_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showerror("Error", "Select a request to deny.")
            return
        req_id = int(sel[0])
        try:
            resp = make_request('POST', f'/change_requests/{req_id}/deny', token=self.token)
            if resp.status_code == 200:
                messagebox.showinfo("Success", "Change request denied.")
                self.load_requests()
            else:
                messagebox.showerror("Error", resp.json().get("error", "Failed to deny request."))
        except Exception as e:
            messagebox.showerror("Error", f"Server error: {e}")

class VolunteersAdminWindow(tk.Toplevel):
    def __init__(self, master, token=None):
        super().__init__(master)
        self.title("Volunteers")
        self.token = token

        self.tree = ttk.Treeview(self, columns=("id","username","name","role","type","availability"), show="headings", height=16)
        self.tree.heading("id", text="ID")
        self.tree.heading("username", text="Username")
        self.tree.heading("name", text="Name")
        self.tree.heading("role", text="Role")
        self.tree.heading("type", text="Type")
        self.tree.heading("availability", text="Availability")
        for c in ("id","username","name","role","type","availability"):
            self.tree.column(c, width=120)
        self.tree.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=6)
        tk.Button(btn_frame, text="Refresh", command=self.load_volunteers).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Edit Availability", command=self.edit_availability).pack(side=tk.LEFT, padx=5)

        self.load_volunteers()

    def load_volunteers(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        try:
            resp = make_request('GET', '/volunteers', token=self.token)
            if resp.status_code == 200:
                rows = resp.json()
                for row in rows:
                    vid = row.get("id")
                    username = row.get("username")
                    name = f"{row.get('first_name','')} {row.get('last_name','')}"
                    role = row.get("role")
                    vtype = row.get("volunteer_type")
                    avail = row.get("availability") or ""
                    self.tree.insert("", tk.END, iid=str(vid), values=(vid, username, name, role, vtype, avail))
            else:
                messagebox.showerror("Error", resp.json().get("error", "Failed to load volunteers."))
        except Exception as e:
            messagebox.showerror("Error", f"Server error: {e}")

    def edit_availability(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showerror("Error", "Select a volunteer to edit.")
            return
        vid = int(sel[0])
        EditAvailabilityDialog(self, vid, self.token, on_saved=self.load_volunteers)


class EditAvailabilityDialog(tk.Toplevel):
    def __init__(self, master, volunteer_id, token, on_saved=None):
        super().__init__(master)
        self.volunteer_id = volunteer_id
        self.token = token
        self.on_saved = on_saved
        self.title("Edit Availability")

        tk.Label(self, text="Availability (freeform):").pack(padx=10, pady=5)
        self.txt = tk.Text(self, width=50, height=8)
        self.txt.pack(padx=10, pady=5)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=6)
        tk.Button(btn_frame, text="Load", command=self.load).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Save", command=self.save).pack(side=tk.LEFT, padx=5)

    def load(self):
        try:
            resp = make_request('GET', f'/volunteers/{self.volunteer_id}', token=self.token)
            if resp.status_code == 200:
                data = resp.json()
                self.txt.delete('1.0', tk.END)
                self.txt.insert(tk.END, data.get('availability') or '')
            else:
                messagebox.showerror("Error", "Failed to load volunteer.")
        except Exception as e:
            messagebox.showerror("Error", f"Server error: {e}")

    def save(self):
        avail = self.txt.get('1.0', tk.END).strip()
        try:
            resp = make_request('POST', f'/volunteers/{self.volunteer_id}/availability', token=self.token, json={'availability': avail})
            if resp.status_code == 200:
                messagebox.showinfo("Saved", "Availability updated.")
                if self.on_saved:
                    self.on_saved()
                self.destroy()
            else:
                messagebox.showerror("Error", resp.json().get('error', 'Failed to save.'))
        except Exception as e:
            messagebox.showerror("Error", f"Server error: {e}")


if __name__ == "__main__":
    app = AdminLoginWindow()
    app.mainloop()