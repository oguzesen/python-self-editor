# editor_tab.py
import tkinter as tk
import re

class EditorTab(tk.Frame):
    def __init__(self, parent, file_path=None, on_change_callback=None, font_size=12, is_dark=True, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.file_path = file_path
        self.is_temp_file = False
        self.on_change_callback = on_change_callback
        self.line_number_fg = "#75715E"
        self.font_size = font_size
        self.highlight_timer = None 
        
        self.text_area = tk.Text(self, undo=True, font=("Consolas", self.font_size), wrap=tk.NONE, bd=0, highlightthickness=0)
        self.line_numbers = tk.Canvas(self, width=40, bg="#1E1F1C", bd=0, highlightthickness=0)
        
        self.scrollbar = tk.Scrollbar(self, command=self.on_scroll)
        self.h_scrollbar = tk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.text_area.xview)
        
        self.text_area.configure(yscrollcommand=self.on_text_scroll, xscrollcommand=self.h_scrollbar.set)
        
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.apply_theme(is_dark=is_dark) 
        self.bind_events()

    def set_font_size(self, new_size):
        self.font_size = new_size
        self.text_area.configure(font=("Consolas", self.font_size))
        self.redraw_line_numbers()
        self.schedule_highlight()

    def on_scroll(self, *args):
        self.text_area.yview(*args)
        self.redraw_line_numbers()
        self.schedule_highlight()

    def on_text_scroll(self, *args):
        self.scrollbar.set(*args)
        self.redraw_line_numbers()
        self.schedule_highlight()

    def redraw_line_numbers(self, event=None):
        self.line_numbers.delete("all")
        i = self.text_area.index("@0,0")
        while True:
            dline = self.text_area.dlineinfo(i)
            if dline is None: break
            y = dline[1]
            linenum = str(i).split(".")[0]
            self.line_numbers.create_text(self.line_numbers.winfo_width() - 5, y, anchor="ne", text=linenum, font=("Consolas", self.font_size), fill=self.line_number_fg)
            i = self.text_area.index(f"{i}+1line")
        
        last_line = int(self.text_area.index("end-1c").split(".")[0])
        digits = max(3, len(str(last_line)))
        
        char_width = int(self.font_size * 0.6)
        new_width = digits * char_width + 10
        if int(self.line_numbers['width']) != new_width:
            self.line_numbers.config(width=new_width)

    def apply_theme(self, is_dark):
        self.text_area.config(
            bg="#272822" if is_dark else "#FFFFFF",
            fg="#F8F8F2" if is_dark else "#000000",
            insertbackground="#F8F8F0" if is_dark else "#000000"
        )
        self.line_numbers.config(bg="#1E1F1C" if is_dark else "#F0F0F0")
        self.line_number_fg = "#75715E" if is_dark else "#888888"
        
        if is_dark:
            self.text_area.tag_configure("Keyword", foreground="#F92672")      
            self.text_area.tag_configure("Builtin", foreground="#66D9EF")      
            self.text_area.tag_configure("String", foreground="#E6DB74")       
            self.text_area.tag_configure("Number", foreground="#AE81FF")       
            self.text_area.tag_configure("Comment", foreground="#75715E")      
            self.text_area.tag_configure("Operator", foreground="#F92672")     
            self.text_area.tag_configure("Variable", foreground="#FD971F")     
            self.text_area.tag_configure("Method", foreground="#A6E22E")       
            self.text_area.tag_configure("DefClass", foreground="#A6E22E")
        else:
            self.text_area.tag_configure("Keyword", foreground="#0000FF")      
            self.text_area.tag_configure("Builtin", foreground="#0070C1")      
            self.text_area.tag_configure("String", foreground="#A31515")       
            self.text_area.tag_configure("Number", foreground="#098658")       
            self.text_area.tag_configure("Comment", foreground="#008000")      
            self.text_area.tag_configure("Operator", foreground="#000000")     
            self.text_area.tag_configure("Variable", foreground="#001080")     
            self.text_area.tag_configure("Method", foreground="#795E26")       
            self.text_area.tag_configure("DefClass", foreground="#267F99")
            
        for tag in ["Keyword", "Builtin", "Method", "Variable", "Number", "Operator", "String", "Comment"]:
            self.text_area.tag_raise(tag)
            
        self.schedule_highlight()
        self.redraw_line_numbers()

    def bind_events(self):
        self.text_area.bind("<KeyRelease>", self.schedule_highlight)
        self.text_area.bind("<Return>", self.auto_indent)
        self.text_area.bind("<Tab>", self.insert_spaces)
        self.text_area.bind("<<Modified>>", self._on_modified)
        self.text_area.bind("<MouseWheel>", self._on_mousewheel)
        self.text_area.bind("<Configure>", lambda e: self.redraw_line_numbers())
        
    def _on_mousewheel(self, event):
        self.after(10, self.redraw_line_numbers)
        self.schedule_highlight()

    def _on_modified(self, event=None):
        if self.text_area.edit_modified():
            if self.on_change_callback:
                self.on_change_callback(self)
            self.text_area.edit_modified(False)
            self.redraw_line_numbers()

    def schedule_highlight(self, event=None):
        if self.highlight_timer:
            self.after_cancel(self.highlight_timer)
        self.highlight_timer = self.after(350, self.highlight_syntax)
    
    def insert_spaces(self, event):
        self.text_area.insert(tk.INSERT, "    ")
        return "break"

    def auto_indent(self, event):
        line = self.text_area.get("insert linestart", "insert")
        indent_match = re.match(r"^(\s*)", line)
        indent = indent_match.group(1) if indent_match else ""
        if line.rstrip().endswith(":"):
            indent += "    "
        self.text_area.insert(tk.INSERT, "\n" + indent)
        self.redraw_line_numbers()
        return "break" 

    def highlight_syntax(self):
        top_visible = self.text_area.index("@0,0")
        bottom_visible = self.text_area.index(f"@0,{self.text_area.winfo_height()}")
        
        start_line = max(1, int(top_visible.split('.')[0]) - 50)
        end_line = int(bottom_visible.split('.')[0]) + 50
        
        start_idx = f"{start_line}.0"
        end_idx = f"{end_line}.end"

        for tag in ["Keyword", "Builtin", "String", "Number", "Comment", "Operator", "Variable", "Method", "DefClass"]:
            self.text_area.tag_remove(tag, start_idx, end_idx)
            
        text = self.text_area.get(start_idx, end_idx)
        rules = [
            ("Comment", r'#.*'),
            ("String", r'(?:"[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\')'),
            ("Keyword", r'\b(def|class|if|elif|else|for|while|break|continue|return|import|from|as|pass|try|except|finally|with|True|False|None|and|or|not|in|is|lambda|global|nonlocal|yield)\b'),
            ("Builtin", r'\b(print|input|len|range|int|float|str|list|dict|set|tuple|open|type|dir|help)\b'),
            ("Method", r'\b([a-zA-Z_]\w*)\s*(?=\()'), 
            ("Variable", r'\b([a-zA-Z_]\w*)\s*(?=\s*=(?!=))'), 
            ("Number", r'\b\d+(?:\.\d+)?\b'),
            ("Operator", r'[\+\-\*\/\%\=\<\>\!\&\|\^]'),
            ("DefClass", r'\b(?:def|class)\s+([a-zA-Z_]\w*)')
        ]
        
        for tag, pattern in rules:
            for match in re.finditer(pattern, text):
                start = match.start(1) if match.lastindex else match.start()
                end = match.end(1) if match.lastindex else match.end()
                self.text_area.tag_add(tag, f"{start_idx} + {start} chars", f"{start_idx} + {end} chars")
        
        self.redraw_line_numbers()

    def get_code(self):
        return self.text_area.get("1.0", tk.END)[:-1]

    def load_code(self, content):
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert(tk.END, content)
        self.schedule_highlight()
        self.text_area.edit_modified(False)
        self.redraw_line_numbers()