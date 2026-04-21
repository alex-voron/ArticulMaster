import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import os, re, threading, shutil, sys, requests
from datetime import datetime, timedelta

# Поточна версія програми
CURRENT_VERSION = "1.4"
VERSION_URL = "https://raw.githubusercontent.com/alex-voron/ArticulMaster/refs/heads/main/version.txt"
UPDATE_URL = "https://raw.githubusercontent.com/alex-voron/ArticulMaster/refs/heads/main/ArticulMaster.pyw"

class ArticulMaster:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Test Update v{CURRENT_VERSION}")
        self.root.geometry("300x200")
        
        tk.Label(root, text="Діагностика оновлення...").pack(pady=20)
        
        # Запускаємо перевірку оновлення
        threading.Thread(target=self.check_updates, daemon=True).start()

    def check_updates(self):
        print("DEBUG: Починаю перевірку оновлень...")
        try:
            r = requests.get(VERSION_URL, timeout=10)
            print(f"DEBUG: Статус відповіді: {r.status_code}")
            if r.status_code == 200:
                online_v = r.text.strip()
                print(f"DEBUG: Версія на GitHub: '{online_v}'")
                print(f"DEBUG: Локальна версія: '{CURRENT_VERSION}'")
                
                # Використовуємо float для сумісності зі старим кодом
                if float(online_v) > float(CURRENT_VERSION):
                    print("DEBUG: Знайдено нову версію!")
                    if messagebox.askyesno("Оновлення", f"Доступна версія {online_v}. Оновити?"):
                        self.update_program()
                else:
                    print("DEBUG: Оновлення не потрібне.")
        except Exception as e:
            print(f"DEBUG: КРИТИЧНА ПОМИЛКА: {e}")

    def update_program(self):
        print("DEBUG: Запускаю процес завантаження...")
        try:
            response = requests.get(UPDATE_URL, timeout=15)
            if response.status_code == 200:
                with open("ArticulMaster.pyw", 'wb') as f:
                    f.write(response.content)
                print("DEBUG: Файл завантажено успішно!")
                messagebox.showinfo("OK", "Новий файл завантажено! Запустіть ArticulMaster.pyw")
                self.root.destroy()
        except Exception as e:
            print(f"DEBUG: Помилка завантаження: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ArticulMaster(root)
    root.mainloop()