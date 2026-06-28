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
            
            uninstaller_path = os.path.join(install_dir, "Uninstall.vbs")
            # ÇÖZÜM BURADA: encoding="mbcs" ile Windows'un ANSI dil kodlamasını kullanarak Türkçe karakter bozulmasını engelliyoruz
            with open(uninstaller_path, "w", encoding="mbcs") as f:
                f.write('Set WshShell = CreateObject("WScript.Shell")\\n')
                f.write('Set FSO = CreateObject("Scripting.FileSystemObject")\\n')
                f.write('On Error Resume Next\\n')
                f.write('WshShell.Run "cmd.exe /c reg delete ""HKLM\\\\SOFTWARE\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\' + APP_NAME + '"" /f", 0, True\\n')
                f.write('FSO.DeleteFile WshShell.ExpandEnvironmentStrings("%PUBLIC%") & "\\\\Desktop\\\\' + APP_NAME + '.lnk", True\\n')
                f.write('FSO.DeleteFile WshShell.ExpandEnvironmentStrings("%USERPROFILE%") & "\\\\Desktop\\\\' + APP_NAME + '.lnk", True\\n')
                f.write('MsgBox "' + APP_NAME + ' bilgisayarınızdan başarıyla kaldırıldı.", 64, "Kaldırma İşlemi"\\n')
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