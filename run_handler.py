# run_handler.py
import os
import tempfile
import uuid
import re
import subprocess
import tkinter as tk
from tkinter import messagebox
from process_runner import ProcessRunner
from compiler_ui import CompilerUI
from event_bus import EventBus

class RunHandler:
    def __init__(self, app):
        self.app = app
        self.temp_files = [] 
        self.runner = ProcessRunner()
        
        EventBus.subscribe("process:finished", self.on_process_finished)
        EventBus.subscribe("process:run_pip", lambda cmd: self.runner.run(cmd, is_pip=True))
        EventBus.subscribe("process:send_input", self.runner.send_input)

    def open_terminal(self):
        tab = self.app.ui.tab_mgr.get_current_tab()
        cwd = os.path.dirname(tab.file_path) if tab and tab.file_path and not tab.is_temp_file else os.path.expanduser("~")
        
        if not os.path.exists(cwd):
            cwd = os.path.expanduser("~")
            
        env_name = self.app.env_mgr.current_env
        
        if os.name == 'nt': 
            if env_name not in ["Yerel", "Manuel"]:
                activate_script = os.path.join(self.app.env_mgr.venv_base_dir, env_name, "Scripts", "activate.bat")
                if os.path.exists(activate_script):
                    subprocess.Popen(['cmd.exe', '/c', 'start', 'cmd.exe', '/k', activate_script], cwd=cwd)
                    return
            subprocess.Popen(['cmd.exe', '/c', 'start', 'cmd.exe'], cwd=cwd)
        else:
            subprocess.Popen('x-terminal-emulator', cwd=cwd, shell=True)

    def compile_code(self):
        tab = self.app.ui.tab_mgr.get_current_tab()
        if not tab: return
        if not tab.file_path or tab.is_temp_file:
            messagebox.showwarning("Uyarı", "Derleme işlemi için kodunuzu kalıcı olarak kaydetmelisiniz!")
            self.app.save_as_file()
            if not tab.file_path or tab.is_temp_file: return
            
        self.app.save_file()
        CompilerUI(self.app.root, target_file=tab.file_path, python_path=self.app.env_mgr.python_path)

    def run_code(self):
        tab = self.app.ui.tab_mgr.get_current_tab()
        if not tab: return
        
        if not tab.file_path:
            tab.file_path = os.path.join(tempfile.gettempdir(), f"python_ide_{uuid.uuid4().hex[:8]}.py")
            tab.is_temp_file = True
            self.temp_files.append(tab.file_path) 
            self.app.file_mgr.write_file(tab.file_path, tab.get_code())
        elif tab.is_temp_file:
            self.app.file_mgr.write_file(tab.file_path, tab.get_code())
        else:
            self.app.save_file() 
            
        args = self.app.ui.args_entry.get().split()
        work_dir = os.path.dirname(tab.file_path)
        cmd = [self.app.env_mgr.python_path, "-u", tab.file_path] + args
        
        self.app.ui.input_entry.config(state=tk.NORMAL)
        self.app.ui.input_entry.focus_set() 
        
        self.runner.run(cmd, is_pip=False, cwd=work_dir)

    def on_process_finished(self, event_type):
        self.app.ui.input_entry.config(state=tk.DISABLED)
        
        tab = self.app.ui.tab_mgr.get_current_tab()
        if tab:
            tab.text_area.focus_set()
            
        if event_type == "PIP_END":
            EventBus.publish("ui:stop_progress")
            EventBus.publish("env:refresh_libs")

        output_text = self.app.ui.output_screen.get("1.0", tk.END)
        match = re.search(r"No module named ['\"]?([a-zA-Z0-9_\-]+)['\"]?", output_text, re.IGNORECASE)
        
        if match:
            missing_module = match.group(1)
            known_modules = {"cv2": "opencv-python", "bs4": "beautifulsoup4", "sklearn": "scikit-learn", "PIL": "Pillow", "dotenv": "python-dotenv", "yaml": "PyYAML", "pyqt5": "PyQt5", "pyside6": "PySide6", "pyinstaller": "pyinstaller"}
            pip_package = known_modules.get(missing_module.lower(), missing_module)
            
            if messagebox.askyesno("Eksik Kütüphane Tespit Edildi", f"Sisteminizde '{missing_module}' modülü bulunamadı!\n\nIDE'nin '{pip_package}' kütüphanesini otomatik kurmasını ister misiniz?"):
                self.app.install_lib_live(pip_package)

    def poll_queue(self):
        self.runner.check_queue()
        self.app.root.after(50, self.poll_queue)
        
    def cleanup_temp_files(self):
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                print(f"Geçici dosya silinemedi: {e}")