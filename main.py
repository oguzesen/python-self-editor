import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import os
import tempfile
import uuid
import re
import multiprocessing
from tkinterdnd2 import TkinterDnD

# Kendi Modüllerimiz
from env_manager import EnvManager
from process_runner import ProcessRunner
from file_manager import FileManager
from ui_manager import UIManager
from compiler_ui import CompilerUI

class PythonIDE:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Self Editör - Adsız")
        self.root.geometry("1200x800")
        
        # --- ANA İKON AYARI (Kuş Tüyü Yerine ikon2.ico) ---
        try:
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ikon1.ico")
            if os.path.exists(icon_path):
                # default=icon_path parametresi tüm açılır pencerelerin (mesaj kutuları vb.) aynı ikonu kullanmasını sağlar
                self.root.iconbitmap(default=icon_path)
        except:
            pass
        # ----------------------------------------------------
        
        self.is_dark_mode = tk.BooleanVar(value=True)
        
        self.root.bind("<Control-s>", lambda event: self.save_file())
        self.root.bind("<Control-S>", lambda event: self.save_file()) 
        
        self.env_mgr = EnvManager()
        self.file_mgr = FileManager(self.env_mgr.venv_base_dir)
        self.runner = ProcessRunner(
            write_callback=self.write_output,
            clear_callback=self.clear_output,
            finish_callback=self.on_process_finished
        )
        
        self.ui = UIManager(self.root, self)
        
        self.refresh_env_list()
        self.refresh_libraries_list()
        self.update_recent_combo()
        self.poll_queue()
        self.new_file() 
        self.update_status()

    def toggle_theme(self):
        self.ui.apply_theme(self.is_dark_mode.get())

    # ==========================================
    # DOSYA YÖNETİMİ VE SÜRÜKLE BIRAK
    # ==========================================
    def open_file_dialog(self):
        file_path = filedialog.askopenfilename(filetypes=[("Python", "*.py"), ("Tüm Dosyalar", "*.*")])
        if file_path: self.load_file(file_path)

    def load_file(self, file_path):
        try:
            content = self.file_mgr.read_file(file_path)
            current_tab = self.ui.tab_mgr.get_current_tab()
            
            if current_tab and not current_tab.file_path and len(current_tab.get_code().strip()) == 0:
                tab = current_tab
            else:
                tab = self.ui.tab_mgr.create_editor_tab(file_path)
                self.ui.tab_mgr.add_tab(tab, os.path.basename(file_path))

            tab.load_code(content)
            tab.file_path = file_path
            tab.is_temp_file = False
            
            self.ui.tab_mgr.mark_as_saved(tab, os.path.basename(file_path))
            
            self.file_mgr.add_to_recent(file_path)
            self.update_title()
            self.update_recent_combo()
        except Exception as e:
            messagebox.showerror("Hata", f"Dosya açılamadı:\n{str(e)}")

    def on_drop(self, event):
        paths = self.root.tk.splitlist(event.data)
        py_files = []
        
        for path in paths:
            clean_path = path.strip('{}') 
            if os.path.isdir(clean_path):
                for root_dir, _, files in os.walk(clean_path):
                    for file in files:
                        if file.endswith('.py'):
                            py_files.append(os.path.join(root_dir, file))
            elif os.path.isfile(clean_path) and clean_path.endswith('.py'):
                py_files.append(clean_path)
                
        if len(py_files) > 20:
            if not messagebox.askyesno("Çok Fazla Dosya", f"Klasörden {len(py_files)} adet Python dosyası bulundu.\nHepsini açmak bilgisayarı yorabilir. Devam edilsin mi?"):
                return
                
        for file_path in py_files:
            self.load_file(file_path)

    def update_recent_combo(self):
        display_list = ["Son Dosyalar..."] + [os.path.basename(f) for f in self.file_mgr.recent_files]
        self.ui.recent_combo['values'] = display_list
        self.ui.recent_combo.current(0)

    def on_recent_selected(self, event):
        idx = self.ui.recent_combo.current()
        if idx > 0:
            file_path = self.file_mgr.recent_files[idx - 1]
            if os.path.exists(file_path): self.load_file(file_path)
        self.ui.recent_combo.current(0)

    def new_file(self):
        tab = self.ui.tab_mgr.create_editor_tab()
        self.ui.tab_mgr.add_tab(tab, "Adsız")
        self.update_title()

    def save_file(self):
        tab = self.ui.tab_mgr.get_current_tab()
        if not tab: return
        if tab.file_path and not tab.is_temp_file:
            self.file_mgr.write_file(tab.file_path, tab.get_code())
            self.file_mgr.add_to_recent(tab.file_path)
            self.update_recent_combo()
            
            self.ui.tab_mgr.mark_as_saved(tab, os.path.basename(tab.file_path))
            self.write_output(f"--- Kaydedildi: {tab.file_path} ---\n")
        else:
            self.save_as_file()

    def save_as_file(self):
        tab = self.ui.tab_mgr.get_current_tab()
        if not tab: return
        file_path = filedialog.asksaveasfilename(defaultextension=".py", filetypes=[("Python", "*.py")])
        if file_path:
            tab.file_path = file_path
            tab.is_temp_file = False
            self.save_file()
            self.ui.tab_mgr.update_tab_text(tab, os.path.basename(file_path))
            self.update_title()

    def update_title(self):
        tab = self.ui.tab_mgr.get_current_tab()
        if tab:
            title = tab.file_path if tab.file_path else "Adsız"
            self.root.title(f"Python Self Editör - {title}")
        else:
            self.root.title("Python Self Editör")

    def update_status(self):
        self.ui.status_bar.config(text=f"Ortam: [{self.env_mgr.current_env}] | Python: {self.env_mgr.python_path}")

    # ==========================================
    # ORTAM VE KÜTÜPHANE YÖNETİMİ
    # ==========================================
    def refresh_env_list(self):
        self.ui.env_combo['values'] = self.env_mgr.get_environment_list()
        self.ui.env_combo.set(self.env_mgr.current_env)

    def on_env_selected(self, event):
        selection = self.ui.env_combo.get()
        if selection == "+ Yeni Ortam Oluştur...":
            env_name = simpledialog.askstring("Yeni Ortam", "Sanal ortam için bir isim girin:")
            if env_name:
                self.ui.progress_bar.pack(side=tk.LEFT, padx=5)
                self.ui.progress_bar.start(10)
                self.ui.env_combo.config(state="disabled")
                self.env_mgr.create_venv_async(env_name, lambda n: self.root.after(0, self._venv_success, n), lambda e: self.root.after(0, self._venv_error, e))
            else:
                self.ui.env_combo.set(self.env_mgr.current_env)
        else:
            success, err_path = self.env_mgr.select_environment(selection)
            if success:
                self.update_status()
                self.refresh_libraries_list() 
            else:
                messagebox.showerror("Hata", f"Ortam bozuk veya python.exe bulunamad!\n{err_path}")
                self.ui.env_combo.set(self.env_mgr.current_env)

    def _venv_success(self, env_name):
        self.ui.progress_bar.stop(); self.ui.progress_bar.pack_forget()
        self.ui.env_combo.config(state="readonly")
        self.refresh_env_list()
        self.ui.env_combo.set(env_name)
        self.on_env_selected(None)

    def _venv_error(self, err_msg):
        self.ui.progress_bar.stop(); self.ui.progress_bar.pack_forget()
        self.ui.env_combo.config(state="readonly")
        messagebox.showerror("Hata", err_msg)
        self.ui.env_combo.set(self.env_mgr.current_env)

    def show_env_context(self, event):
        selection = self.ui.env_combo.get()
        if selection not in ["Yerel", "+ Yeni Ortam Oluştur...", "Manuel", ""]:
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label=f"'{selection}' Ortamını Sil", command=lambda: self.delete_env(selection))
            menu.tk_popup(event.x_root, event.y_root)

    def delete_env(self, env_name):
        if messagebox.askyesno("Onay", f"'{env_name}' ortamını tamamen silmek istediğinize emin misiniz?"):
            self.ui.progress_bar.pack(side=tk.LEFT, padx=5)
            self.ui.progress_bar.start(10)
            self.ui.env_combo.config(state="disabled")
            self.env_mgr.delete_venv_async(env_name, lambda n: self.root.after(0, self._delete_env_success, n), lambda e: self.root.after(0, self._venv_error, e))

    def _delete_env_success(self, env_name):
        self.ui.progress_bar.stop(); self.ui.progress_bar.pack_forget()
        self.ui.env_combo.config(state="readonly")
        
        if self.env_mgr.current_env == env_name:
            self.ui.env_combo.set("Yerel")
            self.on_env_selected(None) 
        
        self.refresh_env_list()
        messagebox.showinfo("Başarılı", f"'{env_name}' ortamı silindi.")

    def refresh_libraries_list(self):
        self.ui.lib_combo['values'] = ["Yükleniyor..."]
        self.ui.lib_combo.current(0)
        self.env_mgr.fetch_libraries_async(lambda libs: self.root.after(0, lambda: self._update_lib_combo(libs)))

    def _update_lib_combo(self, lib_list):
        self.ui.lib_combo['values'] = lib_list
        self.ui.lib_combo.current(0)

    def on_lib_selected(self, event):
        if self.ui.lib_combo.current() == 0: 
            lib_name = simpledialog.askstring("Pip Install", f"[{self.env_mgr.current_env}] ortamına kurulacak kütüphane adı:")
            if lib_name: 
                self.install_lib_live(lib_name)

    def install_lib_live(self, lib_name):
        self.ui.progress_bar.pack(side=tk.LEFT, padx=5)
        self.ui.progress_bar.start(10)
        self.clear_output()
        self.write_output(f"--- '{lib_name}' Kurulumu Başlatılıyor... Lütfen Bekleyin ---\n")
        cmd = [self.env_mgr.python_path, "-m", "pip", "install", lib_name]
        self.runner.run(cmd, is_pip=True)

    def show_lib_context(self, event):
        selection = self.ui.lib_combo.get()
        if selection not in ["+ Kütüphane Ekle", "Yükleniyor...", "Hata!", ""]:
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label=f"'{selection}' Kaldır", command=lambda: self.uninstall_lib(selection))
            menu.tk_popup(event.x_root, event.y_root)

    def uninstall_lib(self, lib_name):
        if messagebox.askyesno("Onay", f"'{lib_name}' kütüphanesini kaldırmak istediğinize emin misiniz?"):
            self.ui.progress_bar.pack(side=tk.LEFT, padx=5)
            self.ui.progress_bar.start(10)
            self.clear_output()
            self.write_output(f"--- '{lib_name}' Kaldırılıyor... ---\n")
            cmd = [self.env_mgr.python_path, "-m", "pip", "uninstall", "-y", lib_name]
            self.runner.run(cmd, is_pip=True)

    # ==========================================
    # ÇALIŞTIRMA, DERLEME VE KONSOL
    # ==========================================
    def compile_code(self):
        tab = self.ui.tab_mgr.get_current_tab()
        if not tab: return
        if not tab.file_path or tab.is_temp_file:
            messagebox.showwarning("Uyarı", "Derleme işlemi için kodunuzu kalıcı olarak kaydetmelisiniz!")
            self.save_as_file()
            if not tab.file_path or tab.is_temp_file: return
            
        self.save_file()
        CompilerUI(self.root, self)

    def run_code(self):
        tab = self.ui.tab_mgr.get_current_tab()
        if not tab: return
        
        if not tab.file_path:
            tab.file_path = os.path.join(tempfile.gettempdir(), f"python_ide_{uuid.uuid4().hex[:8]}.py")
            tab.is_temp_file = True
            self.file_mgr.write_file(tab.file_path, tab.get_code())
        elif tab.is_temp_file:
            self.file_mgr.write_file(tab.file_path, tab.get_code())
        else:
            self.save_file() 
            
        args = self.ui.args_entry.get().split()
        work_dir = os.path.dirname(tab.file_path)
        cmd = [self.env_mgr.python_path, "-u", tab.file_path] + args
        self.runner.run(cmd, is_pip=False, cwd=work_dir)

    def change_python_path(self, event):
        new_path = filedialog.askopenfilename(title="Derleyici Seçin", filetypes=[("Yürütülebilir Dosya", "*.exe"), ("Tüm Dosyalar", "*.*")])
        if new_path:
            self.env_mgr.python_path = new_path
            self.env_mgr.current_env = "Manuel"
            self.update_status()

    def clear_output(self): self.ui.output_screen.delete("1.0", tk.END)
    def write_output(self, text): self.ui.output_screen.insert(tk.END, text); self.ui.output_screen.see(tk.END)

    def on_process_finished(self, event_type):
        if event_type == "PIP_END":
            self.ui.progress_bar.stop()
            self.ui.progress_bar.pack_forget()
            self.refresh_libraries_list()

        output_text = self.ui.output_screen.get("1.0", tk.END)
        match = re.search(r"No module named ['\"]?([a-zA-Z0-9_\-]+)['\"]?", output_text, re.IGNORECASE)
        
        if match:
            missing_module = match.group(1)
            known_modules = {"cv2": "opencv-python", "bs4": "beautifulsoup4", "sklearn": "scikit-learn", "PIL": "Pillow", "dotenv": "python-dotenv", "yaml": "PyYAML", "pyqt5": "PyQt5", "pyside6": "PySide6", "pyinstaller": "pyinstaller"}
            pip_package = known_modules.get(missing_module.lower(), missing_module)
            
            if messagebox.askyesno("Eksik Kütüphane Tespit Edildi", f"Sisteminizde '{missing_module}' modülü bulunamadı!\n\nIDE'nin '{pip_package}' kütüphanesini otomatik kurmasını ister misiniz?"):
                self.install_lib_live(pip_package)

    def poll_queue(self):
        self.runner.check_queue()
        self.root.after(50, self.poll_queue)

if __name__ == "__main__":
    multiprocessing.freeze_support() 
    root = TkinterDnD.Tk()
    app = PythonIDE(root)
    root.mainloop()