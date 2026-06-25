import subprocess
import threading
import queue
import time
import os

class ProcessRunner:
    def __init__(self, write_callback, clear_callback, finish_callback):
        self.process = None
        self.output_queue = queue.Queue()
        self.start_time = 0
        
        self.write_cb = write_callback
        self.clear_cb = clear_callback
        self.finish_cb = finish_callback

    def run(self, cmd, is_pip=False, cwd=None):
        self.clear_cb()
        
        while not self.output_queue.empty():
            self.output_queue.get()
            
        if self.process and self.process.poll() is None:
            self.process.terminate()

        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        self.start_time = time.time() 
        
        try:
            self.process = subprocess.Popen(
                cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors='replace', env=env, bufsize=1,
                cwd=cwd, 
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            threading.Thread(target=self._read_output, args=(self.process, is_pip), daemon=True).start()
        except Exception as e:
            self.write_cb(f"Hata oluştu: {str(e)}\n")

    def _read_output(self, process, is_pip):
        while True:
            char = process.stdout.read(1)
            if not char:
                break
            self.output_queue.put(("OUTPUT", process, char))
            
        process.stdout.close()
        process.wait() 
        elapsed_time = time.time() - self.start_time
        
        if is_pip:
            self.output_queue.put(("PIP_END", process, f"\n--- Pip/Sistem İşlemi Sonlandı ({elapsed_time:.1f} sn) ---\n"))
        else:
            self.output_queue.put(("END", process, f"\n\n--- Program Sonlandı ({elapsed_time:.2f} saniye) ---\n"))

    def send_input(self, user_input):
        if self.process and self.process.poll() is None:
            self.write_cb(user_input + "\n")
            try:
                self.process.stdin.write(user_input + "\n")
                self.process.stdin.flush()
            except Exception as e:
                self.write_cb(f"\nGiriş hatası: {str(e)}\n")

    def check_queue(self):
        buffer = ""
        event_type = None
        
        while not self.output_queue.empty():
            msg_type, process, text = self.output_queue.get()
            if process == self.process:
                buffer += text
                if msg_type in ["PIP_END", "END"]:
                    event_type = msg_type
                    
        if buffer:
            self.write_cb(buffer)
            
        if event_type:
            self.finish_cb(event_type)