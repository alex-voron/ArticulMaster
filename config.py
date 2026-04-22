import os
import base64

# ПРИХОВАНІ КЛЮЧІ
P1, P2, P3 = "979182815966-", "881ss3mv0rbgptiht62blin08g2jgbbq", ".apps.googleusercontent.com"
S1, S2, S3 = "GOCSPX-", "2ZIN8P8_N8VDlrixaY", "xVOfBrnpVN"

def get_keys():
    return f"{P1}{P2}{P3}", f"{S1}{S2}{S3}"

CURRENT_VERSION = "4.1" # Нова мажорна версія після рефакторингу
VERSION_URL = "https://raw.githubusercontent.com/alex-voron/ArticulMaster/refs/heads/main/version.txt"
# URL тепер буде вести на ZIP для оновлення всіх модулів відразу
UPDATE_URL = "https://github.com/alex-voron/ArticulMaster/archive/refs/heads/main.zip"
# Додаємо шлях до картинки. Покладіть файл 'logo.png' в ту ж папку, де й код.
LOGO_FILE = "logo.png"

# Шляхи
APPDATA_DIR = os.path.join(os.getenv('APPDATA'), "ArticulMasterPro")
DB_DIR = os.path.join(APPDATA_DIR, "database")
BACKUP_DIR = os.path.join(APPDATA_DIR, "backups")
LOG_DIR = os.path.join(APPDATA_DIR, "logs")
TOKEN_FILE = os.path.join(APPDATA_DIR, "cloud_token.json")
SECRETS_FILE = os.path.join(APPDATA_DIR, "client_secrets.json")

VENDORS = {
    "207": "Pc.Lviv", "212": "eLaptop", "33": "PXL", "37": "Fortserg1",
    "241": "Gadgetusa", "11": "It-Technolodgy", "213": "IT-Lviv",
    "233": "LPStore", "228": "Ruslan111", "224": "SvChoice"
}