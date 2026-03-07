import tkinter as tk
from tkinter import messagebox, ttk
import requests
from datetime import datetime

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


class VolunteerLoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Volunteer Login")

        tk.Label(self, text="Volunteer Login", font=("Arial", 16, "bold")).grid(
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
        tk.Button(self, text="Create Profile", width=12, command=self.open_register).grid(
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
                # Expecting user dict to include id, username, role, etc.
                self.open_dashboard(user)
            else:
                messagebox.showerror("Error", resp.json().get("error", "Login failed."))
        except Exception as e:
            messagebox.showerror("Error", f"Server error: {e}")

    def open_register(self):
        VolunteerRegisterDialog(self)

    def open_dashboard(self, volunteer_user):
        self.withdraw()
        dashboard = VolunteerMainWindow(self, volunteer_user)
        dashboard.protocol("WM_DELETE_WINDOW", self.on_dashboard_close)

    def on_dashboard_close(self):
        self.destroy()


class VolunteerRegisterDialog(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Volunteer Registration")

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

        tk.Label(self, text="Volunteer Type:").grid(row=len(labels), column=0, sticky="e", padx=5, pady=5)
        self.type_var = tk.StringVar()
        self.type_combo = ttk.Combobox(self, textvariable=self.type_var, state="readonly")
        self.type_combo['values'] = ("Regular Volunteer", "Teen Volunteer", "Community Service")
        self.type_combo.current(0)
        self.type_combo.grid(row=len(labels), column=1, padx=5, pady=5)

        tk.Button(self, text="Create Profile", command=self.create_profile).grid(
            row=len(labels) + 1, column=0, columnspan=2, pady=10
        )

    def create_profile(self):
        try:
            first_name, last_name, username, address, phone, password, confirm = [
                v.get().strip() for v in self.vars
            ]

            if not all([first_name, last_name, username, address, phone, password, confirm]):
                messagebox.showerror("Error", "All fields are required.")
                return

            if password != confirm:
                messagebox.showerror("Error", "Passwords do not match.")
                return

            type_map = {
                "Regular Volunteer": "regular",
                "Teen Volunteer": "teen",
                "Community Service": "community"
            }
            vol_type = type_map.get(self.type_var.get(), "regular")

            data = {
                "first_name": first_name,
                "last_name": last_name,
                "username": username,
                "address": address,
                "phone": phone,
                "password": password,
                "confirm_password": confirm,
                "role": "volunteer",
                "volunteer_type": vol_type,
            }

            resp = requests.post(f"{API_BASE}/register", json=data)
            if resp.status_code == 201:
                messagebox.showinfo("Success", "Volunteer profile created.")
                self.destroy()
            else:
                messagebox.showerror("Error", resp.json().get("error", "Registration failed."))
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")


class VolunteerMainWindow(tk.Toplevel):
    def __init__(self, master, volunteer_user):
        super().__init__(master)
        self.title(f"Volunteer Dashboard - {volunteer_user['username']}")
        self.volunteer_user = volunteer_user
        self.token = volunteer_user.get('token')  # Extract token from login response

        tk.Label(self, text="Volunteer Dashboard", font=("Arial", 16, "bold")).pack(pady=10)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)

        tk.Button(
            btn_frame,
            text="Plan Weekly Schedule",
            width=22,
            command=self.open_week_view,
        ).grid(row=0, column=0, padx=5, pady=5)

        tk.Button(
            btn_frame,
            text="View Approved Shifts",
            width=22,
            command=self.open_approved_shifts,
        ).grid(row=1, column=0, padx=5, pady=5)

        tk.Button(
            btn_frame,
            text="Submit Change Request",
            width=22,
            command=self.open_change_request,
        ).grid(row=2, column=0, padx=5, pady=5)

        tk.Button(
            btn_frame,
            text="View Weekly Hours",
            width=22,
            command=self.open_hours_view,
        ).grid(row=3, column=0, padx=5, pady=5)

        tk.Button(self, text="Logout", command=self.logout).pack(pady=10)

    def open_week_view(self):
        WeekScheduleView(self, self.volunteer_user, token=self.token)

    def open_approved_shifts(self):
        ApprovedShiftsWindow(self, self.volunteer_user, token=self.token)

    def open_change_request(self):
        ChangeRequestWindow(self, self.volunteer_user, token=self.token)

    def open_hours_view(self):
        WeeklyHoursWindow(self, self.volunteer_user, token=self.token)

    def logout(self):
        self.master.deiconify()
        self.destroy()


class WeekScheduleView(tk.Toplevel):
    def __init__(self, master, volunteer_user, token=None):
        super().__init__(master)
        self.title("Plan Weekly Schedule")
        self.volunteer_user = volunteer_user
        self.token = token

        tk.Label(self, text="Select Week:", font=("Arial", 12)).pack(pady=5)
        self.week_combo = ttk.Combobox(self, state="readonly", width=25)
        self.week_combo.pack(pady=5)
        self.week_combo.bind("<<ComboboxSelected>>", self.load_shifts_for_week)

        self.shifts_tree = ttk.Treeview(
            self,
            columns=("date", "start", "end", "site"),
            show="headings",
            height=12,
        )
        self.shifts_tree.heading("date", text="Date")
        self.shifts_tree.heading("start", text="Start")
        self.shifts_tree.heading("end", text="End")
        self.shifts_tree.heading("site", text="Site")
        self.shifts_tree.column("date", width=90)
        self.shifts_tree.column("start", width=70)
        self.shifts_tree.column("end", width=70)
        self.shifts_tree.column("site", width=200)
        self.shifts_tree.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=5)

        tk.Button(
            btn_frame,
            text="Request Selected Shift",
            command=self.request_selected_shift,
        ).grid(row=0, column=0, padx=5, pady=5)

        self.weeks = []
        self.sites = {}
        self.shifts_by_id = {}
        self.load_weeks()
        self.load_sites()

    def load_weeks(self):
        try:
            resp = make_request('GET', '/weeks', token=self.token)
            if resp.status_code == 200:
                self.weeks = resp.json()
                self.week_combo["values"] = [
                    f"{w['id']} - {w['week_start']}" for w in self.weeks
                ]
                display_values = []
                for w in self.weeks:
                    status = ""
                    if w.get('is_finalized'):
                        status = " (Finalized)"
                    elif w.get('finalization_deadline'):
                        try:
                            deadline = datetime.strptime(w['finalization_deadline'], "%Y-%m-%d")
                            if datetime.now().date() > deadline.date():
                                status = " (Closed)"
                        except ValueError:
                            pass
                    display_values.append(f"{w['id']} - {w['week_start']}{status}")
                self.week_combo["values"] = display_values
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load weeks: {e}")

    def load_sites(self):
        try:
            resp = make_request('GET', '/sites', token=self.token)
            if resp.status_code == 200:
                sites_list = resp.json()
                self.sites = {s["id"]: s["site_name"] for s in sites_list}
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load sites: {e}")

    def load_shifts_for_week(self, event=None):
        for row in self.shifts_tree.get_children():
            self.shifts_tree.delete(row)
        self.shifts_by_id.clear()

        if not self.week_combo.get():
            return

        week_id = int(self.week_combo.get().split(" - ")[0])

        try:
            resp = make_request('GET', f'/weeks/{week_id}/shifts', token=self.token)
            if resp.status_code == 200:
                shifts = resp.json()
                my_type = self.volunteer_user.get("volunteer_type", "regular")
                for shift in shifts:
                    shift_id = shift["id"]
                    shift_role = shift.get("role", "any")
                    # Filter by shift role: allow if 'any' or matches volunteer type
                    if shift_role != "any" and shift_role != my_type:
                        continue
                    # Hide full shifts (first-come, first-served)
                    current = shift.get("current_signups", 0)
                    maxv = shift.get("max_volunteers", 1)
                    if current >= maxv:
                        # mark as full and skip
                        continue
                    self.shifts_by_id[shift_id] = shift
                    date = shift["date"]
                    start = shift["start_time"]
                    end = shift["end_time"]
                    site_name = self.sites.get(shift["site_id"], f"Site {shift['site_id']}")
                    self.shifts_tree.insert(
                        "",
                        tk.END,
                        iid=str(shift_id),
                        values=(date, start, end, site_name),
                    )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load shifts: {e}")

    def request_selected_shift(self):
        selected = self.shifts_tree.selection()
        if not selected:
            messagebox.showerror("Error", "Select a shift to request.")
            return

        if self.week_combo.get():
            week_id = int(self.week_combo.get().split(" - ")[0])
            week_obj = next((w for w in self.weeks if w['id'] == week_id), None)
            if week_obj:
                if week_obj.get('is_finalized'):
                    messagebox.showerror("Error", "This week is finalized. No new requests allowed.")
                    return
                
                if week_obj.get('finalization_deadline'):
                    try:
                        deadline = datetime.strptime(week_obj['finalization_deadline'], "%Y-%m-%d")
                        if datetime.now().date() > deadline.date():
                            messagebox.showerror("Error", "The deadline for this week has passed.")
                            return
                    except ValueError:
                        pass

        shift_id = int(selected[0])
        shift = self.shifts_by_id.get(shift_id)
        if not shift:
            messagebox.showerror("Error", "Shift not found.")
            return

        data = {
            "volunteer_id": self.volunteer_user["id"],
            "shift_id": shift_id,
            "status": "pending",
        }

        try:
            resp = make_request('POST', '/shift_requests', token=self.token, json=data)
            if resp.status_code == 201:
                messagebox.showinfo("Success", "Shift request submitted.")
            else:
                messagebox.showerror(
                    "Error", resp.json().get("error", "Failed to submit request.")
                )
        except Exception as e:
            messagebox.showerror("Error", f"Server error: {e}")


class ApprovedShiftsWindow(tk.Toplevel):
    def __init__(self, master, volunteer_user, token=None):
        super().__init__(master)
        self.title("Approved Shifts")
        self.volunteer_user = volunteer_user
        self.token = token

        self.tree = ttk.Treeview(
            self,
            columns=("shift_id", "week", "date", "start", "end", "site"),
            show="headings",
            height=12,
        )
        self.tree.heading("shift_id", text="Shift ID")
        self.tree.heading("week", text="Week Start")
        self.tree.heading("date", text="Date")
        self.tree.heading("start", text="Start")
        self.tree.heading("end", text="End")
        self.tree.heading("site", text="Site")
        self.tree.column("shift_id", width=60)
        self.tree.column("week", width=90)
        self.tree.column("date", width=90)
        self.tree.column("start", width=70)
        self.tree.column("end", width=70)
        self.tree.column("site", width=200)
        self.tree.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.sites = {}
        self.load_sites()
        self.load_approved_shifts()

    def load_sites(self):
        try:
            resp = make_request('GET', '/sites', token=self.token)
            if resp.status_code == 200:
                sites_list = resp.json()
                self.sites = {s["id"]: s["site_name"] for s in sites_list}
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load sites: {e}")

    def load_approved_shifts(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        try:
            resp = make_request('GET', f"/volunteers/{self.volunteer_user['id']}/approved_shifts", token=self.token)
            if resp.status_code == 200:
                shifts = resp.json()
                for s in shifts:
                    shift_id = s.get("shift_id", "")
                    week_start = s.get("week_start", "")
                    date = s["date"]
                    start = s["start_time"]
                    end = s["end_time"]
                    site_name = self.sites.get(s["site_id"], f"Site {s['site_id']}")
                    self.tree.insert(
                        "",
                        tk.END,
                        values=(shift_id, week_start, date, start, end, site_name),
                    )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load approved shifts: {e}")


class ChangeRequestWindow(tk.Toplevel):
    def __init__(self, master, volunteer_user, token=None):
        super().__init__(master)
        self.title("Submit Change Request")
        self.volunteer_user = volunteer_user
        self.token = token

        tk.Label(self, text="Shift ID:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        tk.Label(self, text="Reason / Details:").grid(row=1, column=0, sticky="ne", padx=5, pady=5)

        self.shift_id_var = tk.StringVar()
        tk.Entry(self, textvariable=self.shift_id_var).grid(row=0, column=1, padx=5, pady=5)

        self.reason_text = tk.Text(self, width=40, height=6)
        self.reason_text.grid(row=1, column=1, padx=5, pady=5)

        tk.Button(self, text="Submit Change Request", command=self.submit_request).grid(
            row=2, column=0, columnspan=2, pady=10
        )

    def submit_request(self):
        shift_id_str = self.shift_id_var.get().strip()
        reason = self.reason_text.get("1.0", tk.END).strip()

        if not shift_id_str or not reason:
            messagebox.showerror("Error", "Shift ID and reason are required.")
            return

        try:
            shift_id = int(shift_id_str)
        except ValueError:
            messagebox.showerror("Error", "Shift ID must be a number.")
            return

        data = {
            "volunteer_id": self.volunteer_user["id"],
            "shift_id": shift_id,
            "reason": reason,
        }

        try:
            resp = make_request('POST', '/change_requests', token=self.token, json=data)
            if resp.status_code == 201:
                messagebox.showinfo("Success", "Change request submitted.")
                self.destroy()
            else:
                messagebox.showerror(
                    "Error", resp.json().get("error", "Failed to submit change request.")
                )
        except Exception as e:
            messagebox.showerror("Error", f"Server error: {e}")


class WeeklyHoursWindow(tk.Toplevel):
    def __init__(self, master, volunteer_user, token=None):
        super().__init__(master)
        self.title("Weekly Hours")
        self.volunteer_user = volunteer_user
        self.token = token

        tk.Label(self, text="Select Week:", font=("Arial", 12)).pack(pady=5)
        self.week_combo = ttk.Combobox(self, state="readonly", width=25)
        self.week_combo.pack(pady=5)

        tk.Button(self, text="Load Hours", command=self.load_hours).pack(pady=5)

        self.hours_label = tk.Label(self, text="", font=("Arial", 12))
        self.hours_label.pack(pady=10)

        self.weeks = []
        self.load_weeks()

    def load_weeks(self):
        try:
            resp = make_request('GET', '/weeks', token=self.token)
            if resp.status_code == 200:
                self.weeks = resp.json()
                self.week_combo["values"] = [
                    f"{w['id']} - {w['week_start']}" for w in self.weeks
                ]
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load weeks: {e}")

    def load_hours(self):
        if not self.week_combo.get():
            messagebox.showerror("Error", "Select a week.")
            return

        week_id = int(self.week_combo.get().split(" - ")[0])

        try:
            resp = make_request('GET', f"/volunteers/{self.volunteer_user['id']}/hours", token=self.token, params={"week_id": week_id})
            if resp.status_code == 200:
                data = resp.json()
                total_hours = data.get("total_hours", 0)
                self.hours_label.config(
                    text=f"Total hours for selected week: {total_hours:.2f}"
                )
            else:
                messagebox.showerror(
                    "Error", resp.json().get("error", "Failed to load hours.")
                )
        except Exception as e:
            messagebox.showerror("Error", f"Server error: {e}")


if __name__ == "__main__":
    app = VolunteerLoginWindow()
    app.mainloop()
    #