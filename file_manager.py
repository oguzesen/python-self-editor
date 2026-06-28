# file_manager.py
import os
import json

class FileManager:
    def __init__(self, venv_base_dir):
        self.recent_files_path = os.path.join(venv_base_dir, "recent_files.json")
        self.open_tabs_path = os.path.join(venv_base_dir, "open_tabs.json")
        self.settings_path = os.path.join(venv_base_dir, "settings.json")
        self.recent_files = self._load_recent_files()

    def load_settings(self):
        default_settings = {"is_dark_mode": True, "font_size": 12}
        if os.path.exists(self.settings_path):
            try:
                with open(self.settings_path, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    default_settings.update(settings)
            except Exception as e:
                print(f"Ayarlar yüklenirken hata: {e}")
        return default_settings

    def save_settings(self, settings):
        try:
            with open(self.settings_path, "w", encoding="utf-8") as f:
                json.dump(settings, f)
        except Exception as e:
            print(f"Ayarlar kaydedilirken hata: {e}")

    def _load_recent_files(self):
        if os.path.exists(self.recent_files_path):
            try:
                with open(self.recent_files_path, "r", encoding="utf-8") as f: 
                    return json.load(f)
            except Exception as e:
                print(f"Son dosyalar yüklenirken hata: {e}")
        return []

    def add_to_recent(self, file_path):
        if file_path in self.recent_files: 
            self.recent_files.remove(file_path)
            
        self.recent_files.insert(0, file_path)
        
        if len(self.recent_files) > 20: 
            self.recent_files.pop()
            
        try:
            with open(self.recent_files_path, "w", encoding="utf-8") as f: 
                json.dump(self.recent_files, f)
        except Exception as e:
            print(f"Son dosyalar kaydedilirken hata: {e}")

    def read_file(self, file_path):
        with open(file_path, "r", encoding="utf-8") as f: 
            return f.read()

    def write_file(self, file_path, content):
        with open(file_path, "w", encoding="utf-8") as f: 
            f.write(content)

    def save_open_tabs(self, tabs_list):
        try:
            with open(self.open_tabs_path, "w", encoding="utf-8") as f:
                json.dump(tabs_list, f)
        except Exception as e:
            print(f"Açık sekmeler kaydedilirken hata: {e}")

    def load_open_tabs(self):
        if os.path.exists(self.open_tabs_path):
            try:
                with open(self.open_tabs_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Açık sekmeler yüklenirken hata: {e}")
        return []