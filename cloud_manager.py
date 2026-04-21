import threading
import os
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from config import SECRETS_FILE, TOKEN_FILE

class CloudManager:
    def __init__(self):
        self.drive = None

    def initialize(self, on_success, on_error):
        """Запуск ініціалізації в окремому потоці"""
        def task():
            try:
                gauth = GoogleAuth()
                GoogleAuth.DEFAULT_SETTINGS['client_config_file'] = SECRETS_FILE
                gauth.LoadCredentialsFile(TOKEN_FILE)
                
                if gauth.credentials is None:
                    gauth.LocalWebserverAuth()
                    gauth.SaveCredentialsFile(TOKEN_FILE)
                elif gauth.access_token_expired:
                    gauth.Refresh()
                else:
                    gauth.Authorize()
                    
                self.drive = GoogleDrive(gauth)
                on_success() # Викликаємо функцію успіху (наприклад, показ тосту)
            except Exception as e:
                print(f"Cloud init error: {e}")
                on_error()

        threading.Thread(target=task, daemon=True).start()

    def upload_file(self, filename, local_path):
        """Відправка файлу на диск (одностороння синхронізація)"""
        if not self.drive: return
        def task():
            try:
                file_list = self.drive.ListFile({'q': f"title = '{filename}' and trashed = false"}).GetList()
                f = file_list[0] if file_list else self.drive.CreateFile({'title': filename})
                f.SetContentFile(local_path)
                f.Upload()
            except: pass
        threading.Thread(target=task, daemon=True).start()

    def download_file(self, filename, local_path, on_complete):
        """Завантаження файлу з диска (ручне відновлення)"""
        if not self.drive: return
        def task():
            try:
                file_list = self.drive.ListFile({'q': f"title = '{filename}' and trashed = false"}).GetList()
                if file_list:
                    file_list[0].GetContentFile(local_path)
                    on_complete()
            except: pass
        threading.Thread(target=task, daemon=True).start()