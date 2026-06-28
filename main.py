# main.py
import tkinter as tk
from tkinter import messagebox
import os
import multiprocessing
from tkinterdnd2 import TkinterDnD

from event_bus import EventBus

from env_manager import EnvManager
from file_manager import FileManager
from ui_manager import UIManager

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
        
        self.env_mgr = EnvManager()
        self.file_mgr = FileManager(self.env_mgr.venv_base_dir)
        
        self.settings = self.file_mgr.load_settings()
        self.is_dark_mode = tk.BooleanVar(value=self.settings.get("is_dark_mode", True))
        self.current_font_size = self.settings.get("font_size", 12)
        
        self._setup_event_subscriptions()
        self._setup_shortcuts()
        
        self.file_handler = FileHandler(self)
        self.env_handler = EnvHandler(self)
        self.run_handler = RunHandler(self)
        self.search_handler = SearchHandler()
        
        self.ui = UIManager(self.root, self)
        
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

    def _setup_event_subscriptions(self):
        EventBus.subscribe("ui:write_output", self.write_output)
        EventBus.subscribe("ui:clear_output", self.clear_output)
        EventBus.subscribe("env:refresh_libs", self.refresh_libraries_list)
        EventBus.subscribe("file:save_request", self.save_file_by_tab)
        
        EventBus.subscribe("ui:start_progress", self.start_progress)
        EventBus.subscribe("ui:stop_progress", self.stop_progress)
        
        EventBus.subscribe("ui:set_title", self.root.title)
        EventBus.subscribe("ui:set_line_count", lambda lines: self.ui.line_count_label.config(text=f"Toplam Satır: {lines}"))
        EventBus.subscribe("ui:update_recent_combo", self._update_recent_combo_ui)
        EventBus.subscribe("ui:reset_recent_combo", lambda: self.ui.recent_combo.current(0))
        
        EventBus.subscribe("tab:changed", self.on_tab_change)
        EventBus.subscribe("tab:empty", self.new_file)
        EventBus.subscribe("file:dropped", self.on_drop)
        EventBus.subscribe("tab:content_changed", self.update_line_count)

    def _update_recent_combo_ui(self, display_list):
        self.ui.recent_combo['values'] = display_list
        self.ui.recent_combo.current(0)

    def start_progress(self):
        self.ui.progress_bar.pack(side=tk.LEFT, padx=5)
        self.ui.progress_bar.start(10)
        
    def stop_progress(self):
        self.ui.progress_bar.stop()
        self.ui.progress_bar.pack_forget()

    def _setup_shortcuts(self):
        self.root.bind("<Control-s>", lambda e: self.save_file())
        self.root.bind("<Control-S>", lambda e: self.save_as_file()) 
        self.root.bind("<Control-n>", lambda e: self.new_file())
        self.root.bind("<Control-N>", lambda e: self.new_file())
        self.root.bind("<Control-r>", lambda e: self.run_code())
        self.root.bind("<Control-R>", lambda e: self.run_code())
        self.root.bind("<Control-b>", lambda e: self.compile_code())
        self.root.bind("<Control-B>", lambda e: self.compile_code())
        self.root.bind("<Control-f>", lambda e: self.ui.search_entry.focus_set())
        self.root.bind("<Control-F>", lambda e: self.ui.search_entry.focus_set())
        
        self.root.bind_all("<Control-MouseWheel>", self.on_zoom)
        self.root.bind_all("<Control-Button-4>", self.on_zoom_in)  
        self.root.bind_all("<Control-Button-5>", self.on_zoom_out) 

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

    def on_zoom_in(self, event): self.change_font_size(1); return "break"
    def on_zoom_out(self, event): self.change_font_size(-1); return "break"

    def on_closing(self):
        if self.file_handler.on_closing(): 
            self.run_handler.cleanup_temp_files() 
            self.root.destroy()
            
    def show_donation(self):
        messagebox.showinfo("Bağış", "Desteğiniz için teşekkür ederiz!", parent=self.root)

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
    
    def clear_output(self): self.ui.output_screen.delete("1.0", tk.END)
    def write_output(self, text): 
        self.ui.output_screen.insert(tk.END, text)
        self.ui.output_screen.see(tk.END)
        
    def poll_queue(self): self.run_handler.poll_queue()

if __name__ == "__main__":
    multiprocessing.freeze_support() 
    root = TkinterDnD.Tk()
    app = PythonIDE(root)
    root.mainloop()