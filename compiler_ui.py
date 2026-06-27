import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
import threading
import subprocess
import shutil
import ast
from pathlib import Path

def get_ide_base_path():
    if getattr(sys, 'frozen', False): return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

# --- BAĞIMLILIK İSTEMEYEN SETUP SİHİRBAZI ŞABLONU ---
SETUP_SCRIPT_TEMPLATE = """
import os
import sys
import shutil
import winreg
import ctypes
import tkinter as tk
from tkinter import messagebox

APP_NAME = "__APP_NAME__"
EXE_FILENAME = "__EXE_FILENAME__"
ICON_FILENAME = "__ICON_FILENAME__"
DESCRIPTION = '''__DESCRIPTION__'''
DEFAULT_INSTALL_DIR = os.path.join(os.environ.get("ProgramFiles", "C:\\\\Program Files"), APP_NAME)

def is_admin():
    try: return ctypes.windll.shell32.IsUserAnAdmin()
    except: return False

if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

def get_base_path():
    if getattr(sys, 'frozen', False): return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

class SetupWizard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME + " Kurulumu")
        self.geometry("480x520")
        self.resizable(False, False)
        
        try:
            standard_ico = os.path.join(get_base_path(), "ikon2.ico")
            if os.path.exists(standard_ico):
                self.iconbitmap(standard_ico)
        except: pass
        
        self.install_path_var = tk.StringVar(value=DEFAULT_INSTALL_DIR)
        self.create_shortcut_var = tk.BooleanVar(value=True)
        
        if ICON_FILENAME:
            try:
                icon_path = os.path.join(get_base_path(), ICON_FILENAME)
                self.img = tk.PhotoImage(file=icon_path)
                tk.Label(self, image=self.img).pack(pady=(15, 5))
            except: pass
            
        tk.Label(self, text=APP_NAME + " Kurulumuna Hoş Geldiniz", font=("Arial", 14, "bold")).pack(pady=(5, 10))
        
        if DESCRIPTION.strip():
            desc_frame = tk.Frame(self, bg="#f0f0f0", bd=1, relief="sunken")
            desc_frame.pack(fill="x", padx=25, pady=5)
            
            scrollbar = tk.Scrollbar(desc_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            desc_text = tk.Text(desc_frame, bg="#f0f0f0", height=6, wrap=tk.WORD, yscrollcommand=scrollbar.set, font=("Arial", 9), bd=0)
            desc_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
            scrollbar.config(command=desc_text.yview)
            
            desc_text.insert(tk.END, DESCRIPTION)
            desc_text.config(state=tk.DISABLED)
            
        tk.Label(self, text="Kurulum Konumu:", font=("Arial", 10, "bold")).pack(anchor="w", padx=25, pady=(10, 0))
        tk.Entry(self, textvariable=self.install_path_var, width=60).pack(padx=25, pady=5)
        
        tk.Checkbutton(self, text="Masaüstüne Kısayol Oluştur", variable=self.create_shortcut_var, font=("Arial", 10)).pack(anchor="w", padx=25, pady=5)
        
        tk.Button(self, text="Kur", bg="green", fg="white", font=("Arial", 12, "bold"), width=15, command=self.start_installation).pack(pady=15)

    def start_installation(self):
        install_dir = self.install_path_var.get()
        exe_source = os.path.join(get_base_path(), EXE_FILENAME)
        exe_dest = os.path.join(install_dir, EXE_FILENAME)
        
        try:
            os.makedirs(install_dir, exist_ok=True)
            shutil.copy(exe_source, exe_dest)
            
            # --- YENİ VBSCRIPT UNINSTALLER (Sessiz ve Güvenilir) ---
            uninstaller_path = os.path.join(install_dir, "Uninstall.vbs")
            with open(uninstaller_path, "w", encoding="utf-8") as f:
                f.write('Set WshShell = CreateObject("WScript.Shell")\\n')
                f.write('Set FSO = CreateObject("Scripting.FileSystemObject")\\n')
                f.write('On Error Resume Next\\n')
                # Kayıt Defterinden Silme (Konsolsuz çalışır)
                f.write('WshShell.Run "cmd.exe /c reg delete ""HKLM\\\\SOFTWARE\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\' + APP_NAME + '"" /f", 0, True\\n')
                # Kısayolları Silme
                f.write('FSO.DeleteFile WshShell.ExpandEnvironmentStrings("%PUBLIC%") & "\\\\Desktop\\\\' + APP_NAME + '.lnk", True\\n')
                f.write('FSO.DeleteFile WshShell.ExpandEnvironmentStrings("%USERPROFILE%") & "\\\\Desktop\\\\' + APP_NAME + '.lnk", True\\n')
                # Başarı Mesajı Göster
                f.write('MsgBox "' + APP_NAME + ' bilgisayarinizdan basariyla kaldirildi.", 64, "Kaldirma Islemi"\\n')
                # Program klasörünü tamamen silme (Gecikmeli ping ile VBS dosya kilidini açar, Chr(34) ile tırnak çakışmasını önler)
                f.write('WshShell.Run "cmd.exe /c ping 127.0.0.1 -n 2 > nul & rmdir /s /q " & Chr(34) & "' + install_dir + '" & Chr(34), 0, False\\n')

            if self.create_shortcut_var.get():
                public_desktop = os.path.join(os.environ.get("PUBLIC", os.environ.get("USERPROFILE")), "Desktop")
                shortcut_path = os.path.join(public_desktop, APP_NAME + ".lnk")
                
                ps_script = (
                    '$WshShell = New-Object -comObject WScript.Shell\\n'
                    '$Shortcut = $WshShell.CreateShortcut("' + shortcut_path + '")\\n'
                    '$Shortcut.TargetPath = "' + exe_dest + '"\\n'
                    '$Shortcut.WorkingDirectory = "' + install_dir + '"\\n'
                    '$Shortcut.Save()\\n'
                )
                import subprocess
                subprocess.run(["powershell", "-Command", ps_script], creationflags=0x08000000)

            # Kayıt Defteri Ekleme
            reg_path = "SOFTWARE\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\" + APP_NAME
            key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, APP_NAME)
            winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, 'wscript.exe "' + uninstaller_path + '"')
            winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, '"' + exe_dest + '"')
            winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, install_dir)
            winreg.CloseKey(key)

            messagebox.showinfo("Başarılı", APP_NAME + " başarıyla kuruldu!")
            self.destroy()

        except Exception as e:
            messagebox.showerror("Kurulum Hatası", "Bir hata oluştu:\\n" + str(e))
            self.destroy()

if __name__ == "__main__":
    app = SetupWizard()
    app.mainloop()
"""

class CompilerUI(tk.Toplevel):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.title("Gelişmiş Derleme Yöneticisi")
        self.geometry("550x680") 
        self.resizable(False, True) 
        
        icon_path = os.path.join(get_ide_base_path(), "ikon1.ico")
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)
        
        self.transient(parent)
        self.grab_set()
        
        self.target_file = ""
        self.app_name_var = tk.StringVar() 
        self.icon_path = tk.StringVar()
        self.added_files = []
        
        self.no_console_var = tk.BooleanVar(value=False)
        self.create_setup_var = tk.BooleanVar(value=False)
        
        tab = self.app.ui.tab_mgr.get_current_tab()
        if tab and tab.file_path and not tab.is_temp_file:
            self.target_file = tab.file_path
            
        self.setup_ui()
        
    def setup_ui(self):
        bg_color = "#333333"
        self.configure(bg=bg_color)
        style = {"bg": bg_color, "fg": "white", "font": ("Consolas", 10)}
        
        tk.Label(self, text="Derlenecek Ana Dosya:", **style).pack(anchor="w", padx=10, pady=(10, 0))
        lbl_file = tk.Label(self, text=os.path.basename(self.target_file) if self.target_file else "Seçili Dosya Yok! Önce kaydedin.", bg="#1E1F1C", fg="#A6E22E", font=("Consolas", 10, "bold"))
        lbl_file.pack(fill=tk.X, padx=10, pady=5)
        
        name_frame = tk.Frame(self, bg=bg_color)
        name_frame.pack(fill=tk.X, padx=10, pady=(5, 5))
        tk.Label(name_frame, text="Uygulama Adı:", **style).pack(side=tk.LEFT)
        tk.Entry(name_frame, textvariable=self.app_name_var, bg="#1E1F1C", fg="white", insertbackground="white").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5,0))
        
        icon_frame = tk.Frame(self, bg=bg_color)
        icon_frame.pack(fill=tk.X, padx=10, pady=(5, 10))
        tk.Label(icon_frame, text="Uygulama İkonu:", **style).pack(side=tk.LEFT)
        tk.Entry(icon_frame, textvariable=self.icon_path, bg="#1E1F1C", fg="white", insertbackground="white").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5,5))
        tk.Button(icon_frame, text="Gözat", command=self.browse_icon, bg="#555555", fg="white", relief=tk.FLAT).pack(side=tk.LEFT)
        
        tk.Checkbutton(self, text="Konsol Penceresini Gizle (--windowed)", variable=self.no_console_var, bg=bg_color, fg="white", selectcolor="#444444", activebackground=bg_color, activeforeground="white").pack(anchor="w", padx=10)
        
        tk.Label(self, text="Ek Dosyalar (Resim, Veritabanı vb.):", **style).pack(anchor="w", padx=10, pady=(15, 0))
        
        list_frame = tk.Frame(self, bg=bg_color)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.files_listbox = tk.Listbox(list_frame, bg="#1E1F1C", fg="white", selectbackground="#007ACC", height=5)
        self.files_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        btn_frame = tk.Frame(list_frame, bg=bg_color)
        btn_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5,0))
        tk.Button(btn_frame, text="Ekle", command=self.add_file, bg="#007ACC", fg="white", relief=tk.FLAT, width=8).pack(pady=(0,5))
        tk.Button(btn_frame, text="Sil", command=self.remove_file, bg="#CC4444", fg="white", relief=tk.FLAT, width=8).pack()
        
        tk.Checkbutton(self, text="📦 Setup Oluştur", variable=self.create_setup_var, command=self.toggle_setup_options, bg=bg_color, fg="#A6E22E", font=("Consolas", 12, "bold"), selectcolor="#444444", activebackground=bg_color, activeforeground="#A6E22E").pack(anchor="w", padx=10, pady=10)

        self.setup_options_frame = tk.Frame(self, bg=bg_color)
        tk.Label(self.setup_options_frame, text="Setup İçin Açıklama:", **style).pack(anchor="w")
        self.setup_desc = tk.Text(self.setup_options_frame, height=4, bg="#1E1F1C", fg="white", insertbackground="white", font=("Consolas", 10))
        self.setup_desc.pack(fill=tk.X, pady=5)

        self.build_btn = tk.Button(self, text="⚙ OLUŞTUR", command=self.build, bg="#FD971F", fg="black", font=("Consolas", 14, "bold"), relief=tk.FLAT, pady=5)
        self.build_btn.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=10)

    def toggle_setup_options(self):
        if self.create_setup_var.get():
            self.setup_options_frame.pack(fill=tk.X, padx=10, pady=5, before=self.build_btn)
        else:
            self.setup_options_frame.pack_forget()

    def browse_icon(self):
        path = filedialog.askopenfilename(filetypes=[("Görsel Dosyalar", "*.png;*.jpg;*.jpeg;*.bmp;*.gif;*.ico"), ("Tüm Dosyalar", "*.*")])
        if path: self.icon_path.set(path)
            
    def add_file(self):
        paths = filedialog.askopenfilenames(filetypes=[("Tüm Dosyalar", "*.*")])
        for p in paths:
            if p not in self.added_files:
                self.added_files.append(p)
                self.files_listbox.insert(tk.END, os.path.basename(p))
                
    def remove_file(self):
        selection = self.files_listbox.curselection()
        if selection:
            idx = selection[0]
            self.files_listbox.delete(idx)
            self.added_files.pop(idx)

    # --- DİNAMİK KÜTÜPHANE VE İLİŞKİLİ DOSYA TARAYICI ---
    def _scan_dependencies(self, directory):
        imports = set()
        exclude_dirs = {'venv', '.venv', 'env', '.env', '__pycache__', 'build', 'dist', '.git', '.python_ide_venvs'}
        
        for root_dir, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if file.endswith('.py'):
                    try:
                        with open(os.path.join(root_dir, file), 'r', encoding='utf-8') as f:
                            tree = ast.parse(f.read())
                        for node in ast.walk(tree):
                            if isinstance(node, ast.Import):
                                for alias in node.names:
                                    imports.add(alias.name.split('.')[0])
                            elif isinstance(node, ast.ImportFrom):
                                if node.module:
                                    imports.add(node.module.split('.')[0])
                    except Exception:
                        pass
        return list(imports)
    # -----------------------------------------------------------
            
    def build(self):
        if not self.target_file:
            messagebox.showwarning("Uyarı", "Derlenecek dosya bulunamadı! Lütfen önce dosyanızı diske kaydedin.", parent=self)
            return
            
        final_icon_path = None
        setup_icon_path = None
        
        # 1. Aşama: Görseli ICO Formatına Çevirme
        if self.icon_path.get():
            try:
                from PIL import Image
                img_path = Path(self.icon_path.get())
                target_dir = Path(self.target_file).parent
                
                if img_path.suffix.lower() != '.ico':
                    ico_path = target_dir / (img_path.stem + "_converted.ico")
                    Image.open(img_path).convert("RGBA").save(ico_path, format="ICO", sizes=[(64, 64)])
                    final_icon_path = str(ico_path)
                else:
                    final_icon_path = str(img_path)
                    
                png_path = target_dir / (img_path.stem + "_setup.png")
                img_setup = Image.open(img_path).convert("RGBA")
                img_setup.thumbnail((128, 128), Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.LANCZOS)
                img_setup.save(png_path, format="PNG")
                setup_icon_path = str(png_path)
                    
            except ImportError:
                messagebox.showerror("Hata", "Görsel dönüştürme işlemi için 'Pillow' kütüphanesi eksik!\nLütfen kurun: pip install Pillow", parent=self)
                return
            except Exception as e:
                messagebox.showerror("Hata", f"İkon dönüştürme sırasında hata oluştu:\n{e}", parent=self)
                return

        # 2. Aşama: Orijinal Kodu Derleme (PyInstaller)
        cmd = [self.app.env_mgr.python_path, "-m", "PyInstaller", "--onefile", "--noconfirm"]
        if final_icon_path: cmd.append(f"--icon={final_icon_path}")
        if self.no_console_var.get(): cmd.append("--windowed")
        for f in self.added_files: cmd.append(f"--add-data={f}{os.pathsep}.")
            
        work_dir = os.path.dirname(self.target_file)
        
        # Dinamik kütüphaneleri dahil ediyoruz
        scanned_imports = self._scan_dependencies(work_dir)
        for imp in scanned_imports:
            cmd.append(f"--hidden-import={imp}")

        cmd.append(self.target_file)
        
        custom_app_name = self.app_name_var.get().strip()
        
        self.app.clear_output()
        self.app.write_output(f"--- Derleme İşlemi Başlıyor ---\n")
        
        self.build_btn.config(text="Derleniyor... Lütfen Bekleyin", command=lambda: None)
        self.update()
        
        threading.Thread(target=self._build_worker, args=(cmd, work_dir, final_icon_path, setup_icon_path, custom_app_name), daemon=True).start()

    def _build_worker(self, cmd, work_dir, final_icon_path, setup_icon_path, custom_app_name):
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"

        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors='replace', env=env, bufsize=1,
            cwd=work_dir, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )

        for line in iter(process.stdout.readline, ''):
            self.app.root.after(0, self.app.write_output, line)

        process.stdout.close()
        process.wait()

        self.app.root.after(0, self.app.write_output, "\n--- Derleme Tamamlandı, Klasör Düzenleniyor ---\n")

        try:
            target_path = Path(self.target_file)
            stem = target_path.stem
            parent_dir = target_path.parent
            
            app_name = custom_app_name if custom_app_name else stem.capitalize()
            
            spec_file = parent_dir / f"{stem}.spec"
            build_dir = parent_dir / "build"
            dist_dir = parent_dir / "dist"
            dist_exe = dist_dir / f"{stem}.exe"
            
            final_exe = parent_dir / f"{app_name}.exe"

            if dist_exe.exists():
                if final_exe.exists(): final_exe.unlink()
                shutil.move(str(dist_exe), str(final_exe))

            if build_dir.exists(): shutil.rmtree(build_dir, ignore_errors=True)
            if dist_dir.exists(): shutil.rmtree(dist_dir, ignore_errors=True)
            if spec_file.exists(): spec_file.unlink()
            
            # --- 3. AŞAMA: TEK SAYFA SETUP OLUŞTURMA (Eğer seçildiyse) ---
            if self.create_setup_var.get() and final_exe.exists():
                self.app.root.after(0, self.app.write_output, "\n--- Setup Sihirbazı Üretiliyor... ---\n")
                
                setup_script_name = f"setup_builder_{stem}.py"
                setup_script_path = parent_dir / setup_script_name
                icon_name = os.path.basename(setup_icon_path) if setup_icon_path else ""
                
                desc_text = self.setup_desc.get("1.0", tk.END).strip()
                desc_text = desc_text.replace("'''", "''' + \"'''\" + '''") 

                script_content = SETUP_SCRIPT_TEMPLATE.replace("__APP_NAME__", app_name)
                script_content = script_content.replace("__EXE_FILENAME__", final_exe.name)
                script_content = script_content.replace("__ICON_FILENAME__", icon_name)
                script_content = script_content.replace("__DESCRIPTION__", desc_text)
                
                with open(setup_script_path, "w", encoding="utf-8") as f:
                    f.write(script_content)
                
                standard_icon_path = os.path.join(get_ide_base_path(), "ikon2.ico")
                
                setup_cmd = [
                    self.app.env_mgr.python_path, "-m", "PyInstaller", "--onefile", "--windowed", "--noconfirm",
                    f"--add-data={final_exe}{os.pathsep}.",
                    f"--name=Setup_{app_name}"
                ]
                
                if setup_icon_path:
                    setup_cmd.append(f"--add-data={setup_icon_path}{os.pathsep}.")
                    
                if os.path.exists(standard_icon_path):
                    setup_cmd.append(f"--icon={standard_icon_path}")
                    setup_cmd.append(f"--add-data={standard_icon_path}{os.pathsep}.")
                elif final_icon_path:
                    setup_cmd.append(f"--icon={final_icon_path}")
                    
                setup_cmd.append(str(setup_script_path))
                
                setup_process = subprocess.Popen(
                    setup_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, encoding="utf-8", errors='replace', env=env, bufsize=1,
                    cwd=work_dir, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                
                for line in iter(setup_process.stdout.readline, ''):
                    self.app.root.after(0, self.app.write_output, line)
                    
                setup_process.wait()
                
                setup_spec = parent_dir / f"Setup_{app_name}.spec"
                setup_dist_exe = dist_dir / f"Setup_{app_name}.exe"
                final_setup_exe = parent_dir / f"Setup_{app_name}.exe"
                
                if setup_dist_exe.exists():
                    if final_setup_exe.exists(): final_setup_exe.unlink()
                    shutil.move(str(setup_dist_exe), str(final_setup_exe))
                
                if build_dir.exists(): shutil.rmtree(build_dir, ignore_errors=True)
                if dist_dir.exists(): shutil.rmtree(dist_dir, ignore_errors=True)
                if setup_spec.exists(): setup_spec.unlink()
                if setup_script_path.exists(): setup_script_path.unlink()
                if setup_icon_path and os.path.exists(setup_icon_path): os.remove(setup_icon_path)
                
                self.app.root.after(0, self.app.write_output, f"\n--- SETUP ÜRETİMİ BAŞARILI ---\nSetup Dosyası: {final_setup_exe}\n")
                if os.name == 'nt' and final_setup_exe.exists():
                    subprocess.Popen(f'explorer /select,"{final_setup_exe}"')
            else:
                self.app.root.after(0, self.app.write_output, f"\n--- İŞLEM BAŞARILI ---\nExe Dosyası Konumu: {final_exe}\n")
                if os.name == 'nt' and final_exe.exists():
                    subprocess.Popen(f'explorer /select,"{final_exe}"')

        except Exception as e:
            self.app.root.after(0, self.app.write_output, f"\nİşlem sırasında hata oluştu: {e}\n")

        self.app.root.after(0, self.destroy)