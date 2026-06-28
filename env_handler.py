import os
import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog

class EnvHandler:
    def __init__(self, app):
        self.app = app

    def update_status(self):
        self.app.ui.status_bar.config(text=f"Ortam: [{self.app.env_mgr.current_env}] | Python: {self.app.env_mgr.python_path}")

    def refresh_env_list(self):
        self.app.ui.env_combo['values'] = self.app.env_mgr.get_environment_list()
        self.app.ui.env_combo.set(self.app.env_mgr.current_env)

    def on_env_selected(self, event):
        selection = self.app.ui.env_combo.get()
        if selection == "+ Yeni Ortam Oluştur...":
            env_name = simpledialog.askstring("Yeni Ortam", "Sanal ortam için bir isim girin:")
            if env_name:
                self.app.ui.progress_bar.pack(side=tk.LEFT, padx=5)
                self.app.ui.progress_bar.start(10)
                self.app.ui.env_combo.config(state="disabled")
                self.app.env_mgr.create_venv_async(env_name, lambda n: self.app.root.after(0, self._venv_success, n), lambda e: self.app.root.after(0, self._venv_error, e))
            else:
                self.app.ui.env_combo.set(self.app.env_mgr.current_env)
        else:
            success, err_path = self.app.env_mgr.select_environment(selection)
            if success:
                self.update_status()
                self.refresh_libraries_list() 
            else:
                messagebox.showerror("Hata", f"Ortam bozuk veya python.exe bulunamad!\n{err_path}")
                self.app.ui.env_combo.set(self.app.env_mgr.current_env)

    def _venv_success(self, env_name):
        self.app.ui.progress_bar.stop(); self.app.ui.progress_bar.pack_forget()
        self.app.ui.env_combo.config(state="readonly")
        self.refresh_env_list()
        self.app.ui.env_combo.set(env_name)
        self.on_env_selected(None)

    def _venv_error(self, err_msg):
        self.app.ui.progress_bar.stop(); self.app.ui.progress_bar.pack_forget()
        self.app.ui.env_combo.config(state="readonly")
        messagebox.showerror("Hata", err_msg)
        self.app.ui.env_combo.set(self.app.env_mgr.current_env)

    def show_env_context(self, event):
        selection = self.app.ui.env_combo.get()
        if selection not in ["Yerel", "+ Yeni Ortam Oluştur...", "Manuel", ""]:
            menu = tk.Menu(self.app.root, tearoff=0)
            menu.add_command(label=f"'{selection}' Ortamını Sil", command=lambda: self.delete_env(selection))
            menu.tk_popup(event.x_root, event.y_root)

    def delete_env(self, env_name):
        if messagebox.askyesno("Onay", f"'{env_name}' ortamını tamamen silmek istediğinize emin misiniz?"):
            self.app.ui.progress_bar.pack(side=tk.LEFT, padx=5)
            self.app.ui.progress_bar.start(10)
            self.app.ui.env_combo.config(state="disabled")
            self.app.env_mgr.delete_venv_async(env_name, lambda n: self.app.root.after(0, self._delete_env_success, n), lambda e: self.app.root.after(0, self._venv_error, e))

    def _delete_env_success(self, env_name):
        self.app.ui.progress_bar.stop(); self.app.ui.progress_bar.pack_forget()
        self.app.ui.env_combo.config(state="readonly")
        
        if self.app.env_mgr.current_env == env_name:
            self.app.ui.env_combo.set("Yerel")
            self.on_env_selected(None) 
        
        self.refresh_env_list()
        messagebox.showinfo("Başarılı", f"'{env_name}' ortamı silindi.")

    def refresh_libraries_list(self):
        self.app.ui.lib_combo['values'] = ["Yükleniyor..."]
        self.app.ui.lib_combo.current(0)
        self.app.env_mgr.fetch_libraries_async(lambda libs: self.app.root.after(0, lambda: self._update_lib_combo(libs)))

    def _update_lib_combo(self, lib_list):
        self.app.ui.lib_combo['values'] = lib_list
        self.app.ui.lib_combo.current(0)

    def on_lib_selected(self, event):
        if self.app.ui.lib_combo.current() == 0: 
            lib_name = simpledialog.askstring("Pip Install", f"[{self.app.env_mgr.current_env}] ortamına kurulacak kütüphane adı:")
            if lib_name: 
                self.install_lib_live(lib_name)

    def install_lib_live(self, lib_name):
        self.app.ui.progress_bar.pack(side=tk.LEFT, padx=5)
        self.app.ui.progress_bar.start(10)
        self.app.clear_output()
        self.app.write_output(f"--- '{lib_name}' Kurulumu Başlatılıyor... Lütfen Bekleyin ---\n")
        cmd = [self.app.env_mgr.python_path, "-m", "pip", "install", lib_name]
        self.app.runner.run(cmd, is_pip=True)

    def show_lib_context(self, event):
        selection = self.app.ui.lib_combo.get()
        if selection not in ["+ Kütüphane Ekle", "Yükleniyor...", "Hata!", ""]:
            menu = tk.Menu(self.app.root, tearoff=0)
            menu.add_command(label=f"'{selection}' Kaldır", command=lambda: self.uninstall_lib(selection))
            menu.tk_popup(event.x_root, event.y_root)

    def uninstall_lib(self, lib_name):
        if messagebox.askyesno("Onay", f"'{lib_name}' kütüphanesini kaldırmak istediğinize emin misiniz?"):
            self.app.ui.progress_bar.pack(side=tk.LEFT, padx=5)
            self.app.ui.progress_bar.start(10)
            self.app.clear_output()
            self.app.write_output(f"--- '{lib_name}' Kaldırılıyor... ---\n")
            cmd = [self.app.env_mgr.python_path, "-m", "pip", "uninstall", "-y", lib_name]
            self.app.runner.run(cmd, is_pip=True)

    def change_python_path(self, event):
        new_path = filedialog.askopenfilename(title="Derleyici Seçin", filetypes=[("Yürütülebilir Dosya", "*.exe"), ("Tüm Dosyalar", "*.*")])
        if new_path:
            self.app.env_mgr.python_path = new_path
            self.app.env_mgr.current_env = "Manuel"
            self.update_status()