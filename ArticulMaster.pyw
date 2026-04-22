import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import os, sys, threading, json, re, requests
from datetime import datetime

# --- ФУНКЦІЯ ДЛЯ ВИЗНАЧЕННЯ ШЛЯХІВ (ВАЖЛИВО ДЛЯ EXE) ---
def resource_path(relative_path):
    """ Отримує шлях до ресурсу, працює для розробки (.py) і для PyInstaller (.exe) """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Додаємо шлях до модулів у систему
sys.path.append(resource_path('.'))

# --- БЛОК СИНХРОНІЗАЦІЇ ДЛЯ .PY ВЕРСІЇ (НЕ EXE) ---
def sync_internal_modules():
    if getattr(sys, 'frozen', False): return 
    
    GITHUB_RAW_BASE = "https://raw.githubusercontent.com/alex-voron/ArticulMaster/main/"
    REQUIRED_FILES = ["config.py", "logic.py", "cloud_manager.py", "ui_components.py"]
    downloaded = False
    for filename in REQUIRED_FILES:
        try:
            r = requests.get(GITHUB_RAW_BASE + filename, timeout=10)
            if r.status_code == 200:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(r.text)
                downloaded = True
        except: pass
    if downloaded:
        os.execv(sys.executable, ['python'] + sys.argv)

sync_internal_modules()

# --- ІМПОРТИ МОДУЛІВ ---
import config
from logic import ArticulLogic
from cloud_manager import CloudManager
from ui_components import UIManager

class ArticulMasterApp:
    def __init__(self, root):
        self.root = root
        self.logic = ArticulLogic()
        self.cloud = CloudManager()
        self.ui = UIManager(self.root) 
        
        self.root.title(f"Articul Master v{config.CURRENT_VERSION}")
        self.root.geometry("420x750")
        self.root.resizable(False, False)
        self.root.configure(bg='#0b0d11')
        
        self.vendor_var = tk.StringVar()
        self.res_var = tk.StringVar(value="---")
        
        self.setup_ui()
        self.init_app()

    def init_app(self):
        # Авто-створення секретів для хмари
        cid, sec = config.get_keys()
        secrets = {"installed": {"client_id": cid, "client_secret": sec, 
                   "auth_uri": "https://accounts.google.com/o/oauth2/auth", "token_uri": "https://oauth2.googleapis.com/token",
                   "redirect_uris": ["http://localhost:8080"]}}
        
        with open(config.SECRETS_FILE, 'w') as f: 
            json.dump(secrets, f)
        
        self.root.after(200, self.force_sync_ui)
        self.root.after(1500, lambda: self.cloud.initialize(
            on_success=lambda: self.show_toast(config.t("toast_cloud_ok") if "toast_cloud_ok" in config.LOCALES["UA"] else "ХМАРА АКТИВНА ✅", "#00ff9d"),
            on_error=lambda: self.show_toast(config.t("toast_cloud_err") if "toast_cloud_err" in config.LOCALES["UA"] else "З'ЄДНАННЯ ВІДСУТНЄ", "#f85149")
        ))
        
        # Перевірка оновлень у фоні
        threading.Thread(target=self.check_for_updates, daemon=True).start()

    def toggle_language(self):
        current = config.get_lang()
        new_lang = "EN" if current == "UA" else "UA"
        config.set_lang(new_lang)
        for widget in self.root.winfo_children():
            widget.destroy()
        self.setup_ui()

    def check_for_updates(self):
        try:
            r = requests.get(config.VERSION_URL, timeout=5)
            if r.status_code == 200:
                online_v = r.text.strip()
                # Перетворюємо рядки "4.2" у числа 4.2 для правильного порівняння
                if float(online_v) > float(config.CURRENT_VERSION):
                    if messagebox.askyesno("Update", f"Доступна нова версія {online_v}. Оновити зараз?"):
                        self.start_upgrade()
        except Exception as e:
            print(f"Update check failed: {e}")

    def start_upgrade(self):
        """Механізм самозаміни EXE через BAT-файл"""
        if not getattr(sys, 'frozen', False):
            messagebox.showinfo("Info", "Оновлення EXE доступне лише у зібраній версії.")
            return

        def run_upgrade():
            try:
                r = requests.get(config.EXE_UPDATE_URL, stream=True, timeout=30)
                temp_exe = os.path.join(os.path.dirname(sys.executable), "ArticulMaster_new.exe")
                with open(temp_exe, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                bat_path = os.path.join(os.path.dirname(sys.executable), "update.bat")
                exe_name = os.path.basename(sys.executable)
                with open(bat_path, 'w') as f:
                    f.write(f'@echo off\ntimeout /t 2 /nobreak > nul\ndel "{exe_name}"\nren "ArticulMaster_new.exe" "{exe_name}"\nstart "" "{exe_name}"\ndel "%~f0"')
                
                os.startfile(bat_path)
                self.root.quit()
                sys.exit()
            except Exception as e:
                messagebox.showerror("Error", f"Помилка оновлення: {e}")

        threading.Thread(target=run_upgrade, daemon=True).start()

    def setup_ui(self):
        # Кнопка мови
        tk.Button(self.root, text=config.t("lang_toggle"), command=self.toggle_language,
                  bg='#0b0d11', fg='#58a6ff', relief="flat", font=("Segoe UI", 8), cursor="hand2").place(x=360, y=10)

        # Header
        tk.Label(self.root, text="A R T I C U L  M A S T E R", font=("Segoe UI", 18, "bold"), bg='#0b0d11', fg='#e6edf3').pack(pady=(25, 0))
        tk.Label(self.root, text=f"V{config.CURRENT_VERSION} PRECISION", font=("Segoe UI", 7, "bold"), bg='#0b0d11', fg='#00ff9d').pack()

        v_frame = tk.Frame(self.root, bg='#0b0d11', pady=15)
        v_frame.pack(fill='x', padx=50)
        tk.Label(v_frame, text=config.t("vendor_label"), bg='#0b0d11', fg='#8b949e', font=("Segoe UI", 7, "bold")).pack(anchor='w')
        
        v_list = [f"[{c}] {n}" for c, n in config.VENDORS.items()]
        self.vendor_cb = ttk.Combobox(v_frame, textvariable=self.vendor_var, values=v_list, state="readonly")
        self.vendor_cb.pack(fill='x', pady=5)
        
        def on_vendor_select(e):
            selected = self.vendor_cb.get()
            code = self.logic.get_vendor_code(selected)
            count = self.logic.load_local_data(code)
            self.update_status_label()
            self.vendor_cb.selection_clear()
            self.root.focus()
            self.price_entry.focus_set()
        self.vendor_cb.bind("<<ComboboxSelected>>", on_vendor_select)

        status_frame = tk.Frame(self.root, bg='#0b0d11')
        status_frame.pack(pady=5)
        self.status_label = tk.Label(status_frame, text=config.t("status_sync").format(0), bg='#0b0d11', fg='#8b949e', font=("Segoe UI", 10, "bold"))
        self.status_label.pack(side="left")
        tk.Button(status_frame, text="👁", command=self.show_database_view, bg='#0b0d11', fg='#58a6ff', relief="flat", font=("Segoe UI", 12), cursor="hand2").pack(side="left", padx=8)

        # Search
        s_frame = tk.Frame(self.root, bg='#0d1117', highlightthickness=1, highlightbackground='#30363d')
        s_frame.pack(fill='x', padx=50, pady=15)
        self.search_entry = tk.Entry(s_frame, font=("Segoe UI", 11), justify='center', bg='#0d1117', fg='#8b949e', borderwidth=0, insertbackground='#00ff9d')
        self.search_entry.pack(pady=(10, 2), padx=20, fill='x')
        self.search_entry.insert(0, config.t("search_placeholder"))
        self.search_entry.bind('<FocusIn>', lambda e: self.search_entry.delete(0, tk.END))
        self.search_entry.bind('<KeyRelease>', lambda e: self.quick_search())
        
        search_status_frame = tk.Frame(s_frame, bg='#0d1117')
        search_status_frame.pack(pady=(0, 8))
        self.search_res_label = tk.Label(search_status_frame, text="READY", bg='#0d1117', fg='#30363d', font=("Segoe UI", 8, "bold"))
        self.search_res_label.pack(side="left")
        self.delete_btn = tk.Button(search_status_frame, text="[ DELETE ]", command=self.on_delete, bg='#0d1117', fg='#f85149', relief="flat", font=("Segoe UI", 8, "bold"), state="disabled")
        self.delete_btn.pack(side="left", padx=5)

        tk.Label(self.root, text=config.t("price_label"), bg='#0b0d11', fg='#58a6ff', font=("Segoe UI", 7, "bold")).pack(pady=(10, 0))
        self.price_entry = tk.Entry(self.root, font=("Segoe UI", 16, "bold"), justify='center', bg='#161b22', fg='#ffffff', relief="flat", insertbackground='#00ff9d', highlightthickness=1, highlightbackground='#30363d')
        self.price_entry.pack(pady=5, padx=90, fill='x')
        self.price_entry.bind('<Return>', lambda e: self.on_generate())
        
        tk.Button(self.root, text=config.t("reset_btn"), command=self.clear_fields, bg='#0b0d11', fg='#f85149', relief="flat", font=("Segoe UI", 9, "bold"), pady=10, cursor="hand2").pack(pady=5)

        res_container = tk.Frame(self.root, bg='#0b0d11')
        res_container.pack(pady=20)
        # Результат (виправлено виділення білим фоном)
        res_container = tk.Frame(self.root, bg='#0b0d11')
        res_container.pack(pady=20)
        
        self.res_display = tk.Entry(
            res_container, 
            textvariable=self.res_var, 
            font=("Segoe UI", 28, "bold"), 
            width=9, 
            justify='center', 
            bg='#0b0d11',            # Колір фону коли поле активне
            fg='#00ff9d',            # Колір тексту
            relief="flat", 
            borderwidth=0, 
            highlightthickness=0, 
            readonlybackground='#0b0d11', # ОСЬ ЦЕЙ РЯДОК прибирає білий фон у режимі readonly
            state='readonly'
        )
        self.res_display.pack()

        self.toast_label = tk.Label(self.root, text="", bg='#0b0d11', font=("Segoe UI", 9, "bold"))
        self.toast_label.pack()

        tk.Button(self.root, text=config.t("cloud_restore"), command=self.on_restore, bg='#21262d', fg='#58a6ff', relief="flat", font=("Segoe UI", 10, "bold"), width=20, pady=12, cursor="hand2").pack(pady=10)
        tk.Button(self.root, text=config.t("import_btn"), command=self.on_import, bg='#0b0d11', fg='#30363d', relief="flat", font=("Segoe UI", 7, "bold")).pack(side="bottom", pady=5)

    def show_database_view(self):
        view_win = tk.Toplevel(self.root)
        view_win.title("Occupied Prices")
        view_win.geometry("280x450")
        view_win.configure(bg='#0d1117')
        prices = self.logic.get_sorted_prices()
        list_box = tk.Listbox(view_win, bg='#161b22', fg='#ffffff', font=("Segoe UI", 11), borderwidth=0)
        list_box.pack(expand=True, fill='both', padx=10, pady=10)
        for p in prices: list_box.insert(tk.END, f"  • {p}")

    def on_generate(self):
        val = self.price_entry.get().strip()
        if not val.isdigit(): return
        code = self.logic.get_vendor_code(self.vendor_cb.get())
        articul, _ = self.logic.generate_articul(val, code)
        self.res_var.set(articul)
        self.logic.save_to_file(code)
        db_path = os.path.join(config.DB_DIR, f"vendor_{code}.txt")
        self.cloud.upload_file(f"vendor_{code}.txt", db_path)
        self.root.clipboard_clear()
        self.root.clipboard_append(articul)
        self.show_toast(config.t("copy_toast"), "#00ff9d")
        self.update_status_label()
        self.play_sound()

    def quick_search(self):
        val = self.search_entry.get().strip()
        if not val or val == config.t("search_placeholder"):
            self.search_res_label.config(text="READY", fg='#30363d')
            self.delete_btn.config(state="disabled")
            return
        if val.isdigit() and int(val) in self.logic.occupied_prices:
            self.search_res_label.config(text=config.t("occupied"), fg='#f85149')
            self.delete_btn.config(state="normal")
        else:
            self.search_res_label.config(text=config.t("available"), fg='#00ff9d')
            self.delete_btn.config(state="disabled")

    def on_delete(self):
        val = self.search_entry.get().strip()
        if not val.isdigit(): return
        code = self.logic.get_vendor_code(self.vendor_cb.get())
        if int(val) in self.logic.occupied_prices:
            if messagebox.askyesno("Confirm", f"Delete {val}?"):
                self.logic.occupied_prices.remove(int(val))
                self.logic.save_to_file(code)
                self.update_status_label()
                self.quick_search()

    def on_restore(self):
        if not self.cloud.drive: return
        code = self.logic.get_vendor_code(self.vendor_cb.get())
        filename = f"vendor_{code}.txt"
        self.cloud.download_file(filename, os.path.join(config.DB_DIR, filename), on_complete=lambda: [
            self.logic.load_local_data(code),
            self.update_status_label(),
            self.show_toast("RESTORED", "#00ff9d")
        ])

    def on_import(self):
        path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if path:
            code = self.logic.get_vendor_code(self.vendor_cb.get())
            added = self.logic.import_txt(path)
            
            if added > 0:
                # 1. Зберігаємо локально в AppData
                self.logic.save_to_file(code)
                
                # 2. Оновлюємо цифру в інтерфейсі
                self.update_status_label()
                
                # 3. ВІДПРАВЛЯЄМО В ХМАРУ (щоб дані не зникли)
                db_filename = f"vendor_{code}.txt"
                local_path = os.path.join(config.DB_DIR, db_filename)
                self.cloud.upload_file(db_filename, local_path)
                
                # 4. Показуємо успіх (з використанням перекладу)
                msg = f"{config.t('copy_toast')} (+{added})" if added > 0 else "DONE"
                self.show_toast(f"ADDED {added} ITEMS", "#00ff9d")
            else:
                # Якщо файл вибрали, але там старі ціни, які вже є в базі
                self.show_toast("NO NEW DATA FOUND", "#f85149")

    def update_status_label(self):
        # Використовуємо формат з конфігу, щоб підтримувати мови
        self.status_label.config(text=config.t("status_sync").format(len(self.logic.occupied_prices)))
    def force_sync_ui(self):
        try:
            self.vendor_cb.current(0)
            code = self.logic.get_vendor_code(self.vendor_cb.get())
            self.logic.load_local_data(code)
            self.update_status_label()
        except: pass

    def show_toast(self, text, color):
        self.toast_label.config(text=text, fg=color)
        threading.Timer(2.5, lambda: self.toast_label.config(text="")).start()

    def clear_fields(self):
        self.price_entry.delete(0, tk.END)
        self.res_var.set("---")

    def play_sound(self):
        try:
            import winsound
            winsound.MessageBeep()
        except: pass

if __name__ == "__main__":
    root = tk.Tk()
    app = ArticulMasterApp(root)
    root.mainloop()