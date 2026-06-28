import tkinter as tk
from tkinter import messagebox
import os
from tkinterdnd2 import DND_FILES
from editor_tab import EditorTab

class MockNotebook(tk.Frame):
    def __init__(self, parent, tab_mgr, **kwargs):
        super().__init__(parent, **kwargs)
        self.tab_mgr = tab_mgr

    def tabs(self):
        return tuple(str(id(t)) for t in self.tab_mgr.tabs.keys())

    def nametowidget(self, tab_id):
        for t in self.tab_mgr.tabs.keys():
            if str(id(t)) == str(tab_id):
                return t
        return None

    def tab(self, tab_id, option=None, **kwargs):
        if option == "text":
            tab_widget = self.nametowidget(tab_id)
            if tab_widget in self.tab_mgr.tabs:
                return self.tab_mgr.tabs[tab_widget]["title"]
            return ""
        return {}

    def select(self, tab_id=None):
        if tab_id is None:
            return str(id(self.tab_mgr.current_tab)) if self.tab_mgr.current_tab else ""
        tab_widget = self.nametowidget(tab_id) if isinstance(tab_id, str) else tab_id
        if tab_widget:
            self.tab_mgr.select_tab(tab_widget)
            
    def forget(self, tab_id):
        tab_widget = self.nametowidget(tab_id) if isinstance(tab_id, str) else tab_id
        if tab_widget:
            tab_widget.pack_forget()

class TabManager:
    def __init__(self, parent_widget, on_tab_change, on_empty, on_file_drop, on_save_request, on_content_change):
        self.on_tab_change_cb = on_tab_change
        self.on_empty = on_empty
        self.on_save_request = on_save_request
        self.on_content_change = on_content_change
        
        self.header_frame = tk.Frame(parent_widget, bg="#1E1F1C", bd=0, highlightthickness=0)
        self.header_frame.pack(side=tk.TOP, fill=tk.X)
        
        self.btn_left = tk.Button(self.header_frame, text="◄", command=self.scroll_left, bg="#333333", fg="white", relief=tk.FLAT, padx=5, cursor="hand2", takefocus=0)
        
        self.canvas = tk.Canvas(self.header_frame, height=28, bg="#1E1F1C", highlightthickness=0, bd=0, takefocus=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.btn_right = tk.Button(self.header_frame, text="►", command=self.scroll_right, bg="#333333", fg="white", relief=tk.FLAT, padx=5, cursor="hand2", takefocus=0)
        
        self.tab_container = tk.Frame(self.canvas, bg="#1E1F1C", bd=0, highlightthickness=0)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.tab_container, anchor="nw")
        
        self.tab_container.bind("<Configure>", self._update_scroll_buttons)
        self.canvas.bind("<Configure>", self._update_scroll_buttons)
        
        self.notebook = MockNotebook(parent_widget, self, bd=0, highlightthickness=0, bg="#1E1F1C")
        self.notebook.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        self.notebook.drop_target_register(DND_FILES)
        self.notebook.dnd_bind('<<Drop>>', on_file_drop)
        
        self.tabs = {} 
        self.current_tab = None

    def _update_scroll_buttons(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        tw = self.tab_container.winfo_reqwidth()
        cw = self.canvas.winfo_width()
        if tw > cw and cw > 10: 
            if not self.btn_left.winfo_ismapped():
                self.btn_left.pack(side=tk.LEFT, fill=tk.Y, before=self.canvas)
                self.btn_right.pack(side=tk.RIGHT, fill=tk.Y, after=self.canvas)
        else:
            if self.btn_left.winfo_ismapped():
                self.btn_left.pack_forget()
                self.btn_right.pack_forget()
            self.canvas.xview_moveto(0) 

    def scroll_left(self): self.canvas.xview_scroll(-3, "units")
    def scroll_right(self): self.canvas.xview_scroll(3, "units")
    def get_current_tab(self): return self.current_tab

    def create_editor_tab(self, file_path=None, font_size=12, is_dark=True):
        return EditorTab(self.notebook, file_path=file_path, on_change_callback=self.mark_as_modified, font_size=font_size, is_dark=is_dark)

    def add_tab(self, tab_frame, title):
        btn_frame = tk.Frame(self.tab_container, bg="#555555", cursor="hand2")
        btn_frame.pack(side=tk.LEFT, padx=1, pady=(2,0))
        
        display_title = title if len(title) <= 15 else title[:12] + "..."
        lbl = tk.Label(btn_frame, text=display_title, width=15, anchor="w", bg="#555555", fg="white", font=("Consolas", 9), cursor="hand2")
        lbl.pack(side=tk.LEFT, padx=(5,0), pady=4)
        
        close_btn = tk.Label(btn_frame, text="✖", bg="#555555", fg="#AAAAAA", font=("Consolas", 8), cursor="hand2")
        close_btn.pack(side=tk.RIGHT, padx=5)
        
        for w in (btn_frame, lbl):
            w.bind("<Button-1>", lambda e, tf=tab_frame: self.select_tab(tf))
            w.bind("<Button-2>", lambda e, tf=tab_frame: self.close_tab(tf))
            w.bind("<Button-3>", lambda e, tf=tab_frame: self.show_context_menu(e, tf))
        
        close_btn.bind("<Button-1>", lambda e, tf=tab_frame: self.close_tab(tf))
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg="#FF5555"))
        close_btn.bind("<Leave>", lambda e: close_btn.config(fg="#AAAAAA"))
        
        self.tabs[tab_frame] = {"frame": btn_frame, "lbl": lbl, "title": title}
        self.select_tab(tab_frame)
        tab_frame.text_area.edit_modified(False)
        self._update_scroll_buttons()

    def select_tab(self, tab_frame):
        if self.current_tab and self.current_tab != tab_frame:
            self.current_tab.pack_forget() 
            
        self.current_tab = tab_frame
        tab_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True) 
        
        for tf, tab_data in self.tabs.items():
            bg_color = "#007ACC" if tf == tab_frame else "#555555"
            tab_data["frame"].config(bg=bg_color)
            tab_data["lbl"].config(bg=bg_color)
            tab_data["frame"].winfo_children()[1].config(bg=bg_color) 
            
        self.on_tab_change_cb()

        # --- YENİ EKLENEN KISIM: Seçilen sekme görüş alanına otomatik kaydırılır ---
        self.header_frame.after(50, lambda: self._ensure_tab_visible(tab_frame))

    # Taşma varsa aktif sekmeyi bulan ve canvas'ı o hizaya kaydıran mantık motoru
    def _ensure_tab_visible(self, tab_frame):
        if tab_frame not in self.tabs: return
        self.canvas.update_idletasks()
        
        btn_frame = self.tabs[tab_frame]["frame"]
        btn_x = btn_frame.winfo_x()
        btn_w = btn_frame.winfo_width()
        
        canvas_w = self.canvas.winfo_width()
        scroll_w = self.tab_container.winfo_width()
        
        if scroll_w <= canvas_w:
            self.canvas.xview_moveto(0)
            return
            
        view_start_frac, view_end_frac = self.canvas.xview()
        visible_x_start = view_start_frac * scroll_w
        visible_x_end = view_end_frac * scroll_w
        
        # Eğer sekme sol tarafta gizlenmişse sola kaydır
        if btn_x < visible_x_start:
            self.canvas.xview_moveto(btn_x / scroll_w)
        # Eğer sekme sağ tarafta taşmışsa sağa kaydır
        elif (btn_x + btn_w) > visible_x_end:
            new_start = (btn_x + btn_w - canvas_w) / scroll_w
            self.canvas.xview_moveto(new_start)
    # --------------------------------------------------------------------------------

    def update_tab_text(self, tab_frame, title):
        if tab_frame in self.tabs:
            self.tabs[tab_frame]["title"] = title
            display_title = title if len(title) <= 15 else title[:12] + "..."
            self.tabs[tab_frame]["lbl"].config(text=display_title)
            
    def mark_as_modified(self, tab):
        title = os.path.basename(tab.file_path) if tab.file_path else "Adsız"
        self.update_tab_text(tab, f"⬤ {title}")
        if self.on_content_change: self.on_content_change()

    def mark_as_saved(self, tab, title):
        tab.text_area.edit_modified(False)
        self.update_tab_text(tab, title)
        if self.on_content_change: self.on_content_change()

    def show_context_menu(self, event, tab_frame):
        menu = tk.Menu(self.header_frame, tearoff=0, font=("Consolas", 10))
        menu.add_command(label="❌ Sekmeyi Kapat", command=lambda: self.close_tab(tab_frame))
        menu.post(event.x_root, event.y_root)

    def close_tab(self, tab_frame):
        if tab_frame not in self.tabs: return
        
        if "⬤" in self.tabs[tab_frame]["title"]:
            clean_title = os.path.basename(tab_frame.file_path) if tab_frame.file_path else "Adsız"
            self.select_tab(tab_frame)
            cevap = messagebox.askyesnocancel("Kaydet", f"'{clean_title}' dosyasında değişiklikler var.\nKapatmadan önce kaydetmek ister misiniz?")
            if cevap is None: return 
            elif cevap is True:
                if hasattr(self, 'on_save_request') and self.on_save_request:
                    success = self.on_save_request(tab_frame)
                    if not success: return 
        
        tab_frame.pack_forget()
        self.tabs[tab_frame]["frame"].destroy()
        del self.tabs[tab_frame]
        tab_frame.destroy()
        
        self._update_scroll_buttons()
        
        remaining_tabs = list(self.tabs.keys())
        if remaining_tabs:
            self.select_tab(remaining_tabs[-1])
        else:
            self.current_tab = None
            self.on_empty()

    def next_tab(self, event=None):
        tabs = list(self.tabs.keys())
        if not tabs: return "break"
        if self.current_tab in tabs:
            idx = tabs.index(self.current_tab)
            next_idx = (idx + 1) % len(tabs)
            self.select_tab(tabs[next_idx])
        return "break"

    def prev_tab(self, event=None):
        tabs = list(self.tabs.keys())
        if not tabs: return "break"
        if self.current_tab in tabs:
            idx = tabs.index(self.current_tab)
            prev_idx = (idx - 1) % len(tabs)
            self.select_tab(tabs[prev_idx])
        return "break"

    def apply_theme(self, is_dark):
        bg_color = "#1E1F1C" if is_dark else "#F0F0F0"
        btn_bg = "#555555" if is_dark else "#CCCCCC"
        fg_color = "white" if is_dark else "black"
        active_bg = "#007ACC"
        
        self.header_frame.config(bg=bg_color)
        self.canvas.config(bg=bg_color)
        self.tab_container.config(bg=bg_color)
        self.btn_left.config(bg=btn_bg, fg=fg_color)
        self.btn_right.config(bg=btn_bg, fg=fg_color)
        self.notebook.config(bg=bg_color)
        
        for tf, tab_data in self.tabs.items():
            current_bg = active_bg if tf == self.current_tab else btn_bg
            tab_data["frame"].config(bg=current_bg)
            tab_data["lbl"].config(bg=current_bg, fg="white" if tf == self.current_tab else fg_color)
            tab_data["frame"].winfo_children()[1].config(bg=current_bg)
        
        for tab_frame in self.tabs.keys():
            if isinstance(tab_frame, EditorTab):
                tab_frame.apply_theme(is_dark)