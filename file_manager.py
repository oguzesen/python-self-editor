import os
import json

class FileManager:
    def __init__(self, venv_base_dir):
        # Geçmiş dosyaları ortam klasöründe saklıyoruz
        self.recent_files_path = os.path.join(venv_base_dir, "recent_files.json")
        self.recent_files = self._load_recent_files()

    def _load_recent_files(self):
        if os.path.exists(self.recent_files_path):
            with open(self.recent_files_path, "r", encoding="utf-8") as f: 
                return json.load(f)
        return []

    def add_to_recent(self, file_path):
        if file_path in self.recent_files: 
            self.recent_files.remove(file_path)
            
        self.recent_files.insert(0, file_path)
        
        # En fazla son 20 dosyayı hatırla
        if len(self.recent_files) > 20: 
            self.recent_files.pop()
            
        with open(self.recent_files_path, "w", encoding="utf-8") as f: 
            json.dump(self.recent_files, f)

    def read_file(self, file_path):
        with open(file_path, "r", encoding="utf-8") as f: 
            return f.read()

    def write_file(self, file_path, content):
        with open(file_path, "w", encoding="utf-8") as f: 
            f.write(content)