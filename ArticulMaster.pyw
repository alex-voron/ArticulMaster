import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import os, re, threading, shutil, sys, requests
from datetime import datetime

# Поточна версія програми
CURRENT_VERSION = "1.3"
VERSION_URL = "https://raw.githubusercontent.com/alex-voron/ArticulMaster/refs/heads/main/version.txt"
UPDATE_URL = "https://raw.githubusercontent.com/alex-voron/ArticulMaster/refs/heads/main/ArticulMaster.pyw"

def hide_console():
    if sys.platform == "win32":
        import ctypes
        hWnd = ctypes.WinDLL('kernel32').GetConsoleWindow()
        if hWnd: ctypes.WinDLL('user32').ShowWindow(hWnd, 0)

try:
    import winsound
    def play_beep(): winsound.MessageBeep()
except ImportError:
    def play_beep(): pass

class ArticulMaster:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Articul Master v{CURRENT_VERSION}")
        self.root.geometry("420x760")
        self.root.resizable(False, False)
        self.root.configure(bg='#0b0d11') 

        appdata_path = os.getenv('APPDATA')
        self.work_dir = os.path.join(appdata_path, "ArticulMasterPro")
        self.db_dir = os.path.join(self.work_dir, "database")
        self.backup_dir = os.path.join(self.work_dir, "backups")
        
        for d in [self.work_dir, self.db_dir, self.backup_dir]:
            if not os.path.exists(d): os.makedirs(d)

        self.vendors = {
            "207": "Pc.Lviv", "212": "eLaptop", "33": "PXL", "37": "Fortserg1",
            "241": "Gadgetusa", "11": "It-Technolodgy", "213": "IT-Lviv",
            "233": "LPStore", "228": "Ruslan111", "224": "SvChoice"
        }
        
        self.occupied_prices = set()
        self.setup_ui()
        self.create_backup()
        self.load_vendor_data()
        
        # Перевірка оновлень при старті
        threading.Thread(target=self.check_for_updates, daemon=True).start()

    def check_for_updates(self):
        try:
            response = requests.get(VERSION_URL, timeout=5)
            if response.status_code == 200:
                remote_version_text = response.text.strip()
                # Перетворюємо обидві версії на числа для правильного порівняння
                remote_v = float(remote_version_text)
                current_v = float(CURRENT_VERSION)
                
                # Оновлюємо, тільки якщо версія в мережі БІЛЬША за поточну
                if remote_v > current_v:
                    if messagebox.askyesno("Оновлення", f"Доступна нова версія {remote_version_text}. Оновити зараз?"):
                        self.perform_update()
                else:
                    # Якщо версії рівні або на гіті стара версія - нічого не робимо
                    pass
        except Exception as e:
            print(f"Помилка перевірки оновлень: {e}")

    def perform_update(self):
        try:
            response = requests.get(UPDATE_URL, timeout=10)
            if response.status_code == 200:
                script_path = os.path.abspath(sys.argv[0])
                with open(script_path, 'wb') as f:
                    f.write(response.content)
                messagebox.showinfo("Успіх", "Програму оновлено. Перезапустіть її.")
                self.root.destroy()
        except Exception as e:
            messagebox.showerror("Помилка оновлення", str(e))

    def setup_ui(self):
        style = ttk.Style()
        style.theme_use('clam')
        self.root.option_add("*TCombobox*Listbox.font", ("Segoe UI", 11))
        
        style.configure("TCombobox", fieldbackground="#161b22", background="#0b0d11", foreground="#e6edf3",
                        darkcolor="#161b22", lightcolor="#161b22", selectbackground="#161b22", 
                        selectforeground="#00ff9d", font=("Segoe UI", 12, "bold"), borderwidth=0)
        style.map("TCombobox", fieldbackground=[("readonly", "#161b22")], foreground=[("readonly", "#e6edf3")])
        
        tk.Label(self.root, text="A R T I C U L  M A S T E R", font=("Segoe UI", 18, "bold"), bg='#0b0d11', fg='#e6edf3').pack(pady=(25, 0))
        tk.Label(self.root, text="PREMIUM FINANCIAL TOOL", font=("Segoe UI", 7, "bold"), bg='#0b0d11', fg='#00ff9d').pack()

        v_frame = tk.Frame(self.root, bg='#0b0d11', pady=15)
        v_frame.pack(fill='x', padx=50)
        tk.Label(v_frame, text="ПАРТНЕР ТА ПОСТАЧАЛЬНИК", bg='#0b0d11', fg='#8b949e', font=("Segoe UI", 7, "bold")).pack(anchor='w', padx=2)
        
        self.vendor_var = tk.StringVar()
        v_list = [f"[{c}] {n}" for c, n in self.vendors.items()]
        self.vendor_cb = ttk.Combobox(v_frame, textvariable=self.vendor_var, values=v_list, state="readonly", style="TCombobox")
        self.vendor_cb.pack(fill='x', pady=5)
        self.vendor_cb.current(0)
        self.vendor_cb.bind("<<ComboboxSelected>>", lambda e: self.load_vendor_data())
        
        self.status_label = tk.Label(self.root, text="SYNCED: 0 ITEMS", bg='#0b0d11', fg='#8b949e', font=("Segoe UI", 10, "bold"))
        self.status_label.pack(pady=5)

        s_frame = tk.Frame(self.root, bg='#0d1117', highlightthickness=1, highlightbackground='#30363d')
        s_frame.pack(fill='x', padx=50, pady=15)
        self.search_entry = tk.Entry(s_frame, font=("Segoe UI", 11), justify='center', bg='#0d1117', fg='#8b949e', borderwidth=0, insertbackground='#00ff9d')
        self.search_entry.pack(pady=(10, 2), padx=20, fill='x')
        self.search_entry.insert(0, "Перевірка ціни...")
        self.search_entry.bind('<FocusIn>', lambda e: self.search_entry.delete(0, tk.END))
        self.search_entry.bind('<KeyRelease>', lambda e: self.quick_search())
        self.search_res_label = tk.Label(s_frame, text="READY", bg='#0d1117', fg='#30363d', font=("Segoe UI", 8, "bold"))
        self.search_res_label.pack(pady=(0, 8))

        tk.Label(self.root, text="ВАРТІСТЬ ОДИНИЦІ", bg='#0b0d11', fg='#58a6ff', font=("Segoe UI", 7, "bold")).pack(pady=(10, 0))
        self.price_entry = tk.Entry(self.root, font=("Segoe UI", 16, "bold"), justify='center', bg='#161b22', 
                                    fg='#ffffff', relief="flat", insertbackground='#00ff9d', highlightthickness=1, highlightbackground='#30363d')
        self.price_entry.pack(pady=5, padx=90, fill='x')
        self.price_entry.bind('<Return>', lambda e: self.generate())
        
        tk.Button(self.root, text="RESET", command=self.clear_fields, bg='#0b0d11', fg='#f85149', 
                  activebackground='#0b0d11', activeforeground='#da3633',
                  relief="flat", font=("Segoe UI", 7, "bold"), cursor="hand2").pack()

        self.res_var = tk.StringVar(value="---")
        self.res_display = tk.Entry(self.root, textvariable=self.res_var, font=("Segoe UI", 28, "bold"), 
                                    justify='center', bg='#0b0d11', fg='#00ff9d', relief="flat", 
                                    readonlybackground='#0b0d11', state='readonly')
        self.res_display.pack(pady=10)

        self.toast_label = tk.Label(self.root, text="", bg='#0b0d11', font=("Segoe UI", 9, "bold"))
        self.toast_label.pack()

        btn_frame = tk.Frame(self.root, bg='#0b0d11')
        btn_frame.pack(pady=10)
        btn_opt = {"relief": "flat", "font": ("Segoe UI", 10, "bold"), "width": 14, "pady": 12, "cursor": "hand2"}

        self.reserve_btn = tk.Button(btn_frame, text="RESERVE", command=self.reserve_articul, bg='#238636', fg='#ffffff', activebackground='#2ea043', **btn_opt)
        self.reserve_btn.pack(side="left", padx=10)

        self.occupied_btn = tk.Button(btn_frame, text="BUSY", command=self.mark_as_occupied, bg='#da3633', fg='#ffffff', activebackground='#f85149', **btn_opt)
        self.occupied_btn.pack(side="left", padx=10)

        tk.Button(self.root, text="DATA IMPORT", command=self.import_txt, bg='#21262d', fg='#8b949e', relief="flat", font=("Segoe UI", 8, "bold"), pady=10).pack(pady=20, padx=90, fill='x')

    def get_vendor_code(self):
        match = re.search(r'\[(\d+)\]', self.vendor_var.get())
        return match.group(1) if match else "000"

    def load_vendor_data(self):
        try:
            code = self.get_vendor_code()
            db_path = os.path.join(self.db_dir, f"vendor_{code}.txt")
            self.occupied_prices = set()
            if os.path.exists(db_path):
                with open(db_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        v = line.strip()
                        if v.isdigit(): self.occupied_prices.add(int(v))
            self.status_label.config(text=f"SYNCED: {len(self.occupied_prices)} ITEMS", fg='#e6edf3')
            self.res_var.set("---")
            self.quick_search()
        except: pass

    def generate(self):
        val = self.price_entry.get().strip()
        if not val.isdigit(): return
        curr = int(val)
        start = curr
        while curr in self.occupied_prices: curr -= 1
        
        code = self.get_vendor_code()
        final_articul = f"{curr}_{code}"
        self.res_var.set(final_articul)
        self.res_display.config(fg='#ffac00' if curr < start else '#00ff9d')
        
        # Автоматичне збереження знайденого артикула
        self.occupied_prices.add(curr)
        self.save_db()
        
        self.root.clipboard_clear()
        self.root.clipboard_append(final_articul)
        self.show_toast("ЗБЕРЕЖЕНО ТА СКОПІЙОВАНО!", '#00ff9d')
        play_beep()

    def reserve_articul(self):
        res = self.res_var.get()
        if res == "---": return
        try:
            price = int(res.split('_')[0])
            self.occupied_prices.add(price)
            self.save_db()
            self.show_toast("ASSET RESERVED", '#00ff9d')
            play_beep()
        except: pass

    def mark_as_occupied(self):
        res = self.res_var.get()
        if res == "---": return
        try:
            price = int(res.split('_')[0])
            self.occupied_prices.add(price)
            self.save_db()
            self.generate()
            self.show_toast("RE-SCANNING...")
        except: pass

    def save_db(self):
        try:
            code = self.get_vendor_code()
            db_path = os.path.join(self.db_dir, f"vendor_{code}.txt")
            with open(db_path, 'w', encoding='utf-8') as f:
                for p in sorted(list(self.occupied_prices), reverse=True):
                    f.write(f"{p}\n")
            self.status_label.config(text=f"SYNCED: {len(self.occupied_prices)} ITEMS")
        except: pass

    def create_backup(self):
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d")
            backup_path = os.path.join(self.backup_dir, f"backup_{timestamp}")
            if os.path.exists(self.db_dir) and os.listdir(self.db_dir):
                if not os.path.exists(backup_path): shutil.copytree(self.db_dir, backup_path)
            all_b = [os.path.join(self.backup_dir, d) for d in os.listdir(self.backup_dir) if os.path.isdir(os.path.join(self.backup_dir, d))]
            all_b.sort(key=os.path.getmtime)
            while len(all_b) > 10: shutil.rmtree(all_b.pop(0))
        except: pass

    def import_txt(self):
        path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if path:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                added = 0
                for line in f:
                    m = re.search(r'^(\d+)', line.strip())
                    if m: self.occupied_prices.add(int(m.group(1))); added += 1
            self.save_db(); self.show_toast(f"IMPORTED {added} UNITS")

    def quick_search(self):
        val = self.search_entry.get().strip()
        if not val or val == "Перевірка ціни...":
            self.search_res_label.config(text="READY", fg='#30363d')
            return
        if val.isdigit() and int(val) in self.occupied_prices:
            self.search_res_label.config(text="● OCCUPIED", fg='#f85149')
        else:
            self.search_res_label.config(text="● AVAILABLE", fg='#00ff9d')

    def show_toast(self, text, color='#58a6ff'):
        self.toast_label.config(text=text, fg=color)
        threading.Timer(2.5, lambda: self.toast_label.config(text="")).start()

    def clear_fields(self):
        self.price_entry.delete(0, tk.END)
        self.res_var.set("---")
        self.price_entry.focus()

if __name__ == "__main__":
    hide_console()
    root = tk.Tk()
    app = ArticulMaster(root)
    root.mainloop()