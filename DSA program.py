# -*- coding: utf-8 -*-
"""
@author: Shaz
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
import hashlib
from datetime import datetime
import os

DB_NAME = "gilded_fork_enterprise.db"
THEME_COLOR = "#2C3E50"
ACCENT_COLOR = "#E74C3C"
BG_COLOR = "#ECF0F1"
FONT_MAIN = ("Helvetica", 10)
FONT_HEADER = ("Helvetica", 14, "bold")
TAX_RATE = 0.08

class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME)
        self.cur = self.conn.cursor()
        self.initialize_tables()
        self.seed_data()

    def initialize_tables(self):
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE,
                password_hash TEXT,
                role TEXT
            )
        """)
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE
            )
        """)
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS menu_items (
                id INTEGER PRIMARY KEY,
                category_id INTEGER,
                name TEXT,
                price REAL,
                description TEXT,
                FOREIGN KEY(category_id) REFERENCES categories(id)
            )
        """)
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS restaurant_tables (
                id INTEGER PRIMARY KEY,
                label TEXT,
                capacity INTEGER,
                status TEXT DEFAULT 'Free',
                current_order_id INTEGER
            )
        """)
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY,
                table_id INTEGER,
                server_id INTEGER,
                timestamp DATETIME,
                status TEXT DEFAULT 'Open',
                total_amount REAL DEFAULT 0.0
            )
        """)
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS order_details (
                id INTEGER PRIMARY KEY,
                order_id INTEGER,
                menu_item_id INTEGER,
                quantity INTEGER,
                status TEXT DEFAULT 'Cooking',
                FOREIGN KEY(order_id) REFERENCES orders(id),
                FOREIGN KEY(menu_item_id) REFERENCES menu_items(id)
            )
        """)
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY,
                name TEXT,
                quantity INTEGER
            )
        """)
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS recipe_links (
                menu_item_id INTEGER,
                inventory_id INTEGER,
                amount_needed INTEGER,
                FOREIGN KEY(menu_item_id) REFERENCES menu_items(id),
                FOREIGN KEY(inventory_id) REFERENCES inventory(id)
            )
        """)
        self.conn.commit()

    def seed_data(self):
        if not self.cur.execute("SELECT * FROM users").fetchone():
            pw_hash = hashlib.sha256("admin".encode()).hexdigest()
            self.cur.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", 
                             ("admin", pw_hash, "Manager"))
            
            cats = ["Appetizers", "Mains", "Desserts", "Beverages", "Alcohol"]
            for c in cats:
                self.cur.execute("INSERT INTO categories (name) VALUES (?)", (c,))
            
            for i in range(1, 21):
                cap = 4 if i <= 10 else 2
                if i > 16: cap = 6
                self.cur.execute("INSERT INTO restaurant_tables (label, capacity) VALUES (?, ?)", 
                                 (f"T-{i}", cap))
            
            items = [
                ("Mains", "Ribeye Steak", 32.00), ("Mains", "Salmon", 24.00),
                ("Mains", "Pasta Carbonara", 18.00), ("Beverages", "Cola", 3.00),
                ("Alcohol", "House Red", 9.00)
            ]
            
            for cat, name, price in items:
                cat_id = self.cur.execute("SELECT id FROM categories WHERE name=?", (cat,)).fetchone()[0]
                self.cur.execute("INSERT INTO menu_items (category_id, name, price) VALUES (?, ?, ?)", 
                                 (cat_id, name, price))

            inv_items = [("Steak Meat", 5), ("Salmon Fillet", 10), ("Pasta Portion", 20), ("Wine Bottle", 10)]
            for name, qty in inv_items:
                self.cur.execute("INSERT INTO inventory (name, quantity) VALUES (?, ?)", (name, qty))

            ribeye_id = self.cur.execute("SELECT id FROM menu_items WHERE name='Ribeye Steak'").fetchone()[0]
            steak_inv_id = self.cur.execute("SELECT id FROM inventory WHERE name='Steak Meat'").fetchone()[0]
            self.cur.execute("INSERT INTO recipe_links (menu_item_id, inventory_id, amount_needed) VALUES (?, ?, ?)", 
                             (ribeye_id, steak_inv_id, 1))

            self.conn.commit()
            print("Database Seeded Successfully.")

    def check_inventory(self, menu_item_id):
        ingredients = self.get_data("SELECT inventory_id, amount_needed FROM recipe_links WHERE menu_item_id=?", (menu_item_id,))
        
        if not ingredients: return True

        for inv_id, amount in ingredients:
            stock = self.get_data("SELECT quantity FROM inventory WHERE id=?", (inv_id,))
            if not stock or stock[0][0] < amount:
                return False
        return True

    def deduct_inventory(self, menu_item_id):
        ingredients = self.get_data("SELECT inventory_id, amount_needed FROM recipe_links WHERE menu_item_id=?", (menu_item_id,))
        for inv_id, amount in ingredients:
            self.cur.execute("UPDATE inventory SET quantity = quantity - ? WHERE id=?", (amount, inv_id))
        self.conn.commit()

    def run_query(self, query, params=()):
        self.cur.execute(query, params)
        self.conn.commit()
        return self.cur

    def get_data(self, query, params=()):
        self.cur.execute(query, params)
        return self.cur.fetchall()

    def close(self):
        self.conn.close()

class SessionManager:
    current_user = None
    current_role = None

    @staticmethod
    def login(db, username, password):
        pw_hash = hashlib.sha256(password.encode()).hexdigest()
        user = db.get_data("SELECT id, role FROM users WHERE username=? AND password_hash=?", (username, pw_hash))
        if user:
            SessionManager.current_user = user[0][0]
            SessionManager.current_role = user[0][1]
            return True
        return False

    @staticmethod
    def logout():
        SessionManager.current_user = None
        SessionManager.current_role = None

class LoginScreen(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, bg=THEME_COLOR)
        self.controller = controller
        
        container = tk.Frame(self, bg="white", padx=40, pady=40)
        container.place(relx=0.5, rely=0.5, anchor="center")
        
        tk.Label(container, text="Table Reservation", font=("Georgia", 24, "bold"), bg="white", fg=THEME_COLOR).pack(pady=(0,20))
        tk.Label(container, text="Username", bg="white").pack(anchor="w")
        self.entry_user = ttk.Entry(container, width=30)
        self.entry_user.pack(pady=(0,10))
        
        tk.Label(container, text="Password", bg="white").pack(anchor="w")
        self.entry_pass = ttk.Entry(container, show="*", width=30)
        self.entry_pass.pack(pady=(0,20))
        
        btn = tk.Button(container, text="LOGIN", bg=ACCENT_COLOR, fg="white", 
                        font=("Arial", 12, "bold"), command=self.attempt_login, relief="flat", padx=20, pady=5)
        btn.pack()

    def attempt_login(self):
        u = self.entry_user.get()
        p = self.entry_pass.get()
        if SessionManager.login(self.controller.db, u, p):
            self.entry_user.delete(0, 'end')
            self.entry_pass.delete(0, 'end')
            self.controller.show_frame("MainDashboard")
        else:
            messagebox.showerror("Error", "Invalid Credentials")

class MainDashboard(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        
        nav_bar = tk.Frame(self, bg=THEME_COLOR, height=50)
        nav_bar.pack(side="top", fill="x")
        
        lbl_title = tk.Label(nav_bar, text="ENTERPRISE DASHBOARD", bg=THEME_COLOR, fg="white", font=FONT_HEADER)
        lbl_title.pack(side="left", padx=20)
        
        btn_logout = tk.Button(nav_bar, text="Logout", command=self.logout, bg="#7f8c8d", fg="white")
        btn_logout.pack(side="right", padx=10, pady=10)

        sidebar = tk.Frame(self, bg="#34495e", width=200)
        sidebar.pack(side="left", fill="y")
        
        self.btn_floor = self.create_nav_btn(sidebar, "Floor Plan", lambda: self.show_view("Floor"))
        self.btn_kitchen = self.create_nav_btn(sidebar, "Kitchen (KDS)", lambda: self.show_view("KDS"))
        self.btn_admin = self.create_nav_btn(sidebar, "Admin/Stats", lambda: self.show_view("Admin"))
        
        self.content_area = tk.Frame(self, bg=BG_COLOR)
        self.content_area.pack(side="right", fill="both", expand=True)
        
        self.views = {
            "Floor": FloorPlanView(self.content_area, controller),
            "KDS": KitchenView(self.content_area, controller),
            "Admin": AdminView(self.content_area, controller)
        }
        
        self.current_view = None
        self.show_view("Floor")

    def create_nav_btn(self, parent, text, command):
        btn = tk.Button(parent, text=text, command=command, bg="#34495e", fg="white", 
                        bd=0, font=("Arial", 12), pady=15, anchor="w", padx=20)
        btn.pack(fill="x")
        btn.bind("<Enter>", lambda e: btn.config(bg="#2c3e50"))
        btn.bind("<Leave>", lambda e: btn.config(bg="#34495e"))
        return btn

    def show_view(self, view_name):
        if self.current_view:
            self.current_view.pack_forget()
        self.current_view = self.views[view_name]
        self.current_view.refresh()
        self.current_view.pack(fill="both", expand=True)

    def logout(self):
        SessionManager.logout()
        self.controller.show_frame("LoginScreen")

class FloorPlanView(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, bg=BG_COLOR)
        self.controller = controller
        
        header = tk.Frame(self, bg="white", height=50)
        header.pack(fill="x", pady=(0, 20))
        tk.Label(header, text="RESTAURANT FLOOR", font=FONT_HEADER, bg="white").pack(side="left", padx=20, pady=10)
        
        self.canvas = tk.Canvas(self, bg=BG_COLOR)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=BG_COLOR)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True, padx=20)
        self.scrollbar.pack(side="right", fill="y")

    def refresh(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
            
        tables = self.controller.db.get_data("SELECT * FROM restaurant_tables")
        
        row = 0
        col = 0
        max_cols = 5
        
        for t in tables:
            t_id, label, cap, status, order_id = t
            color = "#27ae60"
            if status == "Occupied": color = "#e74c3c"
            if status == "Reserved": color = "#f39c12"
            if status == "Dirty": color = "#7f8c8d"
            
            card = tk.Frame(self.scrollable_frame, bg="white", bd=1, relief="solid", padx=10, pady=10, width=150, height=150)
            card.grid_propagate(False)
            card.grid(row=row, column=col, padx=10, pady=10)
            
            tk.Label(card, text=label, font=("Arial", 16, "bold"), bg="white").pack()
            tk.Label(card, text=f"Cap: {cap} | {status}", bg="white", fg="#7f8c8d").pack()
            
            tk.Frame(card, bg=color, height=5, width=130).pack(pady=5)
            
            btn_frame = tk.Frame(card, bg="white")
            btn_frame.pack(side="bottom", fill="x")

            action_text = "Open" if status == "Free" else "Manage"
            cmd = lambda tid=t_id, stat=status: self.open_table_manager(tid, stat)
            tk.Button(btn_frame, text=action_text, command=cmd, bg=THEME_COLOR, fg="white", width=6).pack(side="left", padx=2)
            
            if status == "Free":
                tk.Button(btn_frame, text="Rsrv", bg="#f39c12", fg="white", width=6,
                          command=lambda tid=t_id: self.make_reservation(tid)).pack(side="right", padx=2)
            elif status == "Reserved":
                tk.Button(btn_frame, text="Cancel", bg="#c0392b", fg="white", width=6,
                          command=lambda tid=t_id: self.cancel_reservation(tid)).pack(side="right", padx=2)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def make_reservation(self, table_id):
        name = simpledialog.askstring("Reservation", "Enter Guest Name:")
        if name:
            self.controller.db.run_query("UPDATE restaurant_tables SET status='Reserved', label=label || ' (' || ? || ')' WHERE id=?", (name, table_id))
            self.refresh()

    def cancel_reservation(self, table_id):
        if messagebox.askyesno("Cancel", "Cancel this reservation?"):
            original_label = f"T-{table_id}" 
            self.controller.db.run_query("UPDATE restaurant_tables SET status='Free', label=? WHERE id=?", (original_label, table_id))
            self.refresh()

    def open_table_manager(self, table_id, status):
        TableManagerWindow(self.controller, table_id, status, self.refresh)

class TableManagerWindow(tk.Toplevel):
    def generate_receipt(self, order_id, subtotal, tax, total):
        items = self.controller.db.get_data("""
            SELECT m.name, m.price, od.quantity 
            FROM order_details od
            JOIN menu_items m ON od.menu_item_id = m.id
            WHERE od.order_id=?
        """, (order_id,))

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"receipt_{order_id}_{timestamp}.txt"
        
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write("====================================\n")
                f.write(f"        THE GILDED FORK\n")
                f.write("====================================\n")
                f.write(f"Order ID: {order_id}\n")
                f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("------------------------------------\n")
                f.write(f"{'Item':<20} {'Qty':<5} {'Price'}\n")
                f.write("------------------------------------\n")
                
                for name, price, qty in items:
                    f.write(f"{name:<20} {qty:<5} ${price:.2f}\n")
                    
                f.write("------------------------------------\n")
                f.write(f"Subtotal:             ${subtotal:.2f}\n")
                f.write(f"Tax (8%):             ${tax:.2f}\n")
                f.write(f"TOTAL:                ${total:.2f}\n")
                f.write("====================================\n")
                f.write(f"      Thank you for dining!\n")
            
            messagebox.showinfo("Receipt", f"Receipt saved as {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save receipt: {e}")
        
    def __init__(self, controller, table_id, status, callback):
        tk.Toplevel.__init__(self)
        self.controller = controller
        self.table_id = table_id
        self.callback = callback
        self.title(f"Manage Table {table_id}")
        self.geometry("900x600")
        
        left_panel = tk.Frame(self, width=300, bg="#ecf0f1")
        left_panel.pack(side="left", fill="y")
        
        right_panel = tk.Frame(self, bg="white")
        right_panel.pack(side="right", fill="both", expand=True)
        
        tk.Label(left_panel, text="CURRENT BILL", font=("Arial", 12, "bold"), bg="#ecf0f1", pady=10).pack()
        
        self.order_list = tk.Listbox(left_panel, width=40, height=25)
        self.order_list.pack(padx=10)
        
        self.lbl_total = tk.Label(left_panel, text="Total: $0.00", font=("Arial", 14, "bold"), bg="#ecf0f1")
        self.lbl_total.pack(pady=10)
        
        btn_frame = tk.Frame(left_panel, bg="#ecf0f1")
        btn_frame.pack(fill="x", padx=10)
        
        tk.Button(btn_frame, text="Send to Kitchen", command=self.send_to_kitchen, bg="#f39c12", fg="white").pack(fill="x", pady=2)
        tk.Button(btn_frame, text="Checkout / Pay", command=self.checkout, bg="#27ae60", fg="white").pack(fill="x", pady=2)
        tk.Button(btn_frame, text="Occupy / Clear", command=self.toggle_occupancy, bg="#34495e", fg="white").pack(fill="x", pady=2)

        self.notebook = ttk.Notebook(right_panel)
        self.notebook.pack(fill="both", expand=True)
        
        categories = self.controller.db.get_data("SELECT id, name FROM categories")
        for cat_id, cat_name in categories:
            frame = tk.Frame(self.notebook, bg="white")
            self.notebook.add(frame, text=cat_name)
            self.populate_menu_grid(frame, cat_id)

        self.current_order_id = self.get_active_order()
        self.refresh_order_list()

    def get_active_order(self):
        res = self.controller.db.get_data("SELECT current_order_id FROM restaurant_tables WHERE id=?", (self.table_id,))
        if res and res[0][0]:
            return res[0][0]
        return None

    def populate_menu_grid(self, frame, cat_id):
        items = self.controller.db.get_data("SELECT id, name, price FROM menu_items WHERE category_id=?", (cat_id,))
        r, c = 0, 0
        for i_id, name, price in items:
            btn = tk.Button(frame, text=f"{name}\n${price:.2f}", 
                            font=("Arial", 10), width=15, height=3,
                            command=lambda x=i_id: self.add_item(x))
            btn.grid(row=r, column=c, padx=5, pady=5)
            c += 1
            if c > 3:
                c = 0
                r += 1

    def add_item(self, item_id):
        if not self.controller.db.check_inventory(item_id):
            messagebox.showwarning("Out of Stock", "Not enough ingredients to make this item!")
            return

        self.controller.db.deduct_inventory(item_id)

        if not self.current_order_id:
            self.controller.db.run_query(
                "INSERT INTO orders (table_id, server_id, timestamp, status) VALUES (?, ?, ?, 'Open')",
                (self.table_id, SessionManager.current_user, datetime.now())
            )
            self.current_order_id = self.controller.db.cur.lastrowid
            self.controller.db.run_query("UPDATE restaurant_tables SET status='Occupied', current_order_id=? WHERE id=?", 
                                         (self.current_order_id, self.table_id))
        
        self.controller.db.run_query(
            "INSERT INTO order_details (order_id, menu_item_id, quantity) VALUES (?, ?, 1)",
            (self.current_order_id, item_id)
        )
        self.refresh_order_list()

    def refresh_order_list(self):
        self.order_list.delete(0, tk.END)
        total = 0.0
        if self.current_order_id:
            items = self.controller.db.get_data("""
                SELECT m.name, m.price, od.status 
                FROM order_details od 
                JOIN menu_items m ON od.menu_item_id = m.id 
                WHERE od.order_id=?
            """, (self.current_order_id,))
            
            for name, price, status in items:
                self.order_list.insert(tk.END, f"{name} - ${price:.2f} ({status})")
                total += price
        
        self.lbl_total.config(text=f"Total: ${total:.2f}")

    def send_to_kitchen(self):
        if self.current_order_id:
            self.controller.db.run_query("UPDATE order_details SET status='Cooking' WHERE order_id=? AND status IS NULL", 
                                         (self.current_order_id,))
            messagebox.showinfo("Success", "Order sent to kitchen!")
            self.refresh_order_list()

    def checkout(self):
        if not self.current_order_id: return
        
        items = self.controller.db.get_data("""
            SELECT m.price FROM order_details od 
            JOIN menu_items m ON od.menu_item_id = m.id 
            WHERE od.order_id=?
        """, (self.current_order_id,))
        
        subtotal = sum(x[0] for x in items)
        tax = subtotal * TAX_RATE
        total = subtotal + tax
        
        if messagebox.askyesno("Checkout", f"Subtotal: ${subtotal:.2f}\nTax: ${tax:.2f}\nTotal: ${total:.2f}\n\nConfirm Payment?"):
            self.generate_receipt(self.current_order_id, subtotal, tax, total)

            self.controller.db.run_query("UPDATE orders SET status='Completed', total_amount=? WHERE id=?", (total, self.current_order_id))
            self.controller.db.run_query("UPDATE restaurant_tables SET status='Dirty', current_order_id=NULL WHERE id=?", (self.table_id,))
            self.callback()
            self.destroy()

    def toggle_occupancy(self):
        self.controller.db.run_query("UPDATE restaurant_tables SET status='Free' WHERE id=?", (self.table_id,))
        self.callback()
        self.destroy()

class KitchenView(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, bg="black")
        self.controller = controller
        
        header = tk.Frame(self, bg="#2c3e50")
        header.pack(fill="x")
        tk.Label(header, text="KITCHEN DISPLAY SYSTEM", fg="red", bg="#2c3e50", font=("Courier", 20, "bold")).pack(pady=10)
        tk.Button(header, text="REFRESH", command=self.refresh).pack(side="right", padx=10)
        
        self.container = tk.Frame(self, bg="black")
        self.container.pack(fill="both", expand=True, padx=10, pady=10)
        self.refresh()

    def refresh(self):
        for w in self.container.winfo_children(): w.destroy()
        
        active_orders = self.controller.db.get_data("""
            SELECT DISTINCT o.id, t.label, o.timestamp 
            FROM orders o
            JOIN restaurant_tables t ON o.table_id = t.id
            JOIN order_details od ON o.id = od.order_id
            WHERE od.status = 'Cooking'
        """)
        
        col = 0
        row = 0
        for o_id, t_label, time_str in active_orders:
            ticket = tk.Frame(self.container, bg="#fffde7", width=250)
            ticket.grid(row=row, column=col, padx=10, pady=10, sticky="n")
            
            tk.Label(ticket, text=f"ORDER #{o_id}", font=("Courier", 12, "bold"), bg="#fffde7").pack(anchor="w")
            tk.Label(ticket, text=f"{t_label} | {time_str[11:16]}", font=("Courier", 10), bg="#fffde7").pack(anchor="w")
            tk.Frame(ticket, height=2, bg="black").pack(fill="x", pady=5)
            
            items = self.controller.db.get_data("""
                SELECT m.name, od.id FROM order_details od
                JOIN menu_items m ON od.menu_item_id = m.id
                WHERE od.order_id = ? AND od.status = 'Cooking'
            """, (o_id,))
            
            for item_name, item_detail_id in items:
                f = tk.Frame(ticket, bg="#fffde7")
                f.pack(fill="x", anchor="w")
                tk.Label(f, text=f"- {item_name}", font=("Courier", 12), bg="#fffde7").pack(side="left")
            
            tk.Button(ticket, text="BUMP (DONE)", bg="#2ecc71", fg="white", 
                      command=lambda oid=o_id: self.complete_order(oid)).pack(fill="x", pady=(10,0))
            
            col += 1
            if col > 3:
                col = 0
                row += 1

    def complete_order(self, order_id):
        self.controller.db.run_query("UPDATE order_details SET status='Served' WHERE order_id=?", (order_id,))
        self.refresh()

class AdminView(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, bg=BG_COLOR)
        self.controller = controller
        tk.Label(self, text="ADMINISTRATION", font=FONT_HEADER, bg=BG_COLOR).pack(pady=20)
        
        self.stats_frame = tk.Frame(self, bg=BG_COLOR)
        self.stats_frame.pack(fill="x", padx=20)
        self.refresh()
        
    def refresh(self):
        for w in self.stats_frame.winfo_children(): w.destroy()
        
        total_rev = self.controller.db.get_data("SELECT SUM(total_amount) FROM orders WHERE status='Completed'")[0][0] or 0.0
        total_orders = self.controller.db.get_data("SELECT COUNT(*) FROM orders")[0][0]
        top_item = self.controller.db.get_data("""
            SELECT m.name, COUNT(od.id) as cnt FROM order_details od
            JOIN menu_items m ON od.menu_item_id = m.id
            GROUP BY m.name ORDER BY cnt DESC LIMIT 1
        """)
        top_item_name = top_item[0][0] if top_item else "N/A"
        
        stats = [
            ("Total Revenue", f"${total_rev:,.2f}"),
            ("Total Orders", str(total_orders)),
            ("Best Seller", top_item_name)
        ]
        
        for i, (label, val) in enumerate(stats):
            card = tk.Frame(self.stats_frame, bg="white", padx=20, pady=20, relief="raised")
            card.grid(row=0, column=i, padx=10, sticky="ew")
            tk.Label(card, text=label, fg="#7f8c8d", bg="white").pack()
            tk.Label(card, text=val, font=("Arial", 20, "bold"), fg=THEME_COLOR, bg="white").pack()

class RestaurantApp(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.title("Gilded Fork Enterprise System")
        self.geometry("1280x720")
        self.db = DatabaseManager()
        
        self.container = tk.Frame(self)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        
        self.frames = {}
        
        for F in (LoginScreen, MainDashboard):
            page_name = F.__name__
            frame = F(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")
            
        self.show_frame("LoginScreen")

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()

if __name__ == "__main__":
    app = RestaurantApp()
    app.mainloop()
