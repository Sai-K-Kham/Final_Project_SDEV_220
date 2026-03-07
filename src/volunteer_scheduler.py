"""
Volunteer Scheduler - Main Entry Point

This script launches the Volunteer Scheduling and Shift Management System.
It initializes and runs the Launcher window which routes users to Admin or Volunteer interfaces.
"""

import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from launcher import Launcher


if __name__ == "__main__":
    app = Launcher()
    app.mainloop()