import tkinter as tk
from tkinter import ttk, messagebox
import os
from tkinterdnd2 import DND_FILES
from editor_tab import EditorTab

class TabManager:
    def __init__(self, parent_widget, on_tab_change, on_empty, on_file_drop, on_save_request, on_content_change):
        self.notebook = ttk.Notebook(parent_widget)
        self.notebook.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        self.notebook.bind("<<NotebookTabChanged>>", lambda e: on_tab_change())
        
        self.notebook.bind("<Button-3>", self.show_context_menu)
        self.notebook.bind("<Button-2>", self.on_middle_click_close)
        
        self.notebook.drop_target_register(DND_FILES)
        self.notebook.dnd_bind('<<Drop>>', on_file_drop)
        
        self.on_empty = on_empty
        self.on_save_request = on_save_request
        self.on_content_change = on_content_change

    def get_current_tab(self):
        current_tab_id = self.notebook.select()
        if not current_tab_id: return None
        return self.notebook.nametowidget(current_tab_id)

    def add_tab(self, tab_frame, title):
        self.notebook.add(tab_frame, text=f"{title}")
        self.notebook.select(tab_frame)
        tab_frame.text_area.edit_modified(False)

    def update_tab_text(self, tab_frame, title):
        for index in range(self.notebook.index("end")):
            if self.notebook.nametowidget(self.notebook.tabs()[index]) == tab_frame:
                current_text = self.notebook.tab(index, "text")
                if "⬤" in current_text:
                    self.notebook.tab(index, text=f"{title} ⬤")
                else:
                    self.notebook.tab(index, text=f"{title}")
                break

    def create_editor_tab(self, file_path=None, font_size=12): # GÜNCELLENDİ
        return EditorTab(self.notebook, file_path=file_path, on_change_callback=self.mark_as_modified, font_size=font_size)

    def mark_as_modified(self, tab):
        title = os.path.basename(tab.file_path) if tab.file_path else "Adsız"
        self.notebook.tab(tab, text=f"{title} ⬤")
        if hasattr(self, 'on_content_change') and self.on_content_change:
            self.on_content_change()

    def mark_as_saved(self, tab, title):
        tab.text_area.edit_modified(False)
        self.notebook.tab(tab, text=f"{title}")
        if hasattr(self, 'on_content_change') and self.on_content_change:
            self.on_content_change()

    def show_context_menu(self, event):
        try:
            index = self.notebook.index(f"@{event.x},{event.y}")
            self.notebook.select(index)
            menu = tk.Menu(self.notebook, tearoff=0, font=("Consolas", 10))
            menu.add_command(label="❌ Sekmeyi Kapat", command=lambda: self.close_tab_by_index(index))
            menu.post(event.x_root, event.y_root)
        except tk.TclError:
            pass 

    def on_middle_click_close(self, event):
        try:
            index = self.notebook.index(f"@{event.x},{event.y}")
            self.close_tab_by_index(index)
        except tk.TclError:
            pass

    def close_tab_by_index(self, index):
        tab_widget = self.notebook.nametowidget(self.notebook.tabs()[index])
        
        tab_text = self.notebook.tab(index, "text")
        if "⬤" in tab_text:
            title = os.path.basename(tab_widget.file_path) if tab_widget.file_path else "Adsız"
            cevap = messagebox.askyesnocancel("Kaydet", f"'{title}' dosyasında değişiklikler var.\nKapatmadan önce kaydetmek ister misiniz?")
            if cevap is None:
                return 
            elif cevap is True:
                if hasattr(self, 'on_save_request') and self.on_save_request:
                    success = self.on_save_request(tab_widget)
                    if not success:
                        return 
                
        self.notebook.forget(index)
        tab_widget.destroy() 
        if not self.notebook.tabs():
            self.on_empty()

    def apply_theme(self, is_dark):
        for tab_id in self.notebook.tabs():
            tab = self.notebook.nametowidget(tab_id)
            if isinstance(tab, EditorTab):
                tab.apply_theme(is_dark)