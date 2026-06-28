import tkinter as tk
from tkinter import messagebox
import re

class SearchHandler:
    def __init__(self, app):
        self.app = app

    def _tr_lower(self, s):
        return s.replace('I', 'ı').replace('İ', 'i').lower()

    def _get_matches_for_tab(self, tab, target, match_case, whole_word):
        content = tab.text_area.get("1.0", tk.END)
        
        if not match_case:
            content_search = self._tr_lower(content)
            target_search = self._tr_lower(target)
        else:
            content_search = content
            target_search = target
            
        if whole_word:
            pattern = r'(?<!\w)' + re.escape(target_search) + r'(?!\w)'
        else:
            pattern = re.escape(target_search)
            
        return list(re.finditer(pattern, content_search))

    def _get_cursor_flat_index(self, tab):
        cursor_idx = tab.text_area.index(tk.INSERT)
        return len(tab.text_area.get("1.0", cursor_idx))

    def _highlight_and_scroll(self, tab, match):
        self.app.ui.tab_mgr.select_tab(tab)
        
        for t in self.app.ui.tab_mgr.tabs.keys():
            t.text_area.tag_remove("search_highlight", "1.0", tk.END)
            
        start_idx = f"1.0 + {match.start()} chars"
        end_idx = f"1.0 + {match.end()} chars"
        
        tab.text_area.tag_add("search_highlight", start_idx, end_idx)
        
        # --- DÜZELTME: Okunabilirliği yüksek "Seçim Mavisi" ve "Beyaz Metin" eklendi ---
        tab.text_area.tag_config("search_highlight", background="#0078D7", foreground="#FFFFFF") 
        
        # tag_raise metodu sözdizimi(syntax) renklerini ezerek yazının beyaz kalmasını garanti eder
        tab.text_area.tag_raise("search_highlight")
        
        tab.text_area.mark_set("insert", end_idx)
        tab.text_area.see(start_idx)

    def find_next(self, event=None):
        self._find(forward=True)

    def find_prev(self, event=None):
        self._find(forward=False)

    def _find(self, forward=True):
        target = self.app.ui.search_entry.get()
        if not target:
            self._clear_all_highlights()
            return

        match_case = self.app.ui.search_match_case.get()
        whole_word = self.app.ui.search_whole_word.get()
        all_tabs = self.app.ui.search_all_tabs.get()

        tabs_to_search = []
        current_tab = self.app.ui.tab_mgr.get_current_tab()
        
        if not current_tab: return
        
        if all_tabs:
            tabs_to_search = list(self.app.ui.tab_mgr.tabs.keys())
        else:
            tabs_to_search = [current_tab]

        if not tabs_to_search: return

        start_tab_idx = tabs_to_search.index(current_tab) if current_tab in tabs_to_search else 0
        num_tabs = len(tabs_to_search)
        
        for i in range(num_tabs):
            offset = i if forward else -i
            tab_idx = (start_tab_idx + offset) % num_tabs
            tab = tabs_to_search[tab_idx]
            
            matches = self._get_matches_for_tab(tab, target, match_case, whole_word)
            if not matches:
                continue

            if tab == current_tab and i == 0:
                cursor_flat = self._get_cursor_flat_index(tab)
                search_ranges = tab.text_area.tag_ranges("search_highlight")
                
                if search_ranges:
                    hl_start_flat = len(tab.text_area.get("1.0", search_ranges[0]))
                    hl_end_flat = len(tab.text_area.get("1.0", search_ranges[1]))
                    
                    if forward:
                        valid_matches = [m for m in matches if m.start() >= hl_end_flat]
                    else:
                        valid_matches = [m for m in matches if m.end() <= hl_start_flat]
                else:
                    if forward:
                        valid_matches = [m for m in matches if m.start() >= cursor_flat]
                    else:
                        valid_matches = [m for m in matches if m.end() <= cursor_flat]

                if valid_matches:
                    self._highlight_and_scroll(tab, valid_matches[-1] if not forward else valid_matches[0])
                    return
            else:
                self._highlight_and_scroll(tab, matches[-1] if not forward else matches[0])
                return
        
        for i in range(num_tabs):
            offset = i if forward else -i
            tab_idx = (start_tab_idx + offset) % num_tabs
            tab = tabs_to_search[tab_idx]
            matches = self._get_matches_for_tab(tab, target, match_case, whole_word)
            if matches:
                self._highlight_and_scroll(tab, matches[-1] if not forward else matches[0])
                return
        
        messagebox.showinfo("Arama Sonucu", f"'{target}' bulunamadı.", parent=self.app.root)
        self._clear_all_highlights()

    def _clear_all_highlights(self):
        for t in self.app.ui.tab_mgr.tabs.keys():
            t.text_area.tag_remove("search_highlight", "1.0", tk.END)