# compiler_builder.py
import os
import sys
import threading
import subprocess
import shutil
from pathlib import Path
from compiler_template import SETUP_SCRIPT_TEMPLATE
from event_bus import EventBus

def resource_path(relative_path):
    """ Exe içinde veya normal çalışma ortamında dosya yolunu bulur """
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)

class CompilerBuilder:
    def __init__(self, python_path, compiler_ui):
        self.python_path = python_path
        self.ui = compiler_ui

    def start_build(self, target_file, final_icon_path, setup_icon_path, custom_app_name, no_console, added_files, scanned_imports, create_setup, setup_desc_text):
        cmd = [self.python_path, "-m", "PyInstaller", "--onefile", "--noconfirm"]
        if final_icon_path: cmd.append(f"--icon={final_icon_path}")
        if no_console: cmd.append("--windowed")
        for f in added_files: cmd.append(f"--add-data={f}{os.pathsep}.")
            
        work_dir = os.path.dirname(target_file)
        for imp in scanned_imports:
            cmd.append(f"--hidden-import={imp}")
        cmd.append(target_file)
        
        EventBus.publish("ui:clear_output")
        EventBus.publish("ui:write_output", "--- Derleme İşlemi Başlıyor ---\n")
        
        self.ui.build_btn.config(text="Derleniyor... Lütfen Bekleyin", command=lambda: None)
        self.ui.update()
        
        threading.Thread(
            target=self._build_worker, 
            args=(cmd, work_dir, target_file, final_icon_path, setup_icon_path, custom_app_name, create_setup, setup_desc_text), 
            daemon=True
        ).start()

    def _build_worker(self, cmd, work_dir, target_file, final_icon_path, setup_icon_path, custom_app_name, create_setup, setup_desc_text):
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"

        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors='replace', env=env, bufsize=1,
            cwd=work_dir, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )

        for line in iter(process.stdout.readline, ''):
            self.ui.after(0, EventBus.publish, "ui:write_output", line)

        process.stdout.close()
        process.wait()

        self.ui.after(0, EventBus.publish, "ui:write_output", "\n--- Derleme Tamamlandı, Klasör Düzenleniyor ---\n")

        try:
            target_path = Path(target_file)
            stem = target_path.stem
            parent_dir = target_path.parent
            
            app_name = custom_app_name if custom_app_name else stem.capitalize()
            
            spec_file = parent_dir / f"{stem}.spec"
            build_dir = parent_dir / "build"
            dist_dir = parent_dir / "dist"
            dist_exe = dist_dir / f"{stem}.exe"
            
            final_exe = parent_dir / f"{app_name}.exe"

            if dist_exe.exists():
                if final_exe.exists(): final_exe.unlink()
                shutil.move(str(dist_exe), str(final_exe))

            if build_dir.exists(): shutil.rmtree(build_dir, ignore_errors=True)
            if dist_dir.exists(): shutil.rmtree(dist_dir, ignore_errors=True)
            if spec_file.exists(): spec_file.unlink()
            
            if create_setup and final_exe.exists():
                self.ui.after(0, EventBus.publish, "ui:write_output", "\n--- Setup Sihirbazı Üretiliyor... ---\n")
                
                setup_script_name = f"setup_builder_{stem}.py"
                setup_script_path = parent_dir / setup_script_name
                icon_name = os.path.basename(setup_icon_path) if setup_icon_path else ""
                
                desc_text = setup_desc_text.replace("'''", "''' + \"'''\" + '''") 

                script_content = SETUP_SCRIPT_TEMPLATE.replace("__APP_NAME__", app_name)
                script_content = script_content.replace("__EXE_FILENAME__", final_exe.name)
                script_content = script_content.replace("__ICON_FILENAME__", icon_name)
                script_content = script_content.replace("__DESCRIPTION__", desc_text)
                
                with open(setup_script_path, "w", encoding="utf-8") as f:
                    f.write(script_content)
                
                standard_icon_path = resource_path("ikon2.ico")
                
                setup_cmd = [
                    self.python_path, "-m", "PyInstaller", "--onefile", "--windowed", "--noconfirm",
                    f"--add-data={final_exe}{os.pathsep}.",
                    f"--name=Setup_{app_name}"
                ]
                
                if setup_icon_path: setup_cmd.append(f"--add-data={setup_icon_path}{os.pathsep}.")
                    
                if os.path.exists(standard_icon_path):
                    setup_cmd.append(f"--icon={standard_icon_path}")
                    setup_cmd.append(f"--add-data={standard_icon_path}{os.pathsep}.")
                elif final_icon_path:
                    setup_cmd.append(f"--icon={final_icon_path}")
                    
                setup_cmd.append(str(setup_script_path))
                
                setup_process = subprocess.Popen(
                    setup_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, encoding="utf-8", errors='replace', env=env, bufsize=1,
                    cwd=work_dir, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                
                for line in iter(setup_process.stdout.readline, ''):
                    self.ui.after(0, EventBus.publish, "ui:write_output", line)
                    
                setup_process.wait()
                
                setup_spec = parent_dir / f"Setup_{app_name}.spec"
                setup_dist_exe = dist_dir / f"Setup_{app_name}.exe"
                final_setup_exe = parent_dir / f"Setup_{app_name}.exe"
                
                if setup_dist_exe.exists():
                    if final_setup_exe.exists(): final_setup_exe.unlink()
                    shutil.move(str(setup_dist_exe), str(final_setup_exe))
                
                if build_dir.exists(): shutil.rmtree(build_dir, ignore_errors=True)
                if dist_dir.exists(): shutil.rmtree(dist_dir, ignore_errors=True)
                if setup_spec.exists(): setup_spec.unlink()
                if setup_script_path.exists(): setup_script_path.unlink()
                if setup_icon_path and os.path.exists(setup_icon_path): os.remove(setup_icon_path)
                
                self.ui.after(0, EventBus.publish, "ui:write_output", f"\n--- SETUP ÜRETİMİ BAŞARILI ---\nSetup Dosyası: {final_setup_exe}\n")
                if os.name == 'nt' and final_setup_exe.exists():
                    subprocess.Popen(f'explorer /select,"{final_setup_exe}"')
            else:
                self.ui.after(0, EventBus.publish, "ui:write_output", f"\n--- İŞLEM BAŞARILI ---\nExe Dosyası Konumu: {final_exe}\n")
                if os.name == 'nt' and final_exe.exists():
                    subprocess.Popen(f'explorer /select,"{final_exe}"')

        except Exception as e:
            self.ui.after(0, EventBus.publish, "ui:write_output", f"\nİşlem sırasında hata oluştu: {e}\n")

        self.ui.after(0, self.ui.destroy)