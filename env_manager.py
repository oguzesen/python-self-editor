# env_manager.py
import os
import sys
import subprocess
import threading
import shutil

class EnvManager:
    def __init__(self):
        # FORK BOMB KORUMASI: Eğer exe olarak derlenmişsek sys.executable bizi işaret eder!
        if getattr(sys, 'frozen', False):
            # Derlenmişsek (exe), sonsuz döngüye girmemek için sistemdeki gerçek python'u buluyoruz
            system_python = shutil.which("python")
            self.base_python = system_python if system_python else "python"
        else:
            self.base_python = sys.executable  
            
        self.python_path = self.base_python
        self.venv_base_dir = os.path.join(os.path.expanduser("~"), ".python_ide_venvs")
        os.makedirs(self.venv_base_dir, exist_ok=True)
        self.current_env = "Yerel"

    def get_environment_list(self):
        envs = ["Yerel", "+ Yeni Ortam Oluştur..."]
        for item in os.listdir(self.venv_base_dir):
            item_path = os.path.join(self.venv_base_dir, item)
            if os.path.isdir(item_path):
                envs.append(item)
        return envs

    def select_environment(self, selection):
        if selection == "Yerel":
            self.python_path = self.base_python
            self.current_env = "Yerel"
            return True, None
            
        env_python_exe = os.path.join(self.venv_base_dir, selection, "Scripts", "python.exe") if os.name == 'nt' else os.path.join(self.venv_base_dir, selection, "bin", "python")
        if os.path.exists(env_python_exe):
            self.python_path = env_python_exe
            self.current_env = selection
            return True, None
        else:
            return False, env_python_exe

    def create_venv_async(self, env_name, success_cb, error_cb):
        env_path = os.path.join(self.venv_base_dir, env_name)
        if os.path.exists(env_path):
            error_cb("Bu isimde bir ortam zaten var!")
            return

        def worker():
            try:
                subprocess.run([self.base_python, "-m", "venv", env_path], check=True)
                success_cb(env_name)
            except Exception as e:
                error_cb(str(e))
        threading.Thread(target=worker, daemon=True).start()

    def delete_venv_async(self, env_name, success_cb, error_cb):
        env_path = os.path.join(self.venv_base_dir, env_name)
        def worker():
            try:
                shutil.rmtree(env_path)
                success_cb(env_name)
            except Exception as e:
                error_cb(str(e))
        threading.Thread(target=worker, daemon=True).start()

    def fetch_libraries_async(self, callback):
        def worker():
            try:
                result = subprocess.run([self.python_path, "-m", "pip", "freeze"], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                libs = [lib.split('==')[0] for lib in result.stdout.split('\n') if lib] 
                callback(["+ Kütüphane Ekle"] + libs)
            except Exception:
                callback(["+ Kütüphane Ekle", "Hata!"])
        threading.Thread(target=worker, daemon=True).start()