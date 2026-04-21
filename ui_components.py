import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
import config

class UIManager:
    def __init__(self, root):
        self.root = root
        self.bg_color = '#0b0d11'
        self.accent_green = '#00ff9d'
        self.setup_styles()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        self.root.option_add("*TCombobox*Listbox.background", "#1c2128")
        self.root.option_add("*TCombobox*Listbox.foreground", "#ffffff")
        self.root.option_add("*TCombobox*Listbox.font", ("Segoe UI", 12))
        
        style.configure("TCombobox", 
                        fieldbackground="#1c2128", 
                        background=self.bg_color, 
                        foreground="#ffffff", 
                        borderwidth=0,
                        font=("Segoe UI", 12, "bold"),
                        padding=8,
                        arrowcolor=self.accent_green)
        
        style.map("TCombobox",
                  fieldbackground=[("readonly", "#1c2128"), ("focus", "#1c2128")],
                  foreground=[("readonly", "#ffffff"), ("focus", "#ffffff")],
                  selectbackground=[("readonly", "#1c2128"), ("focus", "#1c2128")],
                  selectforeground=[("readonly", "#ffffff"), ("focus", "#ffffff")])

    def add_background_logo(self, parent_frame):
        """Метод з гарантованим пошуком шляху до файлу"""
        try:
            # Визначаємо шлях до папки, де лежить цей скрипт
            if getattr(sys, 'frozen', False):
                # Якщо програма скомпільована в .exe
                base_path = os.path.dirname(sys.executable)
            else:
                # Якщо запущено як .pyw / .py
                base_path = os.path.dirname(os.path.abspath(__file__))

            logo_path = os.path.join(base_path, config.LOGO_FILE)

            # Перевірка наявності файлу
            if not os.path.exists(logo_path):
                print(f"DEBUG: Файл не знайдено за шляхом: {logo_path}")
                return

            from PIL import Image, ImageTk
            
            img = Image.open(logo_path)
            # Примусово робимо розмір, щоб вписався в інтерфейс
            img = img.resize((320, 320), Image.Resampling.LANCZOS)
            
            self.logo_img = ImageTk.PhotoImage(img)
            
            # Створюємо мітку для лого
            logo_label = tk.Label(parent_frame, image=self.logo_img, bg=self.bg_color, bd=0)
            # Центруємо
            logo_label.place(relx=0.5, rely=0.5, anchor='center')
            # Відправляємо на задній план, щоб не перекривав кнопки
            logo_label.lower()
            
            print("DEBUG: Логотип успішно відображено!")

        except ImportError:
            messagebox.showwarning("UI Error", "Встанови Pillow: pip install Pillow")
        except Exception as e:
            print(f"DEBUG: Помилка логотипа: {e}")