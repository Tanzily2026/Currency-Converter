import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import os
from datetime import datetime

# ---------- API Configuration ----------
# Free API from exchangerate-api.com – no API key required for basic usage
BASE_URL = "https://api.exchangerate-api.com/v4/latest/"

# ---------- History Manager ----------
class HistoryManager:
    def __init__(self, filename="history.json"):
        self.filename = filename
        self.history = []  # list of dicts: from, to, amount, result, rate, timestamp
        self.load()

    def load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            except:
                self.history = []

    def save(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)

    def add(self, from_curr, to_curr, amount, result, rate):
        entry = {
            "from": from_curr,
            "to": to_curr,
            "amount": amount,
            "result": result,
            "rate": rate,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.history.insert(0, entry)  # newest first
        self.save()

    def clear(self):
        self.history = []
        self.save()

    def get_all(self):
        return self.history

# ---------- API Wrapper ----------
class CurrencyAPI:
    @staticmethod
    def get_exchange_rate(from_curr, to_curr):
        """Returns (rate, error_message). If error, rate is None."""
        try:
            url = BASE_URL + from_curr
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "rates" in data and to_curr in data["rates"]:
                    return data["rates"][to_curr], None
                else:
                    return None, f"Валюта {to_curr} не найдена в ответе API"
            else:
                return None, f"Ошибка API: {response.status_code}"
        except requests.exceptions.RequestException as e:
            return None, f"Сетевая ошибка: {str(e)}"

# ---------- GUI Application ----------
class CurrencyConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Currency Converter")
        self.root.geometry("750x500")
        self.root.resizable(False, False)

        self.history_mgr = HistoryManager()
        self.currencies = ["USD", "EUR", "RUB", "GBP", "JPY", "CNY", "CHF", "CAD", "AUD", "TRY", "KZT", "UAH"]

        self._setup_ui()
        self._refresh_history()

    def _setup_ui(self):
        # ----- Conversion Frame -----
        conv_frame = ttk.LabelFrame(self.root, text="Конвертация валют", padding=10)
        conv_frame.pack(fill="x", padx=10, pady=5)

        # Amount
        ttk.Label(conv_frame, text="Сумма:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.amount_entry = ttk.Entry(conv_frame, width=15)
        self.amount_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # From currency
        ttk.Label(conv_frame, text="Из валюты:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.from_currency = ttk.Combobox(conv_frame, values=self.currencies, width=10, state="readonly")
        self.from_currency.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.from_currency.current(0)

        # To currency
        ttk.Label(conv_frame, text="В валюту:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.to_currency = ttk.Combobox(conv_frame, values=self.currencies, width=10, state="readonly")
        self.to_currency.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        self.to_currency.current(1)

        # Convert button
        self.convert_btn = ttk.Button(conv_frame, text="Конвертировать", command=self.convert)
        self.convert_btn.grid(row=3, column=0, columnspan=2, pady=10)

        # Result label
        self.result_label = ttk.Label(conv_frame, text="", font=("Arial", 12, "bold"), foreground="green")
        self.result_label.grid(row=4, column=0, columnspan=2)

        # ----- History Table -----
        hist_frame = ttk.LabelFrame(self.root, text="История конвертаций", padding=10)
        hist_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("timestamp", "amount", "from", "to", "result", "rate")
        self.tree = ttk.Treeview(hist_frame, columns=columns, show="headings", height=12)
        self.tree.heading("timestamp", text="Дата/время")
        self.tree.heading("amount", text="Сумма")
        self.tree.heading("from", text="Из")
        self.tree.heading("to", text="В")
        self.tree.heading("result", text="Результат")
        self.tree.heading("rate", text="Курс")

        self.tree.column("timestamp", width=140)
        self.tree.column("amount", width=70)
        self.tree.column("from", width=50)
        self.tree.column("to", width=50)
        self.tree.column("result", width=100)
        self.tree.column("rate", width=80)

        scrollbar = ttk.Scrollbar(hist_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        clear_btn = ttk.Button(hist_frame, text="Очистить историю", command=self.clear_history)
        clear_btn.pack(side="bottom", pady=5)

    def convert(self):
        amount_str = self.amount_entry.get().strip()
        if not amount_str:
            messagebox.showerror("Ошибка", "Введите сумму")
            return
        try:
            amount = float(amount_str)
            if amount <= 0:
                messagebox.showerror("Ошибка", "Сумма должна быть положительным числом")
                return
        except ValueError:
            messagebox.showerror("Ошибка", "Сумма должна быть числом (например, 100.50)")
            return

        from_curr = self.from_currency.get()
        to_curr = self.to_currency.get()

        if from_curr == to_curr:
            result = amount
            rate = 1.0
            self.result_label.config(text=f"{amount} {from_curr} = {result} {to_curr}")
            self.history_mgr.add(from_curr, to_curr, amount, result, rate)
            self._refresh_history()
            return

        rate, error = CurrencyAPI.get_exchange_rate(from_curr, to_curr)
        if rate is None:
            messagebox.showerror("Ошибка получения курса", error)
            return

        result = round(amount * rate, 2)
        self.result_label.config(text=f"{amount} {from_curr} = {result} {to_curr} (курс: {rate})")
        self.history_mgr.add(from_curr, to_curr, amount, result, rate)
        self._refresh_history()

    def _refresh_history(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for entry in self.history_mgr.get_all():
            self.tree.insert("", "end", values=(
                entry["timestamp"],
                entry["amount"],
                entry["from"],
                entry["to"],
                entry["result"],
                entry["rate"]
            ))

    def clear_history(self):
        if messagebox.askyesno("Подтверждение", "Очистить всю историю конвертаций?"):
            self.history_mgr.clear()
            self._refresh_history()
            self.result_label.config(text="")

# ---------- Main ----------
if __name__ == "__main__":
    root = tk.Tk()
    app = CurrencyConverterApp(root)
    root.mainloop()