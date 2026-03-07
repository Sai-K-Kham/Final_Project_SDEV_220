"""
Launcher Module
Provides the main entry point GUI for selecting Admin or Volunteer interfaces.
"""

import subprocess
import sys
import os
import tkinter as tk

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON = sys.executable

API_FILE = os.path.join(BASE_DIR, "api.py")
ADMIN_GUI = os.path.join(BASE_DIR, "admin_gui.py")
VOL_GUI = os.path.join(BASE_DIR, "volunteer_gui.py")
DATABASE_INIT = os.path.join(BASE_DIR, "database.py")


class Launcher(tk.Tk):
    """
    Launcher window for Volunteer Scheduler system.
    
    Provides buttons for Admin and Volunteer login.
    Automatically initializes database and starts API server.
    """
    
    def __init__(self):
        super().__init__()
        self.title("Volunteer Scheduler Launcher")
        self.geometry("400x300")
        
        # Automatically initialize database
        subprocess.Popen([PYTHON, DATABASE_INIT], cwd=BASE_DIR).wait()

        # Automatically start API server
        self.api_process = subprocess.Popen([PYTHON, API_FILE], cwd=BASE_DIR)

        # Create UI elements
        tk.Label(self, text="Volunteer Scheduler", font=("Arial", 18, "bold")).pack(pady=15)
        tk.Label(self, text="Select your role:", font=("Arial", 12)).pack(pady=10)

        tk.Button(
            self, 
            text="Admin Login", 
            width=25, 
            bg="#4CAF50",
            fg="white",
            command=self.start_admin_gui
        ).pack(pady=5)
        
        tk.Button(
            self, 
            text="Volunteer Login", 
            width=25,
            bg="#2196F3",
            fg="white", 
            command=self.start_volunteer_gui
        ).pack(pady=5)

        tk.Button(
            self, 
            text="Exit", 
            width=25,
            bg="#f44336",
            fg="white",
            command=self.close_all
        ).pack(pady=15)

    def start_admin_gui(self):
        """Launch admin interface."""
        subprocess.Popen([PYTHON, ADMIN_GUI], cwd=BASE_DIR)

    def start_volunteer_gui(self):
        """Launch volunteer interface."""
        subprocess.Popen([PYTHON, VOL_GUI], cwd=BASE_DIR)

    def close_all(self):
        """Close launcher and terminate API server."""
        if self.api_process:
            self.api_process.terminate()
        self.destroy()


if __name__ == "__main__":
    app = Launcher()
    app.mainloop()
