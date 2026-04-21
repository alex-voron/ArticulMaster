import os
import re
from config import DB_DIR

class ArticulLogic:
    def __init__(self):
        self.occupied_prices = set()

    def get_vendor_code(self, vendor_str):
        if not vendor_str: return "207"
        match = re.search(r'\[(\d+)\]', vendor_str)
        return match.group(1) if match else "207"

    def load_local_data(self, code):
        db_path = os.path.join(DB_DIR, f"vendor_{code}.txt")
        self.occupied_prices = set()
        if os.path.exists(db_path):
            with open(db_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if line.strip().isdigit(): 
                        self.occupied_prices.add(int(line.strip()))
        return len(self.occupied_prices)

    def generate_articul(self, price_val, code):
        curr = int(price_val)
        while curr in self.occupied_prices:
            curr -= 1
        self.occupied_prices.add(curr)
        return f"{curr}_{code}", curr

    def save_to_file(self, code):
        db_path = os.path.join(DB_DIR, f"vendor_{code}.txt")
        with open(db_path, 'w', encoding='utf-8') as f:
            for p in sorted(list(self.occupied_prices), reverse=True):
                f.write(f"{p}\n")

    # НОВИЙ МЕТОД
    def get_sorted_prices(self):
        """Повертає список цін від найбільшої до найменшої"""
        return sorted(list(self.occupied_prices), reverse=True)