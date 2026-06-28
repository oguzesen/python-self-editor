# ui_manager.py
import tkinter as tk
from tkinter import ttk
from tab_manager import TabManager
from event_bus import EventBus

class UIManager:
    def __init__(self, root, app):
        self.root = root
        self.app = app
        
        self.theme_labels = []
        self.panel_labels = []
        self.theme_buttons = []
        self.search_checks = [] 
        
        self.setup_ui()
        self.apply_theme(self.app.is_dark_mode.get()) 
        
        self.root.after(100, self._adjust_initial_sash)
        
        EventBus.subscribe("ui:select_tab", lambda tab: self.tab_mgr.select_tab(tab))
        EventBus.subscribe("ui:clear_search_highlights", self._clear_all_highlights)

    def _adjust_initial_sash(self):
        try:
            self.root.update_idletasks()
            total_h = self.main_pane.winfo_height()
            target_y = total_h - 200
            if target_y > 100:
                self.main_pane.sash_place(0, 0, target_y)
        except Exception:
            pass

    def _clear_all_highlights(self):
        for t in self.tab_mgr.tabs.keys():
            t.text_area.tag_remove("search_highlight", "1.0", tk.END)

    def _trigger_search(self, forward=True):
        EventBus.publish("search:do_find", 
            forward,
            self.search_entry.get(),
            self.search_match_case.get(),
            self.search_whole_word.get(),
            self.search_all_tabs.get(),
            self.tab_mgr.get_current_tab(),
            self.tab_mgr.tabs
        )

    def setup_ui(self):
        self.top_frame = tk.Frame(self.root, pady=5, padx=5)
        self.top_frame.pack(side=tk.TOP, fill=tk.X)
        
        self.theme_check = tk.Checkbutton(self.top_frame, text="🌙 Gece Modu", variable=self.app.is_dark_mode, command=self.app.toggle_theme)
        self.theme_check.pack(side=tk.RIGHT, padx=10)
        
        btn_donate = tk.Button(self.top_frame, text="💖 Bağış", command=self.app.show_donation, bg="#FF1493", fg="white", font=("Consolas", 10, "bold"), relief=tk.FLAT, padx=8)
        btn_donate.pack(side=tk.RIGHT, padx=(0, 5))
        
        btn_yeni = tk.Button(self.top_frame, text="+", command=self.app.new_file, bg="#007ACC", fg="white", font=("Arial", 12, "bold"), relief=tk.FLAT, padx=4, pady=0)
        btn_yeni.pack(side=tk.LEFT, padx=(2, 5))
        
        btn_ac = tk.Button(self.top_frame, text="Aç", command=self.app.open_file_dialog, bg="#FFD700", fg="black", font=("Consolas", 10, "bold"), relief=tk.FLAT, padx=8)
        btn_ac.pack(side=tk.LEFT, padx=(0, 10))
        
        self.recent_combo = ttk.Combobox(self.top_frame, state="readonly", width=15)
        self.recent_combo.pack(side=tk.LEFT, padx=2)
        self.recent_combo.bind("<<ComboboxSelected>>", self.app.on_recent_selected)

        btn_kaydet = tk.Button(self.top_frame, text="Kaydet", command=self.app.save_file, relief=tk.FLAT, padx=5)
        btn_kaydet.pack(side=tk.LEFT, padx=2)
        btn_fkaydet = tk.Button(self.top_frame, text="Farklı Kaydet", command=self.app.save_as_file, relief=tk.FLAT, padx=5)
        btn_fkaydet.pack(side=tk.LEFT, padx=2)
        
        self.theme_buttons.extend([btn_kaydet, btn_fkaydet])
        
        lbl_param = tk.Label(self.top_frame, text="Parametre:")
        lbl_param.pack(side=tk.LEFT, padx=2)
        self.theme_labels.append(lbl_param)
        
        self.args_entry = tk.Entry(self.top_frame, width=10)
        self.args_entry.pack(side=tk.LEFT, padx=2)
        
        tk.Button(self.top_frame, text="▶ Çalıştır", command=self.app.run_code, bg="#A6E22E", fg="black", relief=tk.FLAT, padx=10).pack(side=tk.LEFT, padx=15)
        tk.Button(self.top_frame, text="⚙ Derle", command=self.app.compile_code, bg="#FD971F", fg="black", relief=tk.FLAT, padx=8).pack(side=tk.LEFT, padx=2)
        
        lbl_ortam = tk.Label(self.top_frame, text="Ortam:", fg="#66D9EF", font=("Consolas", 9, "bold"))
        lbl_ortam.pack(side=tk.LEFT, padx=(10, 2))
        self.theme_labels.append(lbl_ortam)
        
        self.env_combo = ttk.Combobox(self.top_frame, state="readonly", width=25)
        self.env_combo.pack(side=tk.LEFT, padx=2)
        self.env_combo.bind("<<ComboboxSelected>>", self.app.on_env_selected)
        self.env_combo.bind("<Button-3>", self.app.show_env_context)

        lbl_lib = tk.Label(self.top_frame, text="Kütüphaneler:", fg="#FD971F", font=("Consolas", 9, "bold"))
        lbl_lib.pack(side=tk.LEFT, padx=(5, 2))
        self.theme_labels.append(lbl_lib)
        
        self.lib_combo = ttk.Combobox(self.top_frame, state="readonly", width=25)
        self.lib_combo.pack(side=tk.LEFT, padx=2)
        self.lib_combo.bind("<<ComboboxSelected>>", self.app.on_lib_selected)
        self.lib_combo.bind("<Button-3>", self.app.show_lib_context)

        self.progress_bar = ttk.Progressbar(self.top_frame, mode='indeterminate', length=80)

        self.status_frame = tk.Frame(self.root, bg="#007ACC")
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_bar = tk.Label(self.status_frame, text="Hazır", bg="#007ACC", fg="white", anchor="w", padx=10, pady=2, cursor="hand2")
        self.status_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.status_bar.bind("<Double-1>", self.app.change_python_path)

        self.terminal_btn = tk.Button(self.status_frame, text=">_ Terminal", command=self.app.open_terminal, bg="#005A9E", fg="white", font=("Consolas", 9, "bold"), relief=tk.FLAT, padx=10, pady=0)
        self.terminal_btn.pack(side=tk.RIGHT)

        self.main_pane = tk.PanedWindow(self.root, orient=tk.VERTICAL, sashwidth=1, sashpad=2, sashrelief=tk.FLAT, bd=0, cursor="arrow", sashcursor="sb_v_double_arrow")
        self.main_pane.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        self.editor_frame = tk.Frame(self.main_pane)
        self.bottom_panel_frame = tk.Frame(self.main_pane)
        
        self.main_pane.add(self.editor_frame, minsize=100)
        self.main_pane.add(self.bottom_panel_frame, minsize=115)

        self.tab_mgr = TabManager(parent_widget=self.editor_frame)

        self.info_search_frame = tk.Frame(self.bottom_panel_frame)
        self.info_search_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=(5, 0))

        self.line_count_label = tk.Label(self.info_search_frame, text="Toplam Satır: 0", font=("Consolas", 9))
        self.line_count_label.pack(side=tk.LEFT, padx=(0, 30))
        self.theme_labels.append(self.line_count_label)
        
        lbl_aranacak = tk.Label(self.info_search_frame, text="Aranacak:", font=("Consolas", 9))
        lbl_aranacak.pack(side=tk.LEFT)
        self.theme_labels.append(lbl_aranacak)
        
        self.search_entry = tk.Entry(self.info_search_frame, width=20)
        self.search_entry.pack(side=tk.LEFT, padx=(2, 10))
        self.search_entry.bind("<Return>", lambda e: self._trigger_search(forward=True))
        
        self.search_match_case = tk.BooleanVar(value=False)
        self.chk_match_case = tk.Checkbutton(self.info_search_frame, text="Büyük/Küçük Harf", variable=self.search_match_case, cursor="hand2")
        self.chk_match_case.pack(side=tk.LEFT, padx=2)
        
        self.search_whole_word = tk.BooleanVar(value=False)
        self.chk_whole_word = tk.Checkbutton(self.info_search_frame, text="Tam Eşleşme", variable=self.search_whole_word, cursor="hand2")
        self.chk_whole_word.pack(side=tk.LEFT, padx=2)
        
        self.search_all_tabs = tk.BooleanVar(value=False)
        self.chk_all_tabs = tk.Checkbutton(self.info_search_frame, text="Tüm Sekmeler", variable=self.search_all_tabs, cursor="hand2")
        self.chk_all_tabs.pack(side=tk.LEFT, padx=2)
        
        self.search_checks.extend([self.chk_match_case, self.chk_whole_word, self.chk_all_tabs])
        
        self.btn_search_prev = tk.Button(self.info_search_frame, text="▲", relief=tk.FLAT, padx=5, command=lambda: self._trigger_search(forward=False), cursor="hand2")
        self.btn_search_prev.pack(side=tk.LEFT, padx=(10, 2))
        self.theme_buttons.append(self.btn_search_prev)
        
        self.btn_search_next = tk.Button(self.info_search_frame, text="▼", relief=tk.FLAT, padx=5, command=lambda: self._trigger_search(forward=True), cursor="hand2")
        self.btn_search_next.pack(side=tk.LEFT, padx=2)
        self.theme_buttons.append(self.btn_search_next)
        
        self.input_frame = tk.Frame(self.bottom_panel_frame)
        self.input_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=2)
        
        lbl_in = tk.Label(self.input_frame, text="Giriş (stdin):")
        lbl_in.pack(side=tk.LEFT)
        self.panel_labels.append(lbl_in)
        
        self.input_entry = tk.Entry(self.input_frame, state=tk.DISABLED)
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.input_entry.bind("<Return>", lambda e: (EventBus.publish("process:send_input", self.input_entry.get()), self.input_entry.delete(0, tk.END)))

        self.out_header_frame = tk.Frame(self.bottom_panel_frame)
        self.out_header_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=(0, 0))
        
        lbl_out = tk.Label(self.out_header_frame, text="Çıktı Ekranı", fg="#75715E")
        lbl_out.pack(side=tk.LEFT)
        self.panel_labels.append(lbl_out)
        
        btn_temizle = tk.Button(self.out_header_frame, text="Temizle", command=self.app.clear_output, relief=tk.FLAT, padx=8, pady=0)
        btn_temizle.pack(side=tk.RIGHT)
        self.theme_buttons.append(btn_temizle)

        self.output_screen = tk.Text(self.bottom_panel_frame, height=5, font=("Consolas", 11), state=tk.NORMAL)
        self.output_screen.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=2)

    def apply_theme(self, is_dark):
        bg_color = "#333333" if is_dark else "#E5E5E5"
        panel_bg = "#1E1F1C" if is_dark else "#F0F0F0"
        fg_color = "white" if is_dark else "black"
        text_bg = "#000000" if is_dark else "#FFFFFF"
        text_fg = "#A6E22E" if is_dark else "#007F00"
        btn_bg = "#555555" if is_dark else "#CCCCCC"
        
        self.top_frame.config(bg=bg_color)
        
        self.main_pane.config(bg=btn_bg) 
        self.editor_frame.config(bg=panel_bg)
        self.bottom_panel_frame.config(bg=panel_bg)
        
        self.info_search_frame.config(bg=panel_bg) 
        self.out_header_frame.config(bg=panel_bg)
        self.input_frame.config(bg=panel_bg)
        
        for lbl in self.theme_labels: lbl.config(bg=bg_color, fg=fg_color)
        for lbl in self.panel_labels: lbl.config(bg=panel_bg, fg=fg_color)
        
        for chk in self.search_checks:
            chk.config(bg=panel_bg, fg=fg_color, selectcolor="#222222" if is_dark else "#FFFFFF", activebackground=panel_bg, activeforeground=fg_color)
            
        self.theme_check.config(bg=bg_color, fg=fg_color, selectcolor=panel_bg, activebackground=bg_color, activeforeground=fg_color)
            
        for btn in self.theme_buttons: btn.config(bg=btn_bg, fg=fg_color)
            
        self.args_entry.config(bg=panel_bg, fg=fg_color, insertbackground=fg_color)
        self.search_entry.config(bg="#333333" if is_dark else "#FFFFFF", fg=fg_color, insertbackground=fg_color)
        self.input_entry.config(bg="#333333" if is_dark else "#FFFFFF", disabledbackground="#222222" if is_dark else "#DDDDDD", fg=fg_color, insertbackground=fg_color)
        self.output_screen.config(bg=text_bg, fg=text_fg, insertbackground=fg_color)
        
        style = ttk.Style()
        style.theme_use('clam')
        
        if self.tab_mgr:
            self.tab_mgr.apply_theme(is_dark)