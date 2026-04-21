import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import os, sys, threading, json, re, requests
from datetime import datetime
CURRENT_VERSION = "3.4.4"
# --- БЛОК РОЗУМНОГО ЗАВАНТАЖЕННЯ МОДУЛІВ ---
REQUIRED_FILES = ["config.py", "logic.py", "cloud_manager.py", "ui_components.py"]
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/alex-voron/ArticulMaster/main/"



def sync_internal_modules():
    """Перевіряє наявність модулів і завантажує їх, якщо вони відсутні"""
    downloaded_any = False
    for filename in REQUIRED_FILES:
        if not os.path.exists(filename):
            print(f"Downloading missing module: {filename}...")
            try:
                url = GITHUB_RAW_BASE + filename
                r = requests.get(url, timeout=10)
                if r.status_code == 200:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(r.text)
                    downloaded_any = True
                else:
                    print(f"Failed to download {filename}: Status {r.status_code}")
            except Exception as e:
                print(f"Error syncing {filename}: {e}")
    
    if downloaded_any:
        print("Modules synced. Restarting application...")
        os.execv(sys.executable, ['python'] + sys.argv)

# Запускаємо перевірку перед основними імпортами
sync_internal_modules()

# Тепер імпортуємо завантажені модулі
try:
    import config
    from logic import ArticulLogic
    from cloud_manager import CloudManager
    from ui_components import UIManager
except ImportError as e:
    # Якщо навіть після спроби завантаження щось не так (наприклад, немає інтернету)
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Critical Error", f"Не вдалося завантажити модулі: {e}\nПеревірте інтернет!")
    sys.exit()

class ArticulMasterApp:
    def __init__(self, root):
        self.root = root
        self.logic = ArticulLogic()
        self.cloud = CloudManager()
        self.ui = UIManager(self.root) 
        
        self.root.title(f"Articul Master v{config.CURRENT_VERSION}")
        self.root.geometry("420x720")
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
        with open(config.SECRETS_FILE, 'w') as f: json.dump(secrets, f)
        
        self.root.after(200, self.force_sync_ui)
        self.root.after(1500, lambda: self.cloud.initialize(
            on_success=lambda: self.show_toast("ХМАРА АКТИВНА ✅", "#00ff9d"),
            on_error=lambda: self.show_toast("З'ЄДНАННЯ ВІДСУТНЄ", "#f85149")
        ))
        
        # Перевірка оновлень у фоні
        threading.Thread(target=self.check_for_updates, daemon=True).start()

    def check_for_updates(self):
        try:
            r = requests.get(GITHUB_RAW_BASE + "version.txt", timeout=5)
            if r.status_code == 200:
                online_v = r.text.strip()
                if online_v != config.CURRENT_VERSION:
                    print(f"New version available: {online_v}")
        except: pass

    def setup_ui(self):
        # Логотип вимкнено за запитом, але метод готовий у ui_components
        # self.ui.add_background_logo(self.root) 

        # Header
        tk.Label(self.root, text="A R T I C U L  M A S T E R", font=("Segoe UI", 18, "bold"), bg='#0b0d11', fg='#e6edf3').pack(pady=(25, 0))
        tk.Label(self.root, text=f"V{config.CURRENT_VERSION} PRECISION", font=("Segoe UI", 7, "bold"), bg='#0b0d11', fg='#00ff9d').pack()

        # Вибір вендора
        v_frame = tk.Frame(self.root, bg='#0b0d11', pady=15)
        v_frame.pack(fill='x', padx=50)
        v_list = [f"[{c}] {n}" for c, n in config.VENDORS.items()]
        self.vendor_cb = ttk.Combobox(v_frame, textvariable=self.vendor_var, values=v_list, state="readonly", style="TCombobox", height=10)
        self.vendor_cb.pack(fill='x', pady=5)
        
        def on_vendor_select(e):
            selected = self.vendor_cb.get()
            code = self.logic.get_vendor_code(selected)
            count = self.logic.load_local_data(code)
            self.status_label.config(text=f"LOCAL SYNCED: {count} ITEMS")
            self.vendor_cb.selection_clear()
            self.root.focus()
            self.price_entry.focus_set()
        self.vendor_cb.bind("<<ComboboxSelected>>", on_vendor_select)

        # Блок статусу з Оком
        status_frame = tk.Frame(self.root, bg='#0b0d11')
        status_frame.pack(pady=5)
        self.status_label = tk.Label(status_frame, text="LOCAL SYNCED: 0 ITEMS", bg='#0b0d11', fg='#8b949e', font=("Segoe UI", 10, "bold"))
        self.status_label.pack(side="left")
        tk.Button(status_frame, text="👁", command=self.show_database_view, bg='#0b0d11', fg='#58a6ff', activebackground='#0b0d11', relief="flat", font=("Segoe UI", 12), cursor="hand2").pack(side="left", padx=8)

        # Пошук
        s_frame = tk.Frame(self.root, bg='#0d1117', highlightthickness=1, highlightbackground='#30363d')
        s_frame.pack(fill='x', padx=50, pady=15)
        self.search_entry = tk.Entry(s_frame, font=("Segoe UI", 11), justify='center', bg='#0d1117', fg='#8b949e', borderwidth=0, insertbackground='#00ff9d')
        self.search_entry.pack(pady=(10, 2), padx=20, fill='x')
        self.search_entry.insert(0, "Перевірка ціни...")
        self.search_entry.bind('<FocusIn>', lambda e: self.search_entry.delete(0, tk.END))
        self.search_entry.bind('<KeyRelease>', lambda e: self.quick_search())
        
        search_status_frame = tk.Frame(s_frame, bg='#0d1117')
        search_status_frame.pack(pady=(0, 8))
        self.search_res_label = tk.Label(search_status_frame, text="READY", bg='#0d1117', fg='#30363d', font=("Segoe UI", 8, "bold"))
        self.search_res_label.pack(side="left")
        self.delete_btn = tk.Button(search_status_frame, text="[ DELETE ]", command=self.on_delete, bg='#0d1117', fg='#f85149', relief="flat", font=("Segoe UI", 8, "bold"), state="disabled", cursor="hand2")
        self.delete_btn.pack(side="left", padx=5)

        # Ввід
        tk.Label(self.root, text="ВАРТІСТЬ ОДИНИЦІ", bg='#0b0d11', fg='#58a6ff', font=("Segoe UI", 7, "bold")).pack(pady=(10, 0))
        self.price_entry = tk.Entry(self.root, font=("Segoe UI", 16, "bold"), justify='center', bg='#161b22', fg='#ffffff', relief="flat", insertbackground='#00ff9d', highlightthickness=1, highlightbackground='#30363d')
        self.price_entry.pack(pady=5, padx=90, fill='x')
        self.price_entry.bind('<Return>', lambda e: self.on_generate())
        
        tk.Button(self.root, text="[ RESET FIELDS ]", command=self.clear_fields, bg='#0b0d11', fg='#f85149', activebackground='#1c2128', activeforeground='#ff6e6e', relief="flat", font=("Segoe UI", 9, "bold"), pady=10, cursor="hand2").pack(pady=5)

        # Результат
        res_container = tk.Frame(self.root, bg='#0b0d11')
        res_container.pack(pady=20)
        self.res_display = tk.Entry(res_container, textvariable=self.res_var, font=("Segoe UI", 28, "bold"), width=9, justify='center', bg='#0b0d11', fg='#00ff9d', selectbackground='#005a9e', relief="flat", borderwidth=0, highlightthickness=0, readonlybackground='#0b0d11', state='readonly')
        self.res_display.pack()

        self.toast_label = tk.Label(self.root, text="", bg='#0b0d11', font=("Segoe UI", 9, "bold"))
        self.toast_label.pack()

        tk.Button(self.root, text="CLOUD RESTORE", command=self.on_restore, bg='#21262d', fg='#58a6ff', relief="flat", font=("Segoe UI", 10, "bold"), width=20, pady=12, cursor="hand2").pack(pady=10)
        
        tk.Button(self.root, text="IMPORT LOCAL TXT", command=self.on_import, bg='#0b0d11', fg='#30363d', relief="flat", font=("Segoe UI", 7, "bold")).pack(side="bottom", pady=5)

    def show_database_view(self):
        view_win = tk.Toplevel(self.root)
        view_win.title("Occupied Prices")
        view_win.geometry("280x450")
        view_win.configure(bg='#0d1117')
        view_win.transient(self.root)
        
        selected = self.vendor_cb.get()
        tk.Label(view_win, text=f"VENDOR: {selected}", bg='#0d1117', fg='#58a6ff', font=("Segoe UI", 9, "bold")).pack(pady=(15, 0))
        tk.Label(view_win, text="OCCUPIED LIST", bg='#0d1117', fg='#00ff9d', font=("Segoe UI", 11, "bold")).pack(pady=(0, 10))

        text_frame = tk.Frame(view_win, bg='#161b22', highlightthickness=1, highlightbackground='#30363d')
        text_frame.pack(expand=True, fill='both', padx=15, pady=10)
        
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")

        list_box = tk.Listbox(text_frame, bg='#161b22', fg='#ffffff', font=("Segoe UI", 11), borderwidth=0, highlightthickness=0, yscrollcommand=scrollbar.set)
        list_box.pack(side="left", expand=True, fill='both', padx=5)
        scrollbar.config(command=list_box.yview)

        prices = self.logic.get_sorted_prices()
        for p in prices: list_box.insert(tk.END, f"  • {p}")
        if not prices: list_box.insert(tk.END, "  No data found")

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
        self.show_toast("СКОПІЙОВАНО!", "#00ff9d")
        self.update_status_label()
        self.play_sound()

    def quick_search(self):
        val = self.search_entry.get().strip()
        if not val or val == "Перевірка ціни...":
            self.search_res_label.config(text="READY", fg='#30363d')
            self.delete_btn.config(state="disabled")
            return
        if val.isdigit() and int(val) in self.logic.occupied_prices:
            self.search_res_label.config(text="● OCCUPIED", fg='#f85149')
            self.delete_btn.config(state="normal")
        else:
            self.search_res_label.config(text="● AVAILABLE", fg='#00ff9d')
            self.delete_btn.config(state="disabled")

    def on_delete(self):
        val = self.search_entry.get().strip()
        if not val.isdigit(): return
        target = int(val)
        code = self.logic.get_vendor_code(self.vendor_cb.get())
        if target in self.logic.occupied_prices:
            if messagebox.askyesno("Confirm", f"Видалити ціну {target}?"):
                self.logic.occupied_prices.remove(target)
                self.logic.save_to_file(code)
                self.cloud.upload_file(f"vendor_{code}.txt", os.path.join(config.DB_DIR, f"vendor_{code}.txt"))
                self.quick_search()
                self.update_status_label()
                self.show_toast("ВИДАЛЕНО", "#f85149")

    def on_restore(self):
        if not self.cloud.drive: return
        code = self.logic.get_vendor_code(self.vendor_cb.get())
        filename = f"vendor_{code}.txt"
        if messagebox.askyesno("Cloud Restore", f"Завантажити базу вендора {code} з хмари?"):
            self.cloud.download_file(filename, os.path.join(config.DB_DIR, filename), on_complete=lambda: [
                self.logic.load_local_data(code),
                self.update_status_label(),
                self.show_toast("ДАНІ ВІДНОВЛЕНО", "#00ff9d")
            ])

    def on_import(self):
        path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if path:
            code = self.logic.get_vendor_code(self.vendor_cb.get())
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    m = re.search(r'^(\d+)', line.strip())
                    if m: self.logic.occupied_prices.add(int(m.group(1)))
            self.logic.save_to_file(code)
            self.update_status_label()
            self.show_toast("ІМПОРТ ЗАВЕРШЕНО")

    def update_status_label(self):
        self.status_label.config(text=f"LOCAL SYNCED: {len(self.logic.occupied_prices)} ITEMS")

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
        self.price_entry.focus()

    def play_sound(self):
        try:
            import winsound
            winsound.MessageBeep()
        except: pass

if __name__ == "__main__":
    root = tk.Tk()
    app = ArticulMasterApp(root)
    root.mainloop()