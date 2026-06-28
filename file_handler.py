import os
import tkinter as tk
from tkinter import filedialog, messagebox

class FileHandler:
    def __init__(self, app):
        self.app = app

    def on_closing(self):
        open_tabs = []
        for tab_frame in list(self.app.ui.tab_mgr.tabs.keys()):
            # HATA DÜZELTME 1 DEVAMI: Genel çıkışta da başlıkta "⬤" olup olmadığını kontrol ediyoruz
            tab_title = self.app.ui.tab_mgr.tabs[tab_frame]["title"]
            is_modified = "⬤" in tab_title
            
            if tab_frame.file_path and not tab_frame.is_temp_file:
                if is_modified:
                    self.app.file_mgr.write_file(tab_frame.file_path, tab_frame.get_code())
                open_tabs.append(tab_frame.file_path)
            elif is_modified:
                self.app.ui.tab_mgr.select_tab(tab_frame)
                cevap = messagebox.askyesno("Kapatılıyor", "Kaydedilmemiş 'Adsız' dosyalarınız var.\nYine de çıkılsın mı?")
                if not cevap:
                    return False
        
        self.app.file_mgr.save_open_tabs(open_tabs)
        return True

    def on_tab_change(self):
        self.update_title()
        self.update_line_count()

    def update_line_count(self):
        tab = self.app.ui.tab_mgr.get_current_tab()
        if tab:
            text = tab.get_code()
            lines = text.count('\n') + 1 if text else 1
            self.app.ui.line_count_label.config(text=f"Toplam Satır: {lines}")
        else:
            self.app.ui.line_count_label.config(text="Toplam Satır: 0")

    def save_file_by_tab(self, tab):
        if tab.file_path and not tab.is_temp_file:
            self.app.file_mgr.write_file(tab.file_path, tab.get_code())
            self.app.file_mgr.add_to_recent(tab.file_path)
            self.update_recent_combo()
            self.app.ui.tab_mgr.mark_as_saved(tab, os.path.basename(tab.file_path))
            self.app.write_output(f"--- Kaydedildi: {tab.file_path} ---\n")
            return True
        else:
            self.app.ui.tab_mgr.select_tab(tab)
            file_path = filedialog.asksaveasfilename(defaultextension=".py", filetypes=[("Python", "*.py")])
            if file_path:
                tab.file_path = file_path
                tab.is_temp_file = False
                self.app.file_mgr.write_file(tab.file_path, tab.get_code())
                self.app.file_mgr.add_to_recent(tab.file_path)
                self.update_recent_combo()
                self.app.ui.tab_mgr.mark_as_saved(tab, os.path.basename(tab.file_path))
                self.app.write_output(f"--- Kaydedildi: {tab.file_path} ---\n")
                self.update_title()
                return True
            return False

    def open_file_dialog(self):
        file_path = filedialog.askopenfilename(filetypes=[("Python", "*.py"), ("Tüm Dosyalar", "*.*")])
        if file_path: self.load_file(file_path)

    def load_file(self, file_path):
        norm_path = os.path.normpath(file_path)
        for tab_frame in self.app.ui.tab_mgr.tabs.keys():
            if tab_frame.file_path and os.path.normpath(tab_frame.file_path) == norm_path:
                self.app.ui.tab_mgr.select_tab(tab_frame)
                messagebox.showinfo("Bilgi", "Bu dosya zaten açık!")
                return

        try:
            content = self.app.file_mgr.read_file(file_path)
            current_tab = self.app.ui.tab_mgr.get_current_tab()
            
            if current_tab and not current_tab.file_path and len(current_tab.get_code().strip()) == 0:
                tab = current_tab
            else:
                tab = self.app.ui.tab_mgr.create_editor_tab(file_path, font_size=self.app.current_font_size, is_dark=self.app.is_dark_mode.get())
                self.app.ui.tab_mgr.add_tab(tab, os.path.basename(file_path))

            tab.load_code(content)
            tab.file_path = file_path
            tab.is_temp_file = False
            
            self.app.ui.tab_mgr.mark_as_saved(tab, os.path.basename(file_path))
            self.app.file_mgr.add_to_recent(file_path)
            self.update_title()
            self.update_recent_combo()
        except Exception as e:
            messagebox.showerror("Hata", f"Dosya açılamadı:\n{str(e)}")

    def on_drop(self, event):
        paths = self.app.root.tk.splitlist(event.data)
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
        display_list = ["Son Dosyalar..."] + [os.path.basename(f) for f in self.app.file_mgr.recent_files]
        self.app.ui.recent_combo['values'] = display_list
        self.app.ui.recent_combo.current(0)

    def on_recent_selected(self, event):
        idx = self.app.ui.recent_combo.current()
        if idx > 0:
            file_path = self.app.file_mgr.recent_files[idx - 1]
            if os.path.exists(file_path): self.load_file(file_path)
        self.app.ui.recent_combo.current(0)

    def new_file(self):
        tab = self.app.ui.tab_mgr.create_editor_tab(font_size=self.app.current_font_size, is_dark=self.app.is_dark_mode.get())
        self.app.ui.tab_mgr.add_tab(tab, "Adsız")
        self.update_title()

    def save_file(self):
        tab = self.app.ui.tab_mgr.get_current_tab()
        if not tab: return
        self.save_file_by_tab(tab)

    def save_as_file(self):
        tab = self.app.ui.tab_mgr.get_current_tab()
        if not tab: return
        file_path = filedialog.asksaveasfilename(defaultextension=".py", filetypes=[("Python", "*.py")])
        if file_path:
            tab.file_path = file_path
            tab.is_temp_file = False
            self.save_file()
            self.update_title()

    def update_title(self):
        tab = self.app.ui.tab_mgr.get_current_tab()
        if tab:
            title = tab.file_path if tab.file_path else "Adsız"
            self.app.root.title(f"Python Self Editör - {title}")
        else:
            self.app.root.title("Python Self Editör")