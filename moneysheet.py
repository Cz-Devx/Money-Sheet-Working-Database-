import calendar
import hashlib
import json
import os
import random
import string
import tkinter as tk
from datetime import date, datetime
from tkinter import messagebox, ttk
import psycopg2

# ==========================================================
# CONSTANTS & DEFAULTS
# ==========================================================
CATS = [
    "🛒 Groceries", "🥦 Vegetables & Fruits", "🥛 Milk & Dairy", "🥚 Eggs",
    "🍗 Chicken & Mutton", "🐟 Fish & Seafood", "🍚 Rice & Grains", "🌾 Pulses & Dal",
    "🫒 Cooking Oil", "🧂 Masala & Spices", "☕ Tea / Coffee", "🍬 Sugar & Sweets",
    "🍞 Bakery & Biscuits", "🥤 Beverages & Juice", "🧊 Water Can", "🧴 Toiletries & Soap",
    "🧼 Cleaning Supplies", "🍿 Snacks", "🍱 Dining Out", "🏠 Rent / Housing",
    "🏢 Society Maintenance", "💡 Electricity", "🚰 Water", "🔥 Cooking Gas", "📱 Mobile & Recharge",
    "🌐 Broadband / Internet", "📺 DTH / OTT", "⛽ Fuel / Petrol", "🔧 Vehicle Service",
    "🚕 Cab / Transport", "✈️ Travel & Holidays", "🩺 Health / Doctor", "💊 Medicines",
    "🏥 Health Insurance", "🚗 Vehicle Insurance", "🛡️ Life Insurance / LIC", "🎓 Education / Fees",
    "📚 Books & Stationery", "👕 Clothing & Footwear", "💇 Personal Care", "🧹 Household Items",
    "🔨 Home Repairs", "🧽 Domestic Help", "🎬 Entertainment", "🏦 EMI / Loan", "💳 Credit Card Bill",
    "🏛️ Property Tax", "🎁 Gifts & Donations", "🪔 Festivals & Functions", "📈 Savings / Investment",
    "🏧 Bank Charges", "🐕 Pet Care", "👶 Childcare", "💻 Electronics", "🧾 Subscriptions",
    "📦 Miscellaneous"
]

SRCS = [
    "💼 Salary", "🧑‍💻 Freelance / Consulting", "🏦 Bank Interest", "🏠 Rent Received",
    "📈 Dividends", "🎉 Bonus / Incentive", "💵 Refund / Reimbursement", "🎁 Gift Received",
    "👴 Family Support", "💰 Other Income"
]

METHODS = ["📲 GPay", "📱 PhonePe", "💵 Cash", "🏦 Net Banking", "💳 Card"]
GENERIC = ["💵 Cash in Hand", "📳 UPI - Other", "👛 Wallet", "🧾 Cheque", "🔁 Auto-debit"]
PEMOJI = ["👨", "👩", "🧑", "🧒"]

DEF_BILLS = [
    ["🏠 House Rent", "rent", 5], ["🏢 Society Maintenance", "maintenance", 5],
    ["💡 Electricity Bill", "electricity", 10], ["🚰 Water Bill", "water", 10],
    ["🔥 Cooking Gas (LPG)", "lpg", 12], ["📱 Mobile Recharge", "mobile", 8],
    ["🌐 Broadband / Internet", "broadband", 8], ["📺 DTH / OTT", "dth", 8],
    ["🏥 Health Insurance", "health insurance", 15], ["🚗 Vehicle Insurance", "vehicle insurance", 20],
    ["🛡️ Life Insurance / LIC", "lic", 20], ["🏦 Home Loan EMI", "home loan", 5],
    ["🚙 Vehicle Loan EMI", "vehicle loan", 5], ["💳 Credit Card Bill", "credit card", 18],
    ["🎓 School / College Fees", "fees", 10], ["🧽 Domestic Help Salary", "domestic help", 1],
    ["📈 SIP / Investment", "sip", 5], ["🏛️ Property Tax", "property tax", 25],
    ["🏋️ Gym / Club", "gym", 5], ["💻 Subscriptions", "subscription", 1]
]

# Cloud Database URL with your password integrated
CLOUD_DB_URL = "postgresql://postgres:ofCqV1QYqqwS9iKg@db.fbqwrjavtjmhudmgmdwj.supabase.co:5432/postgres"

# ==========================================================
# CLOUD DATABASE & USER LOGIC
# ==========================================================
class DatabaseManager:
    def __init__(self, db_url=CLOUD_DB_URL):
        self.db_url = db_url
        self.init_db()

    def get_connection(self):
        return psycopg2.connect(self.db_url)

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                user_id INTEGER PRIMARY KEY,
                name TEXT,
                source TEXT,
                opening REAL,
                em_months INTEGER,
                people TEXT,
                cats TEXT,
                srcs TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id TEXT PRIMARY KEY,
                user_id INTEGER,
                date TEXT,
                person TEXT,
                kind TEXT,
                cat TEXT,
                item TEXT,
                amt REAL,
                pay TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bills (
                id TEXT PRIMARY KEY,
                user_id INTEGER,
                name TEXT,
                match TEXT,
                day INTEGER,
                expected REAL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        conn.commit()
        cursor.close()
        conn.close()

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def register_user(self, username, password):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            pwd_hash = self.hash_password(password)
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING id", (username, pwd_hash))
            user_id = cursor.fetchone()[0]
            
            cursor.execute('''
                INSERT INTO settings (user_id, name, source, opening, em_months, people, cats, srcs)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (user_id, "Money Sheet", "💼 Salary", 0.0, 6, json.dumps(["Vivek", "Revathi", "", ""]), json.dumps(CATS), json.dumps(SRCS)))
            
            for b in DEF_BILLS:
                b_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
                cursor.execute('''
                    INSERT INTO bills (id, user_id, name, match, day, expected)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (b_id, user_id, b[0], b[1], b[2], 0.0))
                
            conn.commit()
            return True, "Registration successful!"
        except psycopg2.IntegrityError:
            conn.rollback()
            return False, "Username already exists."
        finally:
            cursor.close()
            conn.close()

    def verify_user(self, username, password):
        conn = self.get_connection()
        cursor = conn.cursor()
        pwd_hash = self.hash_password(password)
        cursor.execute("SELECT id FROM users WHERE username = %s AND password_hash = %s", (username, pwd_hash))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return row[0] if row else None


# ==========================================================
# MONEY SHEET USER DATA MODEL
# ==========================================================
class MoneySheetLogic:
    def __init__(self, user_id):
        self.user_id = user_id
        self.db = DatabaseManager()
        self.cur_y = datetime.now().year
        self.cur_m = datetime.now().month - 1
        self.load_user_data()

    def load_user_data(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT name, source, opening, em_months, people, cats, srcs FROM settings WHERE user_id = %s", (self.user_id,))
        row = cursor.fetchone()
        if row:
            self.name, self.source, self.opening, self.em_months, people_json, cats_json, srcs_json = row
            self.people = json.loads(people_json)
            self.cats = json.loads(cats_json)
            self.srcs = json.loads(srcs_json)
        else:
            self.name, self.source, self.opening, self.em_months = "Money Sheet", "💼 Salary", 0.0, 6
            self.people, self.cats, self.srcs = ["Vivek", "Revathi", "", ""], list(CATS), list(SRCS)

        cursor.execute("SELECT id, date, person, kind, cat, item, amt, pay FROM transactions WHERE user_id = %s", (self.user_id,))
        self.tx = []
        for r in cursor.fetchall():
            self.tx.append({"id": r[0], "date": r[1], "person": r[2], "kind": r[3], "cat": r[4], "item": r[5], "amt": r[6], "pay": r[7]})

        cursor.execute("SELECT id, name, match, day, expected FROM bills WHERE user_id = %s", (self.user_id,))
        self.bills = []
        for r in cursor.fetchall():
            self.bills.append({"id": r[0], "name": r[1], "match": r[2], "day": r[3], "expected": r[4]})
            
        cursor.close()
        conn.close()

    def save_transaction(self, t):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO transactions (id, user_id, date, person, kind, cat, item, amt, pay)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (t["id"], self.user_id, t["date"], t["person"], t["kind"], t["cat"], t.get("item", ""), t["amt"], t["pay"]))
        conn.commit()
        cursor.close()
        conn.close()
        self.tx.append(t)

    def generate_uid(self):
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

    def p2(self, n):
        return str(n).zfill(2)

    def dim(self, y, m):
        return calendar.monthrange(y, m + 1)[1]

    def inr(self, n):
        return f"₹{round(abs(n)):,}"

    def sgn(self, n):
        return ("-" if n < 0 else "") + self.inr(n)

    def is_exp(self, t):
        return t.get("kind") == "exp"

    def is_inc(self, t):
        return t.get("kind") != "exp"

    def in_m(self, t):
        p = t["date"].split("-")
        return int(p[0]) == self.cur_y and int(p[1]) == (self.cur_m + 1)

    def before(self, t):
        return t["date"] < f"{self.cur_y}-{self.p2(self.cur_m + 1)}-01"

    def live_people(self):
        return [f"{PEMOJI[i]} {n.strip()}" for i, n in enumerate(self.people) if n.strip()]

    def all_people(self):
        return self.live_people() + ["👪 Family (Shared)"]

    def fig(self):
        inc = [t for t in self.tx if self.is_inc(t)]
        exp = [t for t in self.tx if self.is_exp(t)]

        opening = (self.opening +
                   sum(t["amt"] for t in inc if self.before(t)) -
                   sum(t["amt"] for t in exp if self.before(t)))

        primary = sum(t["amt"] for t in inc if self.in_m(t) and t["kind"] == "pri")
        extra = sum(t["amt"] for t in inc if self.in_m(t) and t["kind"] == "ext")
        income = primary + extra
        spent = sum(t["amt"] for t in exp if self.in_m(t))
        avail = opening + income
        closing = avail - spent

        dm = self.dim(self.cur_y, self.cur_m)
        now_dt = datetime.now()
        if now_dt.year == self.cur_y and now_dt.month == (self.cur_m + 1):
            elapsed = now_dt.day
        elif date(self.cur_y, self.cur_m + 1, 1) < date(now_dt.year, now_dt.month, 1):
            elapsed = dm
        else:
            elapsed = 0

        entries_m = [t for t in exp if self.in_m(t)]
        largest = max((t["amt"] for t in entries_m), default=0)

        return {
            "opening": opening, "primary": primary, "extra": extra, "income": income,
            "spent": spent, "avail": avail, "closing": closing, "dm": dm, "elapsed": elapsed,
            "entries": len(entries_m), "largest": largest
        }

    def bill_paid(self, b):
        if not b.get("match"):
            return 0
        q = b["match"].lower()
        return sum(
            t["amt"] for t in self.tx
            if self.is_exp(t) and self.in_m(t) and (q in t.get("item", "").lower() or q in t.get("cat", "").lower())
        )

    def bill_stat(self, b):
        paid = self.bill_paid(b)
        if not b.get("expected", 0) and not paid:
            return "—"
        if paid > 0:
            return "Paid"
        now_dt = datetime.now()
        is_now = (now_dt.year == self.cur_y and now_dt.month == (self.cur_m + 1))
        dm = self.dim(self.cur_y, self.cur_m)
        due_day = min(b.get("day", 1), dm)
        due_date = date(self.cur_y, self.cur_m + 1, due_day)

        if is_now:
            if now_dt.date() > due_date:
                return "Overdue"
            return "Due"
        if date(self.cur_y, self.cur_m + 1, 1) < date(now_dt.year, now_dt.month, 1):
            return "Not paid"
        return "Upcoming"


# ==========================================================
# MAIN APPLICATION GUI
# ==========================================================
class MoneySheetGUI:
    def __init__(self, root, user_id):
        self.root = root
        self.logic = MoneySheetLogic(user_id)
        self.root.title(f"Money Sheet — {self.logic.name}")
        self.root.geometry("850x650")
        self.root.configure(bg="#2D3561")

        self.setup_styles()
        self.build_ui()
        self.refresh_data()

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("TNotebook", background="#2D3561", borderwidth=0)
        self.style.configure("TNotebook.Tab", background="#3D4A8A", foreground="white", padding=[12, 6], font=("Helvetica", 10, "bold"))
        self.style.map("TNotebook.Tab", background=[("selected", "#6C63FF")], foreground=[("selected", "white")])

    def build_ui(self):
        header_frame = tk.Frame(self.root, bg="#2D3561", pady=10)
        header_frame.pack(fill="x")

        title_lbl = tk.Label(header_frame, text=f"💰 {self.logic.name}", font=("Helvetica", 18, "bold"), fg="#FFC107", bg="#2D3561")
        title_lbl.pack(side="left", padx=20)

        month_control_frame = tk.Frame(header_frame, bg="#2D3561")
        month_control_frame.pack(side="right", padx=20)

        btn_prev = tk.Button(month_control_frame, text="◀", font=("Helvetica", 10, "bold"), command=self.prev_month, bg="#3D4A8A", fg="white", bd=0, padx=8)
        btn_prev.pack(side="left", padx=2)

        self.lbl_month = tk.Label(month_control_frame, text="", font=("Courier", 12, "bold"), fg="white", bg="#2D3561", width=12)
        self.lbl_month.pack(side="left", padx=5)

        btn_next = tk.Button(month_control_frame, text="▶", font=("Helvetica", 10, "bold"), command=self.next_month, bg="#3D4A8A", fg="white", bd=0, padx=8)
        btn_next.pack(side="left", padx=2)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_dashboard = tk.Frame(self.notebook, bg="#F1F0F6")
        self.tab_add = tk.Frame(self.notebook, bg="#F1F0F6")
        self.tab_bills = tk.Frame(self.notebook, bg="#F1F0F6")

        self.notebook.add(self.tab_dashboard, text="📊 Dashboard")
        self.notebook.add(self.tab_add, text="➕ Add Entry")
        self.notebook.add(self.tab_bills, text="🔔 Bills")

        self.build_dashboard_tab()
        self.build_add_tab()
        self.build_bills_tab()

    def build_dashboard_tab(self):
        self.frame_stats = tk.LabelFrame(self.tab_dashboard, text=" Monthly Summary ", font=("Helvetica", 11, "bold"), bg="#F1F0F6", fg="#2D3561", padx=10, pady=10)
        self.frame_stats.pack(fill="x", padx=15, pady=10)

        self.lbl_opening = tk.Label(self.frame_stats, text="Brought Forward: ₹0", font=("Helvetica", 10), bg="#F1F0F6", anchor="w")
        self.lbl_opening.grid(row=0, column=0, sticky="w", padx=10, pady=5)

        self.lbl_income = tk.Label(self.frame_stats, text="Total Income: ₹0", font=("Helvetica", 10, "bold"), fg="#1B5E20", bg="#F1F0F6", anchor="w")
        self.lbl_income.grid(row=0, column=1, sticky="w", padx=10, pady=5)

        self.lbl_spent = tk.Label(self.frame_stats, text="Spent So Far: ₹0", font=("Helvetica", 10, "bold"), fg="#C62828", bg="#F1F0F6", anchor="w")
        self.lbl_spent.grid(row=1, column=0, sticky="w", padx=10, pady=5)

        self.lbl_closing = tk.Label(self.frame_stats, text="Closing Balance: ₹0", font=("Helvetica", 11, "bold"), fg="#2D3561", bg="#F1F0F6", anchor="w")
        self.lbl_closing.grid(row=1, column=1, sticky="w", padx=10, pady=5)

        frame_tx = tk.LabelFrame(self.tab_dashboard, text=" Ledger Entries ", font=("Helvetica", 11, "bold"), bg="#F1F0F6", fg="#2D3561", padx=10, pady=10)
        frame_tx.pack(fill="both", expand=True, padx=15, pady=5)

        columns = ("date", "type", "category", "item", "person", "amount")
        self.tree_tx = ttk.Treeview(frame_tx, columns=columns, show="headings", height=10)
        self.tree_tx.heading("date", text="Date")
        self.tree_tx.heading("type", text="Type")
        self.tree_tx.heading("category", text="Category/Source")
        self.tree_tx.heading("item", text="Item/Remarks")
        self.tree_tx.heading("person", text="Person")
        self.tree_tx.heading("amount", text="Amount")

        self.tree_tx.column("date", width=90, anchor="center")
        self.tree_tx.column("type", width=80, anchor="center")
        self.tree_tx.column("category", width=150)
        self.tree_tx.column("item", width=180)
        self.tree_tx.column("person", width=120)
        self.tree_tx.column("amount", width=100, anchor="e")

        self.tree_tx.pack(fill="both", expand=True)

    def build_add_tab(self):
        container = tk.Frame(self.tab_add, bg="#F1F0F6", padx=20, pady=20)
        container.pack(fill="both", expand=True)

        tk.Label(container, text="Entry Type:", font=("Helvetica", 10, "bold"), bg="#F1F0F6").grid(row=0, column=0, sticky="w", pady=8)
        self.var_kind = tk.StringVar(value="exp")
        frame_radio = tk.Frame(container, bg="#F1F0F6")
        frame_radio.grid(row=0, column=1, sticky="w")
        tk.Radiobutton(frame_radio, text="Money Out (Expense)", variable=self.var_kind, value="exp", bg="#F1F0F6", command=self.update_add_categories).pack(side="left", padx=5)
        tk.Radiobutton(frame_radio, text="Money In (Income)", variable=self.var_kind, value="pri", bg="#F1F0F6", command=self.update_add_categories).pack(side="left", padx=5)

        tk.Label(container, text="Amount (₹):", font=("Helvetica", 10, "bold"), bg="#F1F0F6").grid(row=1, column=0, sticky="w", pady=8)
        self.ent_amt = tk.Entry(container, font=("Helvetica", 10), width=30)
        self.ent_amt.grid(row=1, column=1, sticky="w")

        tk.Label(container, text="Category / Source:", font=("Helvetica", 10, "bold"), bg="#F1F0F6").grid(row=2, column=0, sticky="w", pady=8)
        self.cbo_cat = ttk.Combobox(container, width=28, state="readonly")
        self.cbo_cat.grid(row=2, column=1, sticky="w")

        tk.Label(container, text="Item / Remarks:", font=("Helvetica", 10, "bold"), bg="#F1F0F6").grid(row=3, column=0, sticky="w", pady=8)
        self.ent_item = tk.Entry(container, font=("Helvetica", 10), width=30)
        self.ent_item.grid(row=3, column=1, sticky="w")

        tk.Label(container, text="Person:", font=("Helvetica", 10, "bold"), bg="#F1F0F6").grid(row=4, column=0, sticky="w", pady=8)
        self.cbo_person = ttk.Combobox(container, width=28, state="readonly")
        self.cbo_person.grid(row=4, column=1, sticky="w")

        tk.Label(container, text="Date (YYYY-MM-DD):", font=("Helvetica", 10, "bold"), bg="#F1F0F6").grid(row=5, column=0, sticky="w", pady=8)
        self.ent_date = tk.Entry(container, font=("Helvetica", 10), width=30)
        self.ent_date.insert(0, str(date.today()))
        self.ent_date.grid(row=5, column=1, sticky="w")

        btn_save = tk.Button(container, text="💾 Save Transaction", font=("Helvetica", 11, "bold"), bg="#6C63FF", fg="white", bd=0, pady=8, padx=15, command=self.save_transaction)
        btn_save.grid(row=6, column=1, sticky="w", pady=20)

    def build_bills_tab(self):
        frame_bills = tk.LabelFrame(self.tab_bills, text=" Recurring Bills Status ", font=("Helvetica", 11, "bold"), bg="#F1F0F6", fg="#2D3561", padx=10, pady=10)
        frame_bills.pack(fill="both", expand=True, padx=15, pady=15)

        columns = ("name", "day", "expected", "paid", "status")
        self.tree_bills = ttk.Treeview(frame_bills, columns=columns, show="headings", height=12)
        self.tree_bills.heading("name", text="Bill Name")
        self.tree_bills.heading("day", text="Due Day")
        self.tree_bills.heading("expected", text="Expected")
        self.tree_bills.heading("paid", text="Paid So Far")
        self.tree_bills.heading("status", text="Status")

        self.tree_bills.column("name", width=220)
        self.tree_bills.column("day", width=80, anchor="center")
        self.tree_bills.column("expected", width=120, anchor="e")
        self.tree_bills.column("paid", width=120, anchor="e")
        self.tree_bills.column("status", width=120, anchor="center")

        self.tree_bills.pack(fill="both", expand=True)

    def update_add_categories(self):
        is_exp = self.var_kind.get() == "exp"
        pool = self.logic.cats if is_exp else self.logic.srcs
        self.cbo_cat["values"] = pool
        if pool:
            self.cbo_cat.current(0)

    def refresh_data(self):
        m_name = calendar.month_name[self.logic.cur_m + 1]
        self.lbl_month.config(text=f"{m_name[:3]} {self.logic.cur_y}")

        f = self.logic.fig()
        self.lbl_opening.config(text=f"Brought Forward: {self.logic.sgn(f['opening'])}")
        self.lbl_income.config(text=f"Total Income: {self.logic.inr(f['income'])}")
        self.lbl_spent.config(text=f"Spent So Far: {self.logic.inr(f['spent'])}")
        self.lbl_closing.config(text=f"Closing Balance: {self.logic.sgn(f['closing'])}")

        for row in self.tree_tx.get_children():
            self.tree_tx.delete(row)

        month_tx = [t for t in self.logic.tx if self.logic.in_m(t)]
        month_tx.sort(key=lambda x: x["date"], reverse=True)

        for t in month_tx:
            amt_str = f"-{self.logic.inr(t['amt'])}" if self.logic.is_exp(t) else f"+{self.logic.inr(t['amt'])}"
            kind_str = "Expense" if self.logic.is_exp(t) else "Income"
            self.tree_tx.insert("", "end", values=(t["date"], kind_str, t["cat"], t.get("item", ""), t.get("person", ""), amt_str))

        self.cbo_person["values"] = self.logic.all_people()
        if self.logic.all_people():
            self.cbo_person.current(0)
        self.update_add_categories()

        for row in self.tree_bills.get_children():
            self.tree_bills.delete(row)

        for b in self.logic.bills:
            paid = self.logic.bill_paid(b)
            stat = self.logic.bill_stat(b)
            self.tree_bills.insert("", "end", values=(b["name"], b["day"], self.logic.inr(b.get("expected", 0)), self.logic.inr(paid), stat))

    def save_transaction(self):
        try:
            amt = float(self.ent_amt.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid numeric amount.")
            return

        cat = self.cbo_cat.get()
        if not cat:
            messagebox.showerror("Error", "Please select or enter a category.")
            return

        t = {
            "id": self.logic.generate_uid(),
            "date": self.ent_date.get().strip(),
            "person": self.cbo_person.get(),
            "kind": self.var_kind.get(),
            "cat": cat,
            "item": self.ent_item.get().strip(),
            "amt": amt,
            "pay": "GPay"
        }

        self.logic.save_transaction(t)

        self.ent_amt.delete(0, tk.END)
        self.ent_item.delete(0, tk.END)

        messagebox.showinfo("Success", f"Saved {self.logic.inr(amt)} successfully!")
        self.refresh_data()
        self.notebook.select(self.tab_dashboard)

    def prev_month(self):
        self.logic.cur_m -= 1
        if self.logic.cur_m < 0:
            self.logic.cur_m = 11
            self.logic.cur_y -= 1
        self.refresh_data()

    def next_month(self):
        self.logic.cur_m += 1
        if self.logic.cur_m > 11:
            self.logic.cur_m = 0
            self.logic.cur_y += 1
        self.refresh_data()


# ==========================================================
# AUTHENTICATION WINDOW
# ==========================================================
class AuthWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Money Sheet — Login")
        self.root.geometry("400x320")
        self.root.configure(bg="#2D3561")
        self.db = DatabaseManager()
        self.user_id = None

        self.build_auth_ui()

    def build_auth_ui(self):
        frame = tk.Frame(self.root, bg="#2D3561", padx=20, pady=20)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="💰 Money Sheet", font=("Helvetica", 18, "bold"), fg="#FFC107", bg="#2D3561").pack(pady=10)

        tk.Label(frame, text="Username:", font=("Helvetica", 10, "bold"), fg="white", bg="#2D3561").pack(anchor="w")
        self.ent_user = tk.Entry(frame, font=("Helvetica", 11), width=28)
        self.ent_user.pack(pady=5)

        tk.Label(frame, text="Password:", font=("Helvetica", 10, "bold"), fg="white", bg="#2D3561").pack(anchor="w")
        self.ent_pass = tk.Entry(frame, font=("Helvetica", 11), width=28, show="*")
        self.ent_pass.pack(pady=5)

        btn_frame = tk.Frame(frame, bg="#2D3561")
        btn_frame.pack(pady=15)

        tk.Button(btn_frame, text="Log In", font=("Helvetica", 10, "bold"), bg="#6C63FF", fg="white", width=10, bd=0, command=self.login).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Register", font=("Helvetica", 10, "bold"), bg="#3D4A8A", fg="white", width=10, bd=0, command=self.register).pack(side="left", padx=5)

    def login(self):
        username = self.ent_user.get().strip()
        password = self.ent_pass.get().strip()
        if not username or not password:
            messagebox.showerror("Error", "Please fill in all fields.")
            return
        
        uid = self.db.verify_user(username, password)
        if uid:
            self.user_id = uid
            self.root.destroy()
        else:
            messagebox.showerror("Error", "Invalid username or password.")

    def register(self):
        username = self.ent_user.get().strip()
        password = self.ent_pass.get().strip()
        if not username or not password:
            messagebox.showerror("Error", "Please fill in all fields.")
            return

        success, msg = self.db.register_user(username, password)
        if success:
            messagebox.showinfo("Success", msg)
        else:
            messagebox.showerror("Error", msg)


if __name__ == "__main__":
    root = tk.Tk()
    auth = AuthWindow(root)
    root.mainloop()

    if auth.user_id:
        dash_root = tk.Tk()
        app = MoneySheetGUI(dash_root, auth.user_id)
        dash_root.mainloop()
