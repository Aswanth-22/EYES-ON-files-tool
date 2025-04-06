import os
import hashlib
import json
import time
import threading
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox

HASH_DB_FILE = 'file_hashes.json'

class FileMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("File Integrity Monitor")
        self.root.geometry("800x800")
        self.monitor_dir = ""
        self.running = False

        # GUI Elements
        self.path_label = tk.Label(root, text="No folder selected")
        self.path_label.pack(pady=5)

        self.select_btn = tk.Button(root, text="Select Folder", command=self.select_folder)
        self.select_btn.pack(pady=5)

        self.start_btn = tk.Button(root, text="Start Monitoring", command=self.toggle_monitoring)
        self.start_btn.pack(pady=5)

        self.log_box = scrolledtext.ScrolledText(root, width=80, height=50)
        self.log_box.pack(pady=10)

        self.status_label = tk.Label(root, text="Status: Idle")
        self.status_label.pack()

    def log(self, message):
        self.log_box.insert(tk.END, message + "\n")
        self.log_box.see(tk.END)

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.monitor_dir = folder
            self.path_label.config(text=f"EYES ON: {folder}")

    def toggle_monitoring(self):
        if not self.monitor_dir:
            messagebox.showwarning("No folder", "Please select a folder to monitor.")
            return

        self.running = not self.running
        if self.running:
            self.start_btn.config(text="Stop Monitoring")
            self.status_label.config(text="Status: Monitoring...")
            threading.Thread(target=self.monitor_loop, daemon=True).start()
        else:
            self.start_btn.config(text="Start Monitoring")
            self.status_label.config(text="Status: Stopped")

    def calculate_hash(self, file_path):
        sha256 = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                while chunk := f.read(8192):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except FileNotFoundError:
            return None

    def load_hashes(self):
        if not os.path.exists(HASH_DB_FILE):
            return {}
        with open(HASH_DB_FILE, 'r') as f:
            return json.load(f)

    def save_hashes(self, hashes):
        with open(HASH_DB_FILE, 'w') as f:
            json.dump(hashes, f, indent=4)

    def monitor_once(self):
        stored_hashes = self.load_hashes()
        current_hashes = {}

        for root_dir, _, files in os.walk(self.monitor_dir):
            for file in files:
                path = os.path.join(root_dir, file)
                rel_path = os.path.relpath(path, self.monitor_dir)
                file_hash = self.calculate_hash(path)
                current_hashes[rel_path] = file_hash

                if rel_path not in stored_hashes:
                    self.log(f"[NEW] File added: {rel_path}")
                elif stored_hashes[rel_path] != file_hash:
                    self.log(f"[MODIFIED] File changed: {rel_path}")

        for rel_path in stored_hashes:
            if rel_path not in current_hashes:
                self.log(f"[DELETED] File removed: {rel_path}")

        self.save_hashes(current_hashes)

    def monitor_loop(self):
        while self.running:
            self.monitor_once()
            time.sleep(5)

if __name__ == "__main__":
    root = tk.Tk()
    app = FileMonitorApp(root)
    root.mainloop()
