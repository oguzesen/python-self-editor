import tkinter as tk
from tkinter import filedialog, messagebox
import os
import sys
from pathlib import Path

# Yeni Modüllerimiz
from compiler_scanner import DependencyScanner
from compiler_builder import CompilerBuilder

def get_ide_base_path():
    if getattr(sys, 'frozen', False): return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

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

    def build(self):
        if not self.target_file:
            messagebox.showwarning("Uyarı", "Derlenecek dosya bulunamadı! Lütfen önce dosyanızı diske kaydedin.", parent=self)
            return
            
        final_icon_path = None
        setup_icon_path = None
        
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
                
        work_dir = os.path.dirname(self.target_file)
        scanned_imports = DependencyScanner.scan(work_dir)
        custom_app_name = self.app_name_var.get().strip()
        setup_desc_text = self.setup_desc.get("1.0", tk.END).strip()

        builder = CompilerBuilder(self.app, self)
        builder.start_build(
            target_file=self.target_file,
            final_icon_path=final_icon_path,
            setup_icon_path=setup_icon_path,
            custom_app_name=custom_app_name,
            no_console=self.no_console_var.get(),
            added_files=self.added_files,
            scanned_imports=scanned_imports,
            create_setup=self.create_setup_var.get(),
            setup_desc_text=setup_desc_text
        )