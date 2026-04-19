import json
import os
from datetime import datetime, timezone
import sys

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class LogHandler:
    def __init__(self):
        self.logs_dir = os.path.join(BASE_DIR, "config\logs")
        self.current_session_file = None
        os.makedirs(self.logs_dir, exist_ok=True)

    def start_session(self):
        now = datetime.now(timezone.utc)
        filename = now.strftime("%d.%m.%Y-%H.%M.json")
        self.current_session_file = os.path.join(self.logs_dir, filename)
        
        self._write_logs([])
        
        print(f"Session started: {filename}")
        return self.current_session_file
    
    def end_session(self):
        if self.current_session_file:
            print(f"Session ended: {os.path.basename(self.current_session_file)}")
        self.current_session_file = None

    def add_log(self, category: str, message: str):
        """
        Adds a log entry to the current session file.
        If no session is active, a new one is started automatically.
        
        Format: "category;message"
        Categories: app, system, bot, travel, market
        """
        if not self.current_session_file:
            self.start_session()
        log_entry = f"{category};{message}"
        
        try:
            logs = self._read_logs()
            logs.append(log_entry)
            self._write_logs(logs)
        except Exception as e:
            print(f"Logger Error: Failed to add log '{log_entry}': {e}")

    def _read_logs(self):
        """Helper to safely read logs from the current session file."""
        if os.path.exists(self.current_session_file):
            try:
                with open(self.current_session_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if not content: return []
                    return json.loads(content)
            except (json.JSONDecodeError, IOError):
                return []
        return []

    def _write_logs(self, logs):
        """Helper to safely write logs to the current session file."""
        with open(self.current_session_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=4, ensure_ascii=False)