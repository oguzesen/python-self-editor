import tkinter as tk
import os
import multiprocessing
from tkinterdnd2 import TkinterDnD

# --- ALT YÖNETİCİLER ---
from env_manager import EnvManager
from file_manager import FileManager
from ui_manager import UIManager

# --- MODÜLLER ---
from file_handler import FileHandler
from env_handler import EnvHandler
from run_handler import RunHandler
from search_handler import SearchHandler

class PythonIDE:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Self Editör - Adsız")
        self.root.geometry("1200x800")
        
        try:
            self.root.state('zoomed')
        except:
            self.root.attributes('-zoomed', True) 
            
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        try:
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ikon1.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(default=icon_path)
        except:
            pass
        
        # --- BAĞIMLILIKLAR VE AYARLARIN YÜKLENMESİ ---
        self.env_mgr = EnvManager()
        self.file_mgr = FileManager(self.env_mgr.venv_base_dir)
        
        self.settings = self.file_mgr.load_settings()
        self.is_dark_mode = tk.BooleanVar(value=self.settings.get("is_dark_mode", True))
        self.current_font_size = self.settings.get("font_size", 12)
        
        # --- KISAYOLLAR ---
        self.root.bind("<Control-s>", lambda event: self.save_file())
        self.root.bind("<Control-S>", lambda event: self.save_as_file()) 
        self.root.bind("<Control-n>", lambda event: self.new_file())
        self.root.bind("<Control-N>", lambda event: self.new_file())
        self.root.bind("<Control-r>", lambda event: self.run_code())
        self.root.bind("<Control-R>", lambda event: self.run_code())
        self.root.bind("<Control-b>", lambda event: self.compile_code())
        self.root.bind("<Control-B>", lambda event: self.compile_code())
        self.root.bind("<Control-f>", lambda event: self.ui.search_entry.focus_set())
        self.root.bind("<Control-F>", lambda event: self.ui.search_entry.focus_set())
        
        self.root.bind_all("<Control-MouseWheel>", self.on_zoom)
        self.root.bind_all("<Control-Button-4>", self.on_zoom_in)  
        self.root.bind_all("<Control-Button-5>", self.on_zoom_out) 
        
        # --- ALT MODÜLLERİN (HANDLERS) BAŞLATILMASI ---
        self.file_handler = FileHandler(self)
        self.env_handler = EnvHandler(self)
        self.run_handler = RunHandler(self)
        self.search_handler = SearchHandler(self)
        
        # Arayüz Yükleniyor
        self.ui = UIManager(self.root, self)
        
        # Arayüz yüklendikten sonra tanımlanması gereken kısayollar
        self.root.bind("<Control-Tab>", lambda event: self.ui.tab_mgr.next_tab(event))
        self.root.bind("<Control-Shift-Tab>", lambda event: self.ui.tab_mgr.prev_tab(event))
        
        # Bileşenleri güncelle ve sistemi hazırla
        self.refresh_env_list()
        self.refresh_libraries_list()
        self.update_recent_combo()
        self.poll_queue()
        
        saved_tabs = self.file_mgr.load_open_tabs()
        if saved_tabs:
            for path in saved_tabs:
                if os.path.exists(path):
                    self.load_file(path)
            if not self.ui.tab_mgr.notebook.tabs():
                self.new_file()
        else:
            self.new_file() 
            
        self.update_status()

    # --- ÖZELLİKLER VE AYARLAR ---
    @property
    def runner(self):
        return self.run_handler.runner

    def toggle_theme(self):
        self.ui.apply_theme(self.is_dark_mode.get())
        self.settings["is_dark_mode"] = self.is_dark_mode.get()
        self.file_mgr.save_settings(self.settings)

    def on_zoom(self, event):
        if event.delta > 0: self.change_font_size(1)
        else: self.change_font_size(-1)
        return "break" 

    def on_zoom_in(self, event):
        self.change_font_size(1)
        return "break"

    def on_zoom_out(self, event):
        self.change_font_size(-1)
        return "break"

    def change_font_size(self, delta):
        new_size = self.current_font_size + delta
        if 8 <= new_size <= 48:
            self.current_font_size = new_size
            self.settings["font_size"] = self.current_font_size
            self.file_mgr.save_settings(self.settings)
            
            for tab_id in self.ui.tab_mgr.notebook.tabs():
                tab = self.ui.tab_mgr.notebook.nametowidget(tab_id)
                if hasattr(tab, 'set_font_size'):
                    tab.set_font_size(self.current_font_size)

    def show_donation(self):
        don_win = tk.Toplevel(self.root)
        don_win.title("Projeye Destek Olun")
        don_win.geometry("450x220")
        don_win.resizable(False, False)
        don_win.transient(self.root)
        don_win.grab_set()
        
        bg_color = "#272822" if self.is_dark_mode.get() else "#f0f0f0"
        fg_color = "white" if self.is_dark_mode.get() else "black"
        don_win.configure(bg=bg_color)

        tk.Label(don_win, text="Python Self Editör'ü Sevdiyseniz...", font=("Arial", 12, "bold"), bg=bg_color, fg=fg_color).pack(pady=(15, 5))
        tk.Label(don_win, text="Bu proje tamamen ücretsiz ve açık kaynaklıdır.\nGeliştiriciye destek olmak isterseniz\naşağıdaki kripto cüzdan adresini kullanabilirsiniz:", bg=bg_color, fg=fg_color).pack(pady=5)

        btc_frame = tk.Frame(don_win, bg=bg_color)
        btc_frame.pack(pady=10)
        tk.Label(btc_frame, text="BTC:", font=("Arial", 10, "bold"), bg=bg_color, fg=fg_color).pack(side=tk.LEFT)
        
        btc_entry = tk.Entry(btc_frame, width=42, bg="#DDDDDD", fg="black", font=("Consolas", 10, "bold"), cursor="hand2")
        btc_entry.insert(0, "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
        btc_entry.config(state="readonly")
        btc_entry.pack(side=tk.LEFT, padx=5)

        def copy_to_clipboard(event):
            self.root.clipboard_clear()
            self.root.clipboard_append("...")
            import tkinter.messagebox as messagebox
            messagebox.showinfo("Kopyalandı", "Adres panoya kopyalandı!", parent=don_win)

        btc_entry.bind("<Button-1>", copy_to_clipboard)
        tk.Button(don_win, text="Kapat", command=don_win.destroy, bg="#555555", fg="white", relief=tk.FLAT, width=12).pack(pady=(5, 10))

    # =======================================================
    # UI BİLEŞENLERİ İÇİN ALT MODÜLLERE YÖNLENDİRME (PROXY)
    # =======================================================
    def on_closing(self):
        if self.file_handler.on_closing(): 
            self.run_handler.cleanup_temp_files() 
            self.root.destroy()
        
    def open_terminal(self): self.run_handler.open_terminal()
    def open_file_dialog(self): self.file_handler.open_file_dialog()
    def load_file(self, file_path): self.file_handler.load_file(file_path)
    def on_drop(self, event): self.file_handler.on_drop(event)
    def update_recent_combo(self): self.file_handler.update_recent_combo()
    def on_recent_selected(self, event): self.file_handler.on_recent_selected(event)
    def new_file(self): self.file_handler.new_file()
    def save_file(self): self.file_handler.save_file()
    def save_as_file(self): self.file_handler.save_as_file()
    def update_title(self): self.file_handler.update_title()
    def save_file_by_tab(self, tab): return self.file_handler.save_file_by_tab(tab)
    def on_tab_change(self): self.file_handler.on_tab_change()
    def update_line_count(self): self.file_handler.update_line_count()

    def update_status(self): self.env_handler.update_status()
    def refresh_env_list(self): self.env_handler.refresh_env_list()
    def on_env_selected(self, event): self.env_handler.on_env_selected(event)
    def show_env_context(self, event): self.env_handler.show_env_context(event)
    def delete_env(self, env_name): self.env_handler.delete_env(env_name)
    def refresh_libraries_list(self): self.env_handler.refresh_libraries_list()
    def on_lib_selected(self, event): self.env_handler.on_lib_selected(event)
    def install_lib_live(self, lib_name): self.env_handler.install_lib_live(lib_name)
    def show_lib_context(self, event): self.env_handler.show_lib_context(event)
    def uninstall_lib(self, lib_name): self.env_handler.uninstall_lib(lib_name)
    def change_python_path(self, event): self.env_handler.change_python_path(event)

    def compile_code(self): self.run_handler.compile_code()
    def run_code(self): self.run_handler.run_code()
    def clear_output(self): self.run_handler.clear_output()
    def write_output(self, text): self.run_handler.write_output(text)
    def on_process_finished(self, event_type): self.run_handler.on_process_finished(event_type)
    def poll_queue(self): self.run_handler.poll_queue()

if __name__ == "__main__":
    multiprocessing.freeze_support() 
    root = TkinterDnD.Tk()
    app = PythonIDE(root)
    root.mainloop()